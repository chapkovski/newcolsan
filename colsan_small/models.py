from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)
import random

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
    num_rounds = 1
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
    instructions_stage1_wrapper = 'colsan_small/ins_s1_wrapper.html'
    q6_choices = ['My own', 'A random member of my group']


class Subsession(BaseSubsession):
    def before_session_starts(self):
        ...


class Group(BaseGroup):
    no_dropouts = models.BooleanField()

    @property
    def dropout_exists(self):
        dropouts = [p for p in self.get_players() if p.participant.vars.get('dropout', False)]

        if len(dropouts) > 0:
            return True
        return False

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
            p.set_pd_payoff()
            p.payoff = p.pd_payoff


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
        self.pd_received_mult = self.my_pair.pd_decision * Constants.pd_factor
        self.endowment_remain = Constants.endowment - self.pd_decision
        self.pd_payoff = self.pd_received_mult + self.endowment_remain

    # next field defines which pair will be shown at the punishment stage
    random_id = models.IntegerField(choices=Constants.threesome)
    is_dropout = models.BooleanField(default=False)
    # to which pair (out of 3) a player belongs:
    pair = models.IntegerField()

    # set of vars for results
    # Stage 1 (PD) payoff received by the pair and multiplied by PD factor
    pd_received_mult = models.IntegerField()
    endowment_remain = models.IntegerField()
    # to which subgroup (A or B) the player belongs:
    subgroup = models.CharField()
    pd_decision = models.IntegerField(verbose_name='Your sending decision',
                                      choices=gamechoices(Constants.endowment),
                                      widget=widgets.RadioSelectHorizontal())
    pd_payoff = models.IntegerField(initial=0)
    participant_vars_dump = models.CharField()