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
            'base_points': round(1 / self.session.config['real_world_currency_per_point']),
            'participant_real_currency_payoff': self.participant.payoff.to_real_world_currency(self.session),
            }


class FirstRoundWP(CustomWaitPage):
    group_by_arrival_time = True

    def extra_is_displayed(self):
        return self.subsession.round_number == 1


class MyPage(CustomPage):
    timeout_seconds = Constants.time_to_decide

    def is_displayed(self):
        dropouts_not_shown = super().is_displayed()
        return self.extra_is_displayed() and not self.group.dropout_exists and dropouts_not_shown

    def extra_is_displayed(self):
        return True


class FirstWaitPD(CustomWaitPage):
    def extra_is_displayed(self):
        return not self.group.dropout_exists

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


class InstructionsStage1(MyPage):
    timeout_seconds = 240
    def extra_is_displayed(self):
        return self.subsession.round_number == 1



class PD(MyPage):
    form_model = models.Player
    form_fields = ['pd_decision']
    timeout_submission = {}

    def __init__(self, *args, **kwargs):
        self.timeout_submission = {'pd_decision': random.randint(0, Constants.endowment)}
        super(PD, self).__init__(*args, **kwargs)

    def before_next_page(self):
        if self.timeout_happened:
            self.player.is_dropout = True
            self.player.participant.vars['dropout'] = True

    def get_timeout_seconds(self):
        if self.round_number > 1:
            return Constants.time_to_decide
        return Constants.time_to_decide + 30


class WaitResults(CustomWaitPage):
    # template_name = 'colsan/WaitResults.html'
    def extra_is_displayed(self):
        return not self.group.dropout_exists

    def after_all_players_arrive(self):
        self.group.no_dropouts = True
        self.group.set_payoffs()


class Results(MyPage):
    timeout_seconds = 180
    def vars_for_template(self):
        partner = [_ for _ in self.player.get_others_in_group()
                   if _.pair == self.player.pair][0]
        return {'partner_decision': partner.pd_decision,
                'real_currency_payoff': self.player.payoff.to_real_world_currency(self.session), }


class FinalResults(MyPage):
    def extra_is_displayed(self):
        return self.round_number == Constants.num_rounds


class DropOutFinal(Page):
    timeout_seconds = 900

    def is_displayed(self):
        return self.group.dropout_exists and self.round_number == Constants.num_rounds

    def vars_for_template(self):

        early_dropouts = [p for p in self.group.in_round(1).get_players() if p.is_dropout]
        if len(early_dropouts) > 0:
            early_dropout = True
        else:
            early_dropout = False
        if self.player.participant.vars.get('consent_dropout', False):
            early_dropout = True
            no_participation_fee = True
        else:
            no_participation_fee = False
        others_dropouts = (not self.player.participant.vars.get('dropout', False)) and self.group.dropout_exists
        return {'early_dropout': early_dropout,
                'itself_dropout': self.player.participant.vars.get('dropout', False),
                'others_dropouts': others_dropouts,
                'no_participation_fee': no_participation_fee}


page_sequence = [
    FirstRoundWP,
    FirstWaitPD,
    InstructionsStage1,
    PD,
    WaitResults,
    Results,
    DropOutFinal,
    FinalResults,
]
