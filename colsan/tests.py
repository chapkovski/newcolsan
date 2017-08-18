from otree.api import Currency as c, currency_range
from . import views
from ._builtin import Bot
from .models import Constants
import random
import time
start_time = time.time()
print("--- %s seconds ---" % (time.time() - start_time))
class PlayerBot(Bot):
    cases = ['random', 'revenge', 'enforce_coop', 'revenge_antisocial']
    # random - means 
    def play_round(self):
        # if self.player.round_number == 1:
        #     yield (views.InstructionsStage1)
        #     yield (views.InstructionsStage2)
        #     yield (views.ControlQuestions1,
        #            {'q1': random.randint(0, 100),
        #             'q2': random.randint(0, 100),
        #             'q3': random.randint(0, 100),
        #            })
        #     yield (views.ControlQuestions2,
        #            {
        #             'q_pun_received': random.randint(0, 100),
        #             'q_pun_sent': random.randint(0, 100),
        #             'q_colsan': random.choice(Constants.q6_choices),
        #            })
        #     yield (views.CheckingAnswers)
        self.player.bot_strategy = self.case
        self.player.save()
        if self.case == 'basic':
            yield (views.PD,
                   {'pd_decision': random.choice([True, False])})
        elif self.case == 'min':
            yield (views.PD,
                   {'pd_decision': True})
        else:
            yield (views.PD,
                   {'pd_decision': False})

        fields_to_yield = {}

        if self.session.config['ingroup']:
           fields_to_yield['ingroup_punishment'] = random.choice([True, False])
        if self.session.config['outgroup']:
           fields_to_yield['outgroup_punishment'] = random.choice([True, False])
        yield (views.Pun,
               fields_to_yield)
        # yield (views.Results)
        # if self.player.round_number == Constants.num_rounds:
        #     yield (views.FinalResults)
