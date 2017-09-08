from otree.api import Currency as c, currency_range
from . import models
from ._builtin import Page, WaitPage
from .models import Constants
import math


class FirstIntroPage(Page):
    timeout_seconds = 60
    timer_text = 'You will be forwarded to the Consent Form page in: '

    def is_displayed(self):
        return self.round_number == 1

    def vars_for_template(self):
        part_fee = self.session.config['participation_fee']

        OOG_time_minutes = math.ceil(Constants.startwp_timer / 60)
        return {

            'OOG_time_minutes': OOG_time_minutes,

            'part_fee': part_fee,
            'showing_at_intro': True
        }


class Consent(Page):
    timeout_seconds = 300
    form_model = models.Player
    form_fields = ['consent']
    timeout_submission = {'consent': False}


    def vars_for_template(self):
        return {
            'add_to_timer': 'Otherwise you cannot receive the participation fee!'
        }
    def is_displayed(self):
        return self.round_number == 1

    def consent_error_message(self, value):
        if not value:
            return 'You must accept the consent form in order to proceed with the study!'

    def before_next_page(self):
        if self.timeout_happened:
            self.player.is_dropout = True
            self.player.participant.vars['dropout'] = True


page_sequence = [
    # FirstIntroPage,
    Consent,
]
