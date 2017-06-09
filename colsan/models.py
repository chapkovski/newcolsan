from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)
import random
from otree.common import safe_json
# from django import forms

doc = """
new collective sanctions experiment based on Stoff's paper
"""


class Constants(BaseConstants):
    name_in_url = 'colsan'
    players_per_group = 6
    num_rounds = 2
    A_group_size = players_per_group/2 - 1
    B_group_size = players_per_group/2
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
    punishment_factor = 3
    punishment_endowment = 2
    groupset = ['A', 'A', 'A', 'B', 'B', 'B', ]
    punishment_choices = [0, 1]
    threesome = list(range(1, 4))
    threesomesets = threesome + threesome
    debug = True
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
                ingroup_punishee.punishment_received += 1
            if p.outgroup_punishment:
                outgroup_punishee.punishment_received += 1

        for p in self.get_players():
            p.set_pd_payoff()
            p.punishment_sent = (p.ingroup_punishment or 0) + \
                (p.outgroup_punishment or 0)
            p.payoff = p.payoff_correct + p.pd_payoff + \
                Constants.punishment_endowment - \
                p.punishment_sent - \
                p.punishment_received * Constants.punishment_factor

class Player(BasePlayer):
    def get_my_pair(self):
        those_needed = [p for p in self.get_others_in_group() if
                        p.pair == self.pair and p.subgroup != self.subgroup]
        assert len(those_needed) == 1, 'Something is wrong'
        return those_needed[0]

    def set_pd_payoff(self):
        self.pd_payoff = \
            Constants.pd_pintayoff_dict[(str(int(self.pd_decision)) \
                + str(int(self.get_my_pair().pd_decision)))]
    # next field defines which pair will be shown at the punishment stage
    random_id = models.IntegerField(choices = Constants.threesome)
    punishment_sent = models.IntegerField(initial=0)
    punishment_received = models.IntegerField(initial=0)
    # to which pair (out of 3) a player belongs:
    pair = models.IntegerField()
    # to which subgroup (A or B) the player belongs:
    subgroup = models.CharField()
    pd_decision = models.BooleanField(verbose_name='Your decision',
                                      choices=[(False, 'Reject'),
                                               (True, 'Accept')],)
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
    q_colsan  = models.CharField(
        verbose_name="As a result whose income will be decreased?",
        choices=Constants.q6_choices,
        widget=widgets.RadioSelectHorizontal(),
        )
