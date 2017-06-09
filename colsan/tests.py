from otree.api import Currency as c, currency_range
from . import views
from ._builtin import Bot
from .models import Constants
import random

class PlayerBot(Bot):
    def play_round(self):
        if self.player.round_number == 1:
            yield (views.InstructionsStage1)
            yield (views.InstructionsStage2)
            yield (views.ControlQuestions1,
                   {'q1': random.randint(0, 100),
                    'q2': random.randint(0, 100),
                    'q3': random.randint(0, 100),
                   })
            yield (views.ControlQuestions2,
                   {
                    'q_pun_received': random.randint(0, 100),
                    'q_pun_sent': random.randint(0, 100),
                    'q_colsan': random.choice(Constants.q6_choices),
                   })
            yield (views.CheckingAnswers)
        yield (views.PD,
               {'pd_decision': random.choice([True, False])})
        fields_to_yield = {}

        if self.session.config['ingroup']:
           fields_to_yield['ingroup_punishment'] = random.choice([True, False])
        if self.session.config['outgroup']:
           fields_to_yield['outgroup_punishment'] = random.choice([True, False])
        yield (views.Pun,
               fields_to_yield)
        yield (views.Results)
        if self.player.round_number == Constants.num_rounds:
            yield (views.FinalResults)
