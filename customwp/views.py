from . import models
from ._builtin import Page, WaitPage
from otree.api import Currency as c, currency_range
from otree.models import Participant
from .models import Constants, Player
import time
from colsan_small.models import Constants as pggConstants
import math
from django.core.exceptions import ObjectDoesNotExist


def vars_for_all_templates(self):
    return {'payment_per_minute_in_usd': Constants.payment_per_minute.to_real_world_currency(self.session), }


def stay_with(page):
    is_out_of_game = page.player.participant.vars.get('outofthegame', False)
    return not is_out_of_game


class CustomWaitPage(WaitPage):
    template_name = 'customwp/CustomWaitPage.html'

    def is_displayed(self):
        return self.extra_is_displayed() and stay_with(self)

    def extra_is_displayed(self):
        return True

    def vars_for_template(self):
        return {
            'index_in_pages': self._index_in_pages,
        }


class CustomPage(Page):
    timeout_seconds = 60

    def is_displayed(self):
        return self.extra_is_displayed() and stay_with(self)

    def extra_is_displayed(self):
        return True



class StartWP(CustomWaitPage):
    group_by_arrival_time = True
    template_name = 'customwp/FirstWaitPage.html'

    def dispatch(self, *args, **kwargs):
        super().dispatch(*args, **kwargs)
        if self.request.method == 'POST':
            end_of_game = self.request.POST.dict().get('endofgame')
            if end_of_game is not None:
                try:
                    cur_par = Participant.objects.get(pk=self.participant.pk)
                    cur_par.vars['outofthegame'] = True
                    cur_par.save()
                except ObjectDoesNotExist:
                    print("Matching participant does not exist!!!")

        response = super().dispatch(*args, **kwargs)
        return response

    def is_displayed(self):
        # if self.player.early_finish:
        #     return False
        return (stay_with(self))

    def vars_for_template(self):
        now = time.time()
        if not self.player.startwp_timer_set:
            self.player.startwp_timer_set = True
            self.player.startwp_time = time.time()
        time_left = self.player.startwp_time + Constants.startwp_timer - now
        part_fee = self.session.config['participation_fee']

        OOG_time_minutes = math.ceil(Constants.startwp_timer / 60)
        context_vars = super().vars_for_template()
        context_vars.update({'time_left': round(time_left),
                'OOG_time_minutes': OOG_time_minutes,
                'part_fee': part_fee,
                })
        return context_vars

    def get_players_for_group(self, waiting_players):
        slowpokes = [p.participant for p in self.subsession.get_players()
                     if p.participant._index_in_pages
                     < self._index_in_pages]


        if len(slowpokes) + len(waiting_players) < pggConstants.players_per_group:
            self.subsession.not_enough_players = True
        if len(waiting_players) == Constants.players_per_group:
            return waiting_players


page_sequence = [
    StartWP,
]
