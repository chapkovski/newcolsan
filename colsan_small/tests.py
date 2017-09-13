from otree.api import Currency as c, currency_range, Submission
from . import views
from ._builtin import Bot
from .models import Constants
import random
import time


class PlayerBot(Bot):
    def play_round(self):
        time.sleep(0.01)
        self.player.refresh_from_db()
        self.group.refresh_from_db()
        if self.group.has_dropout and self.round_number == Constants.num_rounds:
            yield (views.DropOutFinal)
            return
        if self.group.has_dropout and self.round_number < Constants.num_rounds:
            return
        if self.player.round_number == 1:
            yield (views.InstructionsStage1)
            yield (views.InstructionsStage2)
        drop = random.random() < 0.1
        if drop:
            time.sleep(0.02)
        yield Submission(views.PD, {'pd_decision': 5}, timeout_happened=drop)
        if not self.group.has_dropout:
            fields_to_yield = {}
            if self.session.config['ingroup']:
                fields_to_yield['ingroup_punishment'] = 5
            if self.session.config['outgroup']:
                fields_to_yield['outgroup_punishment'] = 5
            yield (views.Pun, fields_to_yield)
            yield (views.Results)
            if self.player.round_number == Constants.num_rounds:
                yield (views.FinalResults)
