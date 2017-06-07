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

    # set of constants to include instructions to other pages:
    instructions_stage1_wrapper = 'colsan/ins_s1_wrapper.html'
    instructions_stage2_wrapper = 'colsan/ins_s2_wrapper.html'

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
    # myselfshown = models.BooleanField(initial=False)
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
