from . import models
from ._builtin import Page, WaitPage
from .models import Constants, Player, Group, Subsession
import random
import statuses
from functions import debug_session
from otree.api import Currency as c
from django.views.generic.base import TemplateResponseMixin
from otree.models import Participant
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
import datetime

FIRST_WP = 1
OTHER_WP = 0


def vars_for_all_templates(self):
    max_pd = Constants.endowment * Constants.pd_factor
    egoistic_pd = max_pd + Constants.endowment
    return {'max_pd': max_pd,
            'egoistic_pd': egoistic_pd,
            'base_points': round(1 / self.session.config['real_world_currency_per_point']),
            'payment_per_minute_in_usd': Constants.payment_per_minute.to_real_world_currency(self.session),
            }


class CustomWaitPage(WaitPage):
    template_name = 'custom_pages/CustomWaitPage.html'
    status = statuses.HEALTHY
    page_type = OTHER_WP

    def is_displayed(self):
        return self.extra_is_displayed() and self.participant.vars['status'] == self.status

    def extra_is_displayed(self):
        return True

    def vars_for_template(self):
        return {'page_type': self.page_type,
                'pay_per_sec': float(Constants.payment_per_minute.to_real_world_currency(self.session)) / 60, }

    def after_all_players_arrive(self):
        parts = [p.participant for p in self.group.get_players()]
        for p in parts:
            p.timestamps.all().update(opened=False)


class CustomPage(Page):
    timeout_seconds = 90
    status = statuses.HEALTHY

    def is_displayed(self):
        return self.extra_is_displayed() and self.participant.vars['status'] == self.status

    def extra_is_displayed(self):
        return True


class DecisionPage(CustomPage):
    def register_ingame_dropout(self):
        self.participant.vars['status'] = statuses.INGAME_DROPOUT
        self.group.check_and_update_dropouts()

    def before_next_page(self):
        if self.timeout_happened:
            self.register_ingame_dropout()

    def get_timeout_seconds(self):
        if self.round_number > 1:
            return Constants.time_to_decide
        return Constants.time_to_decide + 120


class StartWP(CustomWaitPage):
    group_by_arrival_time = True
    template_name = 'colsan_small/FirstWaitPage.html'
    page_type = FIRST_WP
    timer = Constants.wait_at_first_wp

    def extra_is_displayed(self):
        return self.round_number == 1

    def dispatch(self, *args, **kwargs):
        super().dispatch(*args, **kwargs)
        if self.request.method == 'POST':
            wp_dropout = self.request.POST.dict().get('wp_dropout')
            if wp_dropout is not None:
                p = Participant.objects.get(pk=self.participant.pk)
                p.vars['status'] = statuses.WP_DROPOUT
                p.save()
                # check_and_update_NEPS(self.session, self._index_in_pages)
        response = super().dispatch(*args, **kwargs)
        return response

    def vars_for_template(self):
        context = super().vars_for_template()
        now = datetime.datetime.now(datetime.timezone.utc)
        try:
            current_time_stamp = self.participant.timestamps.get(cur_page=self._index_in_pages, )
            started_at = current_time_stamp.created_at
        except ObjectDoesNotExist:
            started_at = now
        timer = self.timer
        time_left = timer + (started_at - now).total_seconds()
        context.update({'time_left': time_left})
        return context


class FirstWaitPD(CustomWaitPage):
    def after_all_players_arrive(self):
        super().after_all_players_arrive()
        self.group.update_subgroups_and_pairs()


class InstructionsStage1(CustomPage):
    timeout_seconds = 300

    def extra_is_displayed(self):
        return self.subsession.round_number == 1


class InstructionsStage2(CustomPage):
    timeout_seconds = 300

    def extra_is_displayed(self):
        return self.subsession.round_number == 1


class PD(DecisionPage):
    form_model = models.Player
    form_fields = ['pd_decision']


class WaitPD(CustomWaitPage):
    def after_all_players_arrive(self):
        super().after_all_players_arrive()
        if not self.group.check_and_update_dropouts():
            allplayers = self.group.get_players()
            for p in allplayers:
                # we define the which random pair will be shown to the participants
                p.random_id = random.choice([_ for _ in Constants.threesome if _ != p.pair])
                p.set_pd_payoff()


