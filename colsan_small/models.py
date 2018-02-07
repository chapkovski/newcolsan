from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)
import random
import statuses
from django.db import models as djmodels
from django.db.models import Sum
from itertools import cycle
from random import shuffle
from otree.models import Participant

doc = """
new collective sanctions experiment based on Stoff's paper
"""


# let's do some work on supergroup management

class Constants(BaseConstants):
    currency_name = 'point'
    name_in_url = 'colsansmall'
    players_per_group = 6
    num_others_per_group = players_per_group - 1
    time_to_decide = 120
    num_rounds = 2
    A_group_size = players_per_group / 2 - 1
    B_group_size = players_per_group / 2
    # how much money can be invested into public good project
    endowment = 10
    # by how much will be the sending money increased:
    pd_factor = 2
    # by how much will 1 deduction token sent affect the payoff of the punishee (the recipient of punishment):
    punishment_factor = 3
    # how many punishment tokens will be received for distributing the punishment
    punishment_endowment = 10
    groupset = ['A', 'B', ]
    punishment_choices = [0, 1]
    threesome = list(range(1, 4))
    # payment for each correct answer in control question set of pages:
    correct_answer_payoff = 0.5
    # set of constants to include instructions to other pages:
    instructions_stage1_wrapper = 'includes/ins_s1_wrapper.html'
    instructions_stage2_wrapper = 'includes/ins_s2_wrapper.html'
    q6_choices = ['My own', 'A random member of my group']
    payment_per_minute = c(20)


class Subsession(BaseSubsession):
    def creating_session(self):
        for p in self.get_players():
            p.punishment_endowment = Constants.punishment_endowment


class Group(BaseGroup):
    def check_and_update_dropouts(self):
        ingame_drops = [p for p in self.get_players() if p.participant.vars['status'] == statuses.INGAME_DROPOUT]
        if ingame_drops:
            others = [p for p in self.get_players() if p not in ingame_drops]
            for o in others:
                o.participant.vars['status'] = statuses.GROUP_HAS_DROPOUT
        return ingame_drops

    def update_subgroups_and_pairs(self):
        if not self.check_and_update_dropouts():
            allplayers = self.get_players()
            random.shuffle(allplayers)
            sg = cycle(Constants.groupset)
            for i, p in enumerate(allplayers):
                if self.round_number == 1:
                    p.subgroup = next(sg)
                else:
                    p.subgroup = p.in_round(1).subgroup
            for k, v in self.subgroups.items():
                pairs = Constants.threesome.copy()
                shuffle(pairs)
                for i, p in enumerate(v):
                    p.pair = pairs[i]

    @property
    def subgroups(self):
        subgroup_dict = {}
        for s in Constants.groupset:
            subgroup_dict[s] = self.get_subgroup(s)
        return subgroup_dict

    def get_subgroup(self, name):
        return [p for p in self.get_players() if p.subgroup == name]

    def set_payoffs(self):
        for p in self.get_players():
            chosen = [o for o in p.get_others_in_group()
                      if o.pair == p.random_id]
            assert len(chosen) == 2, 'Too few chosen!'
            ingroup_punishee = next(_ for _ in chosen if _.subgroup == p.subgroup)
            observed_outgroup_punishee = next(_ for _ in chosen if _.subgroup != p.subgroup)
            if self.session.config['colsan']:
                outgroup_punishee = random.choice([_ for _ in
                                                   p.get_others_in_group()
                                                   if _.subgroup != p.subgroup])
            else:
                outgroup_punishee = observed_outgroup_punishee
            p.outgroup_punishee_decision = observed_outgroup_punishee.pd_decision
            p.ingroup_punishee_decision = ingroup_punishee.pd_decision
            ingroup_punishee.punishment_received_in += (p.ingroup_punishment or 0)
            ingroup_punishee.punishment_received += (p.ingroup_punishment or 0)
            outgroup_punishee.punishment_received_out += (p.outgroup_punishment or 0)
            outgroup_punishee.punishment_received += (p.outgroup_punishment or 0)
        for p in self.get_players():
            assert p.punishment_received_out + p.punishment_received_in == \
                   p.punishment_received, 'Miscalculation in punishment received'
            assert p.punishment_sent <= p.punishment_endowment, """Amount of punishment sent cannot exceed 
                                                                   punishment endowment"""
            p.pun_r_out_mult = p.punishment_received_out * Constants.punishment_factor
            p.pun_r_in_mult = p.punishment_received_in * Constants.punishment_factor

            p.set_pd_payoff()
            p.punishment_sent = (p.ingroup_punishment or 0) + \
                                (p.outgroup_punishment or 0)
            p.punishment_endowment_remain = p.punishment_endowment - p.punishment_sent
            p.payoff_stage2 = p.punishment_endowment_remain - \
                              p.punishment_received * Constants.punishment_factor
            p.payoff = p.pd_payoff + p.payoff_stage2


