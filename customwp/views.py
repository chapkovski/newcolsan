from . import models
from ._builtin import Page, WaitPage
from otree.api import Currency as c, currency_range

from .models import Constants, Player
import time
from colsan_small.models import Constants as pggConstants
import math


def stay_with(page):
    is_dropout = page.player.participant.vars.get('dropout', False)
    is_out_of_game = page.player.participant.vars.get('outofthegame', False)
    return not is_dropout and not is_out_of_game


class CustomWaitPage(WaitPage):
    template_name = 'customwp/CustomWaitPage.html'

    def is_displayed(self):
        return self.extra_is_displayed() and stay_with(self)

    def extra_is_displayed(self):
        return True


class CustomPage(Page):
    timeout_seconds = 60
    def is_displayed(self):
        return self.extra_is_displayed() and stay_with(self)

    def extra_is_displayed(self):
        return True


class StartWP(CustomWaitPage):
    group_by_arrival_time = True
    template_name = 'customwp/FirstWaitPage.html'

    def vars_for_template(self):
        now = time.time()
        if not self.player.startwp_timer_set:
            self.player.startwp_timer_set = True
            self.player.startwp_time = time.time()
        time_left = self.player.startwp_time + Constants.startwp_timer - now
        part_fee = self.session.config['participation_fee']

        OOG_time_minutes = math.ceil(Constants.startwp_timer / 60)
        return {'time_left': round(time_left),
                'OOG_time_minutes': OOG_time_minutes,
                'part_fee': part_fee,
                }

    def get_players_for_group(self, waiting_players):
        post_dict = self.request.POST.dict()
        endofgame = post_dict.get('endofgame')
        slowpokes = [p.participant for p in self.subsession.get_players()
                     if p.participant._index_in_pages
                     < self.index_in_pages]
        # TO DEBUG
        those_with_us = Player.objects.filter(
            subsession=self.subsession,
            participant___index_in_pages=self.index_in_pages,
            _group_by_arrival_time_arrived=True,
            _group_by_arrival_time_grouped=False,
        )
        waiting_players = those_with_us
        # END OF TO DEBUG

        if len(slowpokes) + len(waiting_players) < pggConstants.players_per_group:
            self.subsession.not_enough_players = True
        if endofgame:
            curplayer = [p for p in waiting_players if p.pk == int(endofgame)][0]
            curplayer.participant.vars['outofthegame'] = True
            curplayer.outofthegame = True
            return [curplayer]
        if len(waiting_players) == Constants.players_per_group:
            return waiting_players


page_sequence = [
    StartWP,
]
