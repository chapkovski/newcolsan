from . import models
from ._builtin import Page, WaitPage
from .models import Constants
import random
from otree.common import safe_json


class FirstWP(WaitPage):
    group_by_arrival_time = True
    template_name = 'colsan/FirstWP.html'

    def is_displayed(self):
        return self.round_number == 1

    def after_all_players_arrive(self):
        allplayers = self.group.get_players()
        if Constants.debug:
            for p in allplayers:
                p.pd_decision=random.choice([True, False])
        g = self.group
        for i, p in enumerate(allplayers):
            p.subgroup = Constants.groupset[i]
            p.pair = Constants.threesomesets[i]


class InstructionsStage1(Page):
    def is_displayed(self):
        return self.subsession.round_number == 1

class InstructionsStage2(Page):
    def is_displayed(self):
        return self.subsession.round_number == 1

class ControlQuestions1(Page):
    form_model = models.Player

    def is_displayed(self):
        return self.subsession.round_number == 1

    def get_form_fields(self):
        q_set = ['q1', 'q2', 'q3']
        random.shuffle(q_set)
        return q_set


class ControlQuestions2(Page):
    form_model = models.Player
    form_fields = ['q_pun_received', 'q_pun_sent', 'q_colsan']

    def is_displayed(self):
        return self.subsession.round_number == 1 and \
         self.session.config['ingroup'] or self.session.config['outgroup']

    def vars_for_template(self):
        if self.session.config['ingroup']:
            q_pun_received_label = "By how many tokens the Participant A's income will be decreased?"

        else:
            q_pun_received_label = "By how many tokens the Participant B's income will be decreased?"

        return {
                'q_pun_received_label': q_pun_received_label,

                }


class PD(Page):
    form_model = models.Player
    form_fields = ['pd_decision']


class WaitPD(WaitPage):
    template_name = 'colsan/WaitPD.html'

    def after_all_players_arrive(self):
        for p in self.group.get_players():
            p.random_id = random.choice([_ for _ in
                                        Constants.threesome if _ != p.pair])


class Pun(Page):
    form_model = models.Player

    def vars_for_template(self):
        random_pair = [p
                       for p in self.player.get_others_in_group()
                       if p.pair == self.player.random_id]
        random_pair_A  = [p
                          for p in random_pair
                          if p.subgroup == self.player.subgroup][0]
        random_pair_B  = [p
                          for p in random_pair
                          if p.subgroup != self.player.subgroup][0]
        # myform = self.get_form()
        return {
               'random_pair_A': random_pair_A,
               'random_pair_B': random_pair_B,
               'myform': myform,
               }

    def get_form_fields(self):
        fields = []
        if self.session.config['ingroup']:
            fields.append('ingroup_punishment')
        if self.session.config['outgroup']:
            fields.append('outgroup_punishment')

        return fields

class WaitResults(WaitPage):
    template_name = 'colsan/WaitResults.html'

    def after_all_players_arrive(self):
        self.group.set_payoffs()


class Results(Page):
    ...


class FinalResults(Page):
    def is_displayed(self):
        return self.round_number == Constants.num_rounds


page_sequence = [
    FirstWP,
    InstructionsStage1,
    InstructionsStage2,
    ControlQuestions1,
    ControlQuestions2,
    PD,
    WaitPD,
    Pun,
    WaitResults,
    # Results,
    # FinalResults,
]
