from otree.api import Currency as c, currency_range
from . import models
from ._builtin import Page, WaitPage
from .models import Constants


class Survey(Page):
    form_model = models.Player
    form_fields = ['comment']

    def get_form_fields(self):
        if self.session.config.get('name') == 'survey':
            return ['gender', 'q1', 'q2', 'q3', ]
        else:
            return self.form_fields
    def before_next_page(self):
        self.player.last_page=True
        how_many_passed = len([p for p in self.subsession.get_players() if p.last_page])
        if how_many_passed >= self.session.mturk_num_participants:
            for p in self.subsession.get_players():
                p.set_payoff()


page_sequence = [
    Survey,

]
