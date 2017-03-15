from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)
import random
from otree.common import safe_json
from django import forms

doc = """
new collective sanctions experiment based on Stoff's paper
"""


class Constants(BaseConstants):
    name_in_url = 'colsan'
    players_per_group = None
    num_rounds_first = 2
    num_rounds_second = 1
    num_rounds = num_rounds_first + num_rounds_second
    A_group_size = 2
    B_group_size = 3
    yesyes_payoff = 6
    nono_payoff = 3
    noyes_payoff = 9
    yesno_payoff = 0
    punishment_factor = 3


class Subsession(BaseSubsession):
    def before_session_starts(self):
        for g in self.get_groups():
            g.colsan = self.session.config['colsan']
            g.outgroup = self.session.config['outgroup']
            g.ingroup = self.session.config['ingroup']


class Group(BaseGroup):
    colsan = models.BooleanField()
    outgroup = models.BooleanField()
    ingroup = models.BooleanField()


class Player(BasePlayer):
    pd_decision = models.BooleanField(verbose_name='Your decision')
    ingroup_punishment = models.BooleanField(verbose_name=
                                             'Punishing your group member')
    outgroup_punishment = models.BooleanField(verbose_name=
                                              'Punishing another group member')
