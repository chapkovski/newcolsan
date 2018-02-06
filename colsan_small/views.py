from . import models
from ._builtin import Page, WaitPage
from .models import Constants, Player, Group, Subsession
import random
import statuses
from functions import debug_session
from otree.api import Currency as c
from django.views.generic.base import TemplateResponseMixin
from otree.models import Participant

FIRST_WP = 1
OTHER_WP = 0


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
        # TODO delete next line after debugging
        return 60
        if debug_session(self):
            return 30000
        if self.round_number > 1:
            return Constants.time_to_decide
        return Constants.time_to_decide + 30


class StartWP(CustomWaitPage):
    group_by_arrival_time = True
    template_name = 'colsan_small/FirstWaitPage.html'
    page_type = FIRST_WP

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


class FirstWaitPD(CustomWaitPage):
    def after_all_players_arrive(self):
        self.group.update_subgroups_and_pairs()


class InstructionsStage1(CustomPage):
    timeout_seconds = 300

    def extra_is_displayed(self):
        return self.subsession.round_number == 1


class InstructionsStage2(CustomPage):
    timeout_seconds = 300

    def extra_is_displayed(self):
        return self.subsession.round_number == 1

    def get_timeout_seconds(self):
        if debug_session(self):
            return 30000
        return 300


class PD(DecisionPage):
    form_model = models.Player
    form_fields = ['pd_decision']


class WaitPD(CustomWaitPage):
    def after_all_players_arrive(self):
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


class FinalResults(CustomPage):
    def vars_for_template(self):
        tot_game_payoff = self.participant.payoff - self.player.payoff_minutes_waited
        return {'last_round_payoff': self.player.payoff - self.player.payoff_minutes_waited,
                'tot_game_payoff': tot_game_payoff,
                'payoff_waiting': c(self.player.payoff_minutes_waited).to_real_world_currency(self.session),
                'participant_real_currency_payoff': tot_game_payoff.to_real_world_currency(self.session),
                }


class FinalPage(CustomPage):
    def vars_for_template(self):

        if self.player.payoff_minutes_waited is not None:
            earned_by_waiting= self.player.tot_minutes_waited
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
    # TODO: MOVE IT AOUT!
    timeout_seconds = 90000

    def extra_is_displayed(self):
        #TODO: finish the payoff calculation for waiting time!!1
        self.player.participant_vars_dump = self.participant.vars
        return self.round_number == Constants.num_rounds


class DropOutsPage(FinalPage, TemplateResponseMixin):
    # TODO: MOVE IT AOUT!
    timeout_seconds = 90000

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
    # InstructionsStage1,
    # InstructionsStage2,
    PD,
    WaitPD,
    Pun,
    WaitResults,
    # Results,
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
