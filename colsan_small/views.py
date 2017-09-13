from . import models
from ._builtin import Page, WaitPage
from .models import Constants, Player, Group
import random
from customwp.views import CustomWaitPage, CustomPage
from itertools import cycle
from random import shuffle
from functions import debug_session
from otree.api import Currency as c
from otree.models_concrete import PageCompletion
import time


# class WP(WaitPage):
#     def after_all_players_arrive(self):



def vars_for_all_templates(self):
    max_pd = Constants.endowment * Constants.pd_factor
    egoistic_pd = max_pd + Constants.endowment
    return {'max_pd': max_pd,
            'egoistic_pd': egoistic_pd,
            'base_points': round(1 / self.session.config['real_world_currency_per_point']),
            'payment_per_minute_in_usd': Constants.payment_per_minute.to_real_world_currency(self.session),
            }


class FirstRoundWP(CustomWaitPage):
    group_by_arrival_time = True

    def extra_is_displayed(self):
        return self.subsession.round_number == 1


class MyPage(CustomPage):
    timeout_seconds = Constants.time_to_decide

    def is_displayed(self):
        out_of_game = self.participant.vars.get('outofthegame', False)
        return self.extra_is_displayed() and not self.group.has_dropout and not out_of_game

    def extra_is_displayed(self):
        return True


class FirstWaitPD(CustomWaitPage):
    # def is_displayed(self):
    #     return True

    def is_displayed(self):
        if self.round_number > 1:
            self.group.has_dropout = self.group.in_round(self.round_number - 1).has_dropout
            if self.group.has_dropout:
                groups_in_all_rounds = Group.objects.filter(session=self.session,
                                                            id_in_subsession=self.group.id_in_subsession)
                for g in groups_in_all_rounds:
                    g.has_dropout = self.group.has_dropout
                    g.save()
        out_of_game = self.participant.vars.get('outofthegame', False)
        return not self.group.has_dropout and not out_of_game

    def after_all_players_arrive(self):
        if self.round_number > 1:
            self.group.has_dropout = self.group.in_round(self.round_number - 1).has_dropout
            if self.group.has_dropout:
                groups_in_all_rounds = Group.objects.filter(session=self.session,
                                                            id_in_subsession=self.group.id_in_subsession)
                for g in groups_in_all_rounds:
                    g.has_dropout = self.group.has_dropout
                    g.save()
        if not self.group.has_dropout:
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


class InstructionsStage2(MyPage):
    timeout_seconds = 240

    def extra_is_displayed(self):
        return self.subsession.round_number == 1


class PD(MyPage):
    def is_displayed(self):
        self.player.refresh_from_db()
        self.group.refresh_from_db()
        has_dropout = any([g.has_dropout for g in self.group.in_all_rounds()])
        out_of_game = self.participant.vars.get('outofthegame', False)
        return not has_dropout and not out_of_game

    form_model = models.Player
    form_fields = ['pd_decision']

    def before_next_page(self):
        if self.timeout_happened:
            self.group.has_dropout = True
            self.group.save()
            groups_in_all_rounds = Group.objects.filter(session=self.session,
                                                        id_in_subsession=self.group.id_in_subsession)
            for g in groups_in_all_rounds:
                g.has_dropout = self.group.has_dropout
                g.save()

    def get_timeout_seconds(self):
        if debug_session(self):
            return 30000
        if self.round_number > 1:
            return Constants.time_to_decide
        return Constants.time_to_decide + 30


class WaitPD(CustomWaitPage):
    def is_displayed(self):
        out_of_game = self.participant.vars.get('outofthegame', False)
        has_dropout = any([g.has_dropout for g in self.group.in_all_rounds()])
        return not has_dropout and not out_of_game

    def after_all_players_arrive(self):
        has_dropout = any([g.has_dropout for g in self.group.in_all_rounds()])
        if not has_dropout:
            allplayers = self.group.get_players()
            for p in allplayers:
                # we define the which random pair will be shown to the participants
                p.random_id = random.choice([_ for _ in
                                             Constants.threesome if _ != p.pair])
                if not p.group.has_dropout:
                    p.set_pd_payoff()


