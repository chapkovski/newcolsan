from os import environ
from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)
from colsan_small.models import Constants as pggConstants
from django import forms as djforms
import statuses
author = 'Philipp Chapkovski, UZH'

doc = """
Your app description
"""


class Constants(BaseConstants):
    name_in_url = 'consent'
    players_per_group = None
    num_others_per_group = pggConstants.num_others_per_group
    num_rounds = 1
    consent_timeout = int(environ.get('CONSENT_TIMEOUT', 300))




class Subsession(BaseSubsession):
    def creating_session(self):
        if self.round_number == 1:
            for p in self.session.get_participants():
                p.vars['status'] = statuses.NON_INITIATED


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    consent = models.BooleanField(widget=djforms.CheckboxInput,
                                  initial=False
                                  )

    is_dropout = models.BooleanField(default=False)
