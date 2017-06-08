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
    ...
    def before_session_starts(self):
        ...


class Group(BaseGroup):
    pair_to_show = models.IntegerField()
    def set_payoffs(self):
            # whom_to_punish_B = [p for p in self.get_players() if p.subgroup == 'B' and p.id == random.choice(Constants.threesome)]
            # whom_to_punish = whom_to_punish_A + whom_to_punish_B
        # else:
        whom_to_punish = [p for p in self.get_players() if p.chosen_for_punishment]
        for p in whom_to_punish:
            totpun_ingroup = sum([o.ingroup_punishment or 0 for o in self.get_players() if o.subgroup == p.subgroup])
            totpun_outgroup = sum([o.outgroup_punishment or 0  for o in self.get_players() if o.subgroup != p.subgroup])
            p.punishment_received = (totpun_ingroup + totpun_outgroup) * Constants.punishment_factor
            p.punishment_sent = (p.ingroup_punishment or 0)  + (p.outgroup_punishment or 0)


class Player(BasePlayer):
    # next field defines which pair will be shown at the punishment stage
    random_id = models.IntegerField(choices = Constants.threesome)
    chosen_for_punishment = models.BooleanField(initial=False)
    punishment_sent = models.IntegerField()
    punishment_received = models.IntegerField()
    pair = models.IntegerField()
    subgroup = models.CharField()
    pd_decision = models.BooleanField(verbose_name='Your decision', choices=[(False,'Reject'),(True,'Accept')],)
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
    num_correct = models.IntegerField()
    payoff_correct = models.FloatField()
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