class Pun(MyPage):
    form_model = models.Player

    def vars_for_template(self):
        random_pair = [p
                       for p in self.player.get_others_in_group()
                       if p.pair == self.player.random_id]
        random_pair_A = [p
                         for p in random_pair
                         if p.subgroup == self.player.subgroup][0]
        random_pair_B = [p
                         for p in random_pair
                         if p.subgroup != self.player.subgroup][0]

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
        if values.get('ingroup_punishment', 0) + values.get('outgroup_punishment', 0) > Constants.punishment_endowment:
            return 'Total amount of deduction points should not be more than {}'.format(Constants.punishment_endowment)

    def before_next_page(self):
        if self.timeout_happened:
            self.group.has_dropout = True
            self.group.save()
            groups_in_all_rounds = Group.objects.filter(session=self.session,
                                                        id_in_subsession=self.group.id_in_subsession)
            for g in groups_in_all_rounds:
                g.has_dropout = self.group.has_dropout
                g.save()

    def get_timeout_seconds(self):
        return 240
        if self.round_number > 1:
            return Constants.time_to_decide
        return Constants.time_to_decide + 30


class WaitResults(CustomWaitPage):
    # template_name = 'colsan/WaitResults.html'
    def extra_is_displayed(self):
        out_of_game = self.participant.vars.get('outofthegame', False)
        return not self.group.has_dropout and not out_of_game

    def after_all_players_arrive(self):
        if not self.group.has_dropout:
            self.group.set_payoffs()


class Results(MyPage):
    timeout_seconds = 240

    def vars_for_template(self):
        partner = [_ for _ in self.player.get_others_in_group()
                   if _.pair == self.player.pair][0]
        tot_game_payoff = self.participant.payoff - (self.player.payoff_minutes_waited or 0)
        return {'partner_decision': partner.pd_decision,
                'participant_real_currency_payoff': tot_game_payoff.to_real_world_currency(self.session),
                'real_currency_payoff': self.player.payoff.to_real_world_currency(self.session), }


class FinalResults(MyPage):
    timeout_seconds = 900

    def extra_is_displayed(self):
        self.player.participant_vars_dump = self.participant.vars
        return self.round_number == Constants.num_rounds

    def vars_for_template(self):
        tot_game_payoff = self.participant.payoff - self.player.payoff_minutes_waited
        return {'last_round_payoff': self.player.payoff - self.player.payoff_minutes_waited,
                'tot_game_payoff': tot_game_payoff,
                'payoff_waiting': c(self.player.payoff_minutes_waited).to_real_world_currency(self.session),
                'participant_real_currency_payoff': tot_game_payoff.to_real_world_currency(self.session),
                }


class DropOutFinal(Page):
    timeout_seconds = 900

    def is_displayed(self):
        if self.round_number == Constants.num_rounds:
            waiting_pages = ['StartWP',
                             'FirstRoundWP',
                             'FirstWaitPD',
                             'WaitPD',
                             'WaitResults',
                             ]

            wp_sec_in_min = sum(PageCompletion.objects.filter(participant=self.player.participant,
                                                              page_name__in=waiting_pages).values_list(
                'seconds_on_page',
                flat=True)) / 60
            self.player.tot_minutes_waited = round(wp_sec_in_min, 2)
            self.player.payoff_minutes_waited = round(wp_sec_in_min * Constants.payment_per_minute, 2)
            if not self.player.payoff_min_added:
                self.player.payoff_min_added = True
                self.player.payoff += self.player.payoff_minutes_waited
        return self.group.has_dropout and self.round_number == Constants.num_rounds

    def vars_for_template(self):

        early_dropout = False
        if self.player.participant.vars.get('consent_dropout', False):
            early_dropout = True
            no_participation_fee = True
        else:
            no_participation_fee = False
        tot_game_payoff = self.participant.payoff - self.player.payoff_minutes_waited
        others_dropouts = (not self.player.participant.vars.get('dropout', False)) and self.group.dropout_exists
        return {'early_dropout': early_dropout,
                'tot_game_payoff': tot_game_payoff,
                'itself_dropout': self.player.participant.vars.get('dropout', False),
                'others_dropouts': others_dropouts,
                'no_participation_fee': no_participation_fee,
                'last_round_payoff': self.player.payoff - self.player.payoff_minutes_waited,
                'payoff_waiting': c(self.player.payoff_minutes_waited).to_real_world_currency(self.session),
                'participant_real_currency_payoff': tot_game_payoff.to_real_world_currency(self.session),
                }


page_sequence = [
    FirstRoundWP,
    FirstWaitPD,
    InstructionsStage1,
    InstructionsStage2,
    PD,
    WaitPD,
    Pun,
    WaitResults,
    Results,
    DropOutFinal,
    FinalResults,
]
