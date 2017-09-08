from . import models
from ._builtin import Page, WaitPage
from .models import Constants, Player
import random
from customwp.views import CustomWaitPage, CustomPage
from itertools import cycle
from random import shuffle


def vars_for_all_templates(self):
    max_pd = Constants.endowment * Constants.pd_factor
    egoistic_pd = max_pd + Constants.endowment
    return {'max_pd': max_pd,
            'egoistic_pd': egoistic_pd,
            }


class MyPage(CustomPage):
    timeout_seconds = 100000


class FirstWaitPD(CustomWaitPage):
    def after_all_players_arrive(self):
        allplayers = self.group.get_players()
        random.shuffle(allplayers)
        sg = cycle(Constants.groupset)

        for i, p in enumerate(allplayers):
            if self.round_number == 1:
                p.subgroup = next(sg)
            else:
                p.subgroup = p.in_round(1).subgroup
        for k, v in self.group.subgroups.items():
            pairs = Constants.threesome
            shuffle(pairs)
            for i, p in enumerate(v):
                p.pair = pairs[i]


class WaitPD(CustomWaitPage):
    # template_name = 'colsan/WaitPD.html'

    def after_all_players_arrive(self):
        allplayers = self.group.get_players()
        for p in allplayers:
            # we define the which random pair will be shown to the participants
            p.random_id = random.choice([_ for _ in
                                         Constants.threesome if _ != p.pair])
            p.set_pd_payoff()


class InstructionsStage1(MyPage):
    def extra_is_displayed(self):
        return self.subsession.round_number == 1





def A_or_B(self):
    if self.session.config['ingroup']:
        return 'A'
    else:
        return 'B'


class PD(MyPage):
    form_model = models.Player
    form_fields = ['pd_decision']
    timeout_submission = {}

    def __init__(self, *args, **kwargs):
        self.timeout_submission = {'pd_decision': random.randint(0, Constants.endowment)}
        super(PD, self).__init__(*args, **kwargs)




class WaitResults(CustomWaitPage):
    # template_name = 'colsan/WaitResults.html'

    def after_all_players_arrive(self):
        self.group.set_payoffs()


class Results(MyPage):
    def vars_for_template(self):
        partner = [_ for _ in self.player.get_others_in_group()
                   if _.pair == self.player.pair][0]
        return {'partner_decision': partner.pd_decision}


class FinalResults(MyPage):
    def extra_is_displayed(self):
        return self.round_number == Constants.num_rounds





page_sequence = [
    FirstWaitPD,
    InstructionsStage1,
    PD,
    WaitPD,
    WaitResults,
    Results,
    FinalResults,
]
