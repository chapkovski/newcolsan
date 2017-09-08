from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)
from colsan_small.models import Constants as pggConstants
from customwp.models import Constants as CWPConstants
from django import forms as djforms

author = 'Philipp Chapkovski, UZH'

doc = """
Your app description
"""


class Constants(BaseConstants):
    name_in_url = 'consent'
    players_per_group = None
    num_others_per_group = pggConstants.num_others_per_group
    num_rounds = 1
    time_to_decide = pggConstants.time_to_decide
    startwp_timer = CWPConstants.startwp_timer


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    consent = models.BooleanField(widget=djforms.CheckboxInput,
                                  initial=False
                                  )
