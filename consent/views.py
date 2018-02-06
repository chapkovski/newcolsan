from otree.api import Currency as c, currency_range
from . import models
from ._builtin import Page, WaitPage
from .models import Constants
import math
from functions import debug_session
import statuses


class Consent(Page):
    timeout_seconds = Constants.consent_timeout
    form_model = models.Player
    form_fields = ['consent']
    timeout_submission = {'consent': False}

    def vars_for_template(self):
        return {'consent_timeout_min': math.ceil(self.timeout_seconds / 60)}

    def is_displayed(self):
        return self.round_number == 1 and (self.participant.vars['status'] == statuses.HEALTHY or
                                           self.participant.vars['status'] == statuses.NON_INITIATED)

    def consent_error_message(self, value):
        if not value:
            return 'You must accept the consent form in order to proceed with the study!'

    def before_next_page(self):
        if self.timeout_happened:
            self.participant.vars['status'] = statuses.CONSENT_DROPOUT
        else:
            self.participant.vars['status'] = statuses.HEALTHY
        # if debug_session(self):
        #


page_sequence = [
    Consent,
]
