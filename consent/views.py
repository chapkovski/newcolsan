from otree.api import Currency as c, currency_range
from . import models
from ._builtin import Page, WaitPage
from .models import Constants
import math
from functions import debug_session




class Consent(Page):
    timeout_seconds = 600
    form_model = models.Player
    form_fields = ['consent']
    timeout_submission = {'consent': False}


    def is_displayed(self):
        return self.round_number == 1

    def consent_error_message(self, value):
        if not value:
            return 'You must accept the consent form in order to proceed with the study!'

    def before_next_page(self):
        if self.timeout_happened and not debug_session(self):
            self.player.consent = False
            self.player.is_dropout = True
            self.player.participant.vars['dropout'] = True
            return
        if self.timeout_happened and debug_session(self):
            self.player.consent = True


page_sequence = [
    Consent,
]