def gamechoices(n):
    result = []
    for i in range(n + 1):
        currency = Constants.currency_name if i == 1 else Constants.currency_name + 's'
        result.append((i, '{} {}'.format(i, currency)))
    return result


class Player(BasePlayer):
    @property
    def my_subgroup(self):
        return self.group.subgroups[self.subgroup]

    @property
    def another_subgroup_name(self):
        other_subgroups = set(Constants.groupset)
        another_subgroup = other_subgroups - set([self.subgroup])
        assert len(another_subgroup) == 1, 'SOMETHING GONE WRONG'
        return another_subgroup.pop()

    @property
    def another_subgroup(self):
        return self.group.subgroups[self.another_subgroup_name]

    @property
    def my_pair(self):
        others = self.another_subgroup
        my_pair = list(filter(lambda x: x.pair == self.pair, others))
        assert len(my_pair) == 1, 'Something is wrong'
        return my_pair.pop()

    @property
    def random_pair(self):
        assert self.random_id != self.pair, 'the player pair cannot be the same as the random pair shown to him!'
        random_pair = [p for p in self.get_others_in_group() if p.pair == self.random_id]
        ingroup_member = [p for p in random_pair if p.subgroup == self.subgroup][0]
        outgroup_member = [p for p in random_pair if p.subgroup != self.subgroup][0]
        return {'ingroup_member': ingroup_member,
                'outgroup_member': outgroup_member, }

    def set_pd_payoff(self):
        self.pd_received_mult = (self.my_pair.pd_decision or 0) * Constants.pd_factor
        self.endowment_remain = Constants.endowment - self.pd_decision
        self.pd_payoff = self.pd_received_mult + self.endowment_remain

    def set_waiting_payoff(self):
        tot_sec_waited = sum([t.diff.total_seconds() for t in self.participant.timestamps.all() if t.diff is not None])
        self.tot_minutes_waited = round(tot_sec_waited / 60, 2)
        self.payoff_minutes_waited = self.tot_minutes_waited * Constants.payment_per_minute
        if self.round_number == Constants.num_rounds and not self.payoff_min_added:
            print('adding payoff, old payoff was:{}'.format(self.payoff))
            self.payoff += self.payoff_minutes_waited
            self.payoff_min_added = True
            print('new payoff is:{}'.format(self.payoff))
            # raise ValueError('STOP THE BULLSHIT')

    random_id = models.IntegerField(choices=Constants.threesome)
    punishment_endowment = models.IntegerField()
    punishment_sent = models.IntegerField(initial=0)
    # total amount of punishment received
    punishment_received = models.IntegerField(initial=0)
    # separately: punishment received by ingroup members
    punishment_received_in = models.IntegerField(initial=0)
    # separately: punishment received by outgroup memebers
    punishment_received_out = models.IntegerField(initial=0)
    # to which pair (out of 3) a player belongs:
    pair = models.IntegerField()

    # set of vars for results
    # Stage 1 (PD) payoff received by the pair and multiplied by PD factor
    pd_received_mult = models.IntegerField()
    endowment_remain = models.IntegerField()
    punishment_endowment_remain = models.IntegerField()
    pun_r_in_mult = models.IntegerField()
    pun_r_out_mult = models.IntegerField()
    # to which subgroup (A or B) the player belongs:
    subgroup = models.CharField()
    pd_decision = models.IntegerField(verbose_name='Your sending decision', min=0, max=Constants.endowment,
                                      )
    pd_payoff = models.IntegerField(initial=0)
    payoff_stage2 = models.IntegerField(initial=0)
    ingroup_punishment = models.IntegerField(verbose_name=
                                             'Sending deduction tokens to your group member',
                                             min=0,
                                             max=Constants.punishment_endowment,
                                             )
    outgroup_punishment = models.IntegerField(verbose_name=
                                              'Sending deduction tokens to another group member',
                                              min=0,
                                              max=Constants.punishment_endowment,
                                              )
    outgroup_punishee_decision = models.IntegerField(
        doc='to store the decision of observed target of outgroup punishment')
    ingroup_punishee_decision = models.IntegerField(
        doc='to store the decision of observed target of ingroup punishment')
    participant_vars_dump = models.CharField()
    tot_minutes_waited = models.IntegerField(doc='total amount of minutes waited by participant which should be paid')
    payoff_minutes_waited = models.FloatField(doc='minutes waited multiplied by price per minute')
    payoff_min_added = models.BooleanField(doc='whether payoff for waiting has been already added')


class TimeStamp(djmodels.Model):
    participant = djmodels.ForeignKey(to=Participant, related_name='timestamps')
    created_at = djmodels.DateTimeField(auto_now_add=True)
    closed_at = djmodels.DateTimeField(null=True)
    cur_page = models.IntegerField()
    opened = models.BooleanField()
    diff = djmodels.DurationField(null=True)

    def __str__(self):
        return 'TIMESTAMP {} CREATED {}, CLOSED {}, OPENED:{}. SEC {} '.format(self.pk, self.created_at,
                                                                               self.closed_at, self.opened,
                                                                               self.diff)