class Pun(DecisionPage):
    form_model = models.Player

    def vars_for_template(self):
        random_pair = [p
                       for p in self.player.get_others_in_group()
                       if p.pair == self.player.random_id]
        random_pair_A = next(p for p in random_pair if p.subgroup == self.player.subgroup)
        random_pair_B = next(p for p in random_pair if p.subgroup != self.player.subgroup)

        return {
            'random_pair_A': random_pair_A,
            'random_pair_B': random_pair_B,
        }

    def get_form_fields(self):
        fields = []
        if self.session.config['ingroup']:
            fields.append('ingroup_punishment')
        if self.session.config['outgroup']:
            fields.append('outgroup_punishment')
        return fields

    def error_message(self, values):
        if values.get('ingroup_punishment', 0) + values.get('outgroup_punishment',
                                                            0) > Constants.punishment_endowment:
            return 'Total amount of deduction points should not be more than {}'.format(
                Constants.punishment_endowment)


class WaitResults(CustomWaitPage):
    def after_all_players_arrive(self):
        super().after_all_players_arrive()
        if not self.group.check_and_update_dropouts():
            self.group.set_payoffs()


class Results(CustomPage):
    timeout_seconds = 240

    def vars_for_template(self):
        partner = next(i for i in self.player.get_others_in_group() if i.pair == self.player.pair)
        tot_game_payoff = self.participant.payoff - (self.player.payoff_minutes_waited or 0)
        return {'partner_decision': partner.pd_decision,
                'participant_real_currency_payoff': tot_game_payoff.to_real_world_currency(self.session),
                'real_currency_payoff': self.player.payoff.to_real_world_currency(self.session), }


class FinalPage(CustomPage):
    timeout_seconds = 600

    def vars_for_template(self):
        if self.player.payoff_minutes_waited is not None:
            earned_by_waiting = self.player.payoff_minutes_waited
        else:
            earned_by_waiting = 0
        tot_game_payoff = self.participant.payoff - earned_by_waiting
        waited_min = self.player.tot_minutes_waited if self.player.tot_minutes_waited is not None else 0
        return {
            'tot_game_payoff': tot_game_payoff,
            'waited_min': waited_min,
            'last_round_payoff': self.player.payoff - earned_by_waiting,
            'payoff_waiting': c(earned_by_waiting).to_real_world_currency(self.session),
            'participant_real_currency_payoff': tot_game_payoff.to_real_world_currency(self.session),
        }


class HealthyFinal(FinalPage):
    def extra_is_displayed(self):
        self.player.participant_vars_dump = self.participant.vars
        last_round = self.round_number == Constants.num_rounds
        if last_round:
            self.player.set_waiting_payoff()

        return last_round


class DropOutsPage(FinalPage, TemplateResponseMixin):
    def extra_is_displayed(self):
        return self.round_number == Constants.num_rounds

    def get_template_names(self):
        return ['dropouts/{}.html'.format(self.__class__.__name__)]


class ConsentDropoutFinal(DropOutsPage):
    status = statuses.CONSENT_DROPOUT


class WPDropoutFinal(DropOutsPage):
    status = statuses.WP_DROPOUT


class NotEnoughPlayersInSubsessionFinal(DropOutsPage):
    status = statuses.NOT_ENOUGH_PLAYERS_IN_SESSION


class IngameDropoutFinal(DropOutsPage):
    status = statuses.INGAME_DROPOUT


class GroupHasDropoutFinal(DropOutsPage):
    status = statuses.GROUP_HAS_DROPOUT


health_pages = [
    StartWP,
    FirstWaitPD,
    InstructionsStage1,
    InstructionsStage2,
    PD,
    WaitPD,
    Pun,
    WaitResults,
    Results,
    HealthyFinal,
]
dropouts_pages = [
    ConsentDropoutFinal,
    WPDropoutFinal,
    NotEnoughPlayersInSubsessionFinal,
    IngameDropoutFinal,
    GroupHasDropoutFinal,
]

page_sequence = health_pages + dropouts_pages
