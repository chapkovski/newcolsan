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
    name_in_url = 'colsan'
    players_per_group = 6
    num_rounds = 10
    A_group_size = players_per_group / 2 - 1
    B_group_size = players_per_group / 2
    yesyes_payoff = 6
    nono_payoff = 3
    noyes_payoff = 9
    yesno_payoff = 0
    pd_pintayoff_dict = {
        '11': yesyes_payoff,
        '00': nono_payoff,
        '01': noyes_payoff,
        '10': yesno_payoff,
    }
    # by how much will be the sending money increased:
    pgg_factor = 2
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
    instructions_stage1_wrapper = 'colsan/ins_s1_wrapper.html'
    instructions_stage2_wrapper = 'colsan/ins_s2_wrapper.html'
    q6_choices = ['My own', 'A random member of my group']


class Subsession(BaseSubsession):
    def before_session_starts(self):
        if self.session.config['ingroup']:
            assert self.session.config['outgroup'], "You can't create ingroup treatment without outgroup"


class Group(BaseGroup):
    @property
    def subgroups(self):
        subgroup_dict = {}
        for s in Constants.groupset:
            subgroup_dict[s] = self.get_subgroup(s)
        print('SET OF SUBGROUPS:::', subgroup_dict)
        return subgroup_dict

    def get_subgroup(self, name):
        return [p for p in self.get_players() if p.subgroup == name]

    def set_payoffs(self):
        for p in self.get_players():
            chosen = [o for o in p.get_others_in_group()
                      if o.pair == p.random_id]
            assert len(chosen) == 2, 'Too few chosen!'
            ingroup_punishee = [_ for _ in chosen if _.subgroup == p.subgroup][0]
            if self.session.config['colsan']:
                outgroup_punishee = random.choice([_ for _ in
                                                   p.get_others_in_group()
                                                   if _.subgroup != p.subgroup])
            else:
                outgroup_punishee = [_ for _ in chosen if _.subgroup != p.subgroup][0]
            if p.ingroup_punishment:
                ingroup_punishee.punishment_received_in += 1
                ingroup_punishee.punishment_received += 1
            if p.outgroup_punishment:
                outgroup_punishee.punishment_received_out += 1
                outgroup_punishee.punishment_received += 1
        for p in self.get_players():
            assert p.punishment_received_out + p.punishment_received_in == \
                   p.punishment_received, 'Miscalculation in punishment received'
            p.set_pd_payoff()
            p.punishment_sent = (p.ingroup_punishment or 0) + \
                                (p.outgroup_punishment or 0)
            p.payoff = p.payoff_correct + p.pd_payoff + \
                       Constants.punishment_endowment - \
                       p.punishment_sent - \
                       p.punishment_received * Constants.punishment_factor


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

    def set_pd_payoff(self):
        self.pd_payoff = \
            Constants.pd_pintayoff_dict[(str(int(self.pd_decision)) \
                                         + str(int(self.my_pair.pd_decision)))]

    # next field defines which pair will be shown at the punishment stage
    random_id = models.IntegerField(choices=Constants.threesome)
    punishment_sent = models.IntegerField(initial=0)
    # total amount of punishment received
    punishment_received = models.IntegerField(initial=0)
    # separately: punishment received by ingroup members
    punishment_received_in = models.IntegerField(initial=0)
    # separately: punishment received by outgroup memebers
    punishment_received_out = models.IntegerField(initial=0)
    # to which pair (out of 3) a player belongs:
    pair = models.IntegerField()
    # to which subgroup (A or B) the player belongs:
    subgroup = models.CharField()
    pd_decision = models.BooleanField(verbose_name='Your decision',
                                      choices=[(False, 'Reject'),
                                               (True, 'Accept')], )
    pd_payoff = models.IntegerField(initial=0)
    ingroup_punishment = models.BooleanField(verbose_name=
                                             'Punishing your group member',
                                             widget=widgets.RadioSelectHorizontal(),
                                             )
    outgroup_punishment = models.BooleanField(verbose_name=
                                              'Punishing another group member',
                                              widget=widgets.RadioSelectHorizontal()
                                              )

    # control questions
    # counting the number of correct control answers
    num_correct = models.IntegerField(initial=0)
    payoff_correct = models.FloatField(initial=0)
    # control questions for stage 1
    q1 = models.IntegerField(verbose_name="""
            If you choose Red, and your partner chooses Blue, what will be your payoff at the end of Stage 1 of that round?
        """)
    q2 = models.IntegerField(verbose_name="""
            If you and your partner chose Red, what will be your payoff at the end of Stage 1?
        """)
    q3 = models.IntegerField(verbose_name="""
            If you and your partner chose Blue, what will be your payoff at the end of Stage 1?
        """)
    # control questions for stage 2
    # Question 4: In the stage 2, you chose to send XXX deduction tokens to a Participant A.

    q_pun_received = models.IntegerField()
    q_pun_sent = models.IntegerField(verbose_name="""
            By how many tokens your own income will be decreased?""")

    # Question 4: You decided to send XXX deduction tokens to a Participant B.
    q_colsan = models.CharField(
        verbose_name="As a result whose income will be decreased?",
        choices=Constants.q6_choices,
        widget=widgets.RadioSelectHorizontal(),
    )  # import itertools as it
    # filename='colsan/questions.txt'
    # qstart = '=='
    # with open(filename,'r') as f:
    #     i = 0
    #     for key,group in it.groupby(f,lambda line: line.startswith(qstart)):
    #         if not key:
    #             i += 1
    #             group = list(group)
    #             print('CHOICES:::: ', group[1:])
    #             Player.add_to_class("survey_q{}".format(i),
    #                     models.CharField(verbose_name=group[0],
    #                                     choices=group[1:]))
