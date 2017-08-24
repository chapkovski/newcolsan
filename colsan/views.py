from . import models
from ._builtin import Page, WaitPage
from .models import Constants, Player
import random
from otree.common import safe_json
from otree.bots.bot import ParticipantBot
# from otree.bots.runner import SessionBotRunner
from .customsessionbots import MySessionBotRunner
import threading
from customwp.views import CustomWaitPage, CustomPage


class MyPage(CustomPage):
    timeout_seconds = 12000



class InstructionsStage1(MyPage):
    def extra_is_displayed(self):
        return self.subsession.round_number == 1

class InstructionsStage2(MyPage):
    def extra_is_displayed(self):
        return self.subsession.round_number == 1

class ControlQuestions1(MyPage):
    form_model = models.Player

    def extra_is_displayed(self):
        return self.subsession.round_number == 1

    def get_form_fields(self):
        q_set = ['q1', 'q2', 'q3']
        random.shuffle(q_set)
        return q_set

def A_or_B(self):
    if self.session.config['ingroup']:
        return 'A'
    else:
        return 'B'


class ControlQuestions2(MyPage):
    form_model = models.Player
    form_fields = ['q_pun_received', 'q_pun_sent', 'q_colsan']

    def extra_is_displayed(self):
        return self.subsession.round_number == 1 and \
          self.session.config['outgroup']

    def vars_for_template(self):
        q_pun_received_label = "By how many tokens the Participant {}'s income will be decreased?".format(A_or_B(self))

        return {
                'q_pun_received_label': q_pun_received_label,

                }


class CheckingAnswers(MyPage):

    def extra_is_displayed(self):
        return self.subsession.round_number == 1

    def vars_for_template(self):

        q4_5 = 'In the stage 2, you chose to send a deduction token to a Participant {}.'.format(A_or_B(self))
        q4 = q4_5 + " By how many tokens the Participant {}'s income will be decreased?".format(A_or_B(self))
        q5 = q4_5 + Player._meta.get_field('q_pun_sent').verbose_name
        q6 = """
        Imagine, that you were the one whose decision was shown to someone
           from the Group B. This person decides to send you a deduction token.
        """
        q6 += str(Player._meta.get_field('q_colsan').verbose_name)
        if self.session.config['colsan']:
            corr_q6 =Constants.q6_choices[1]
        else:
            corr_q6 =Constants.q6_choices[0]
        ca = [[Player._meta.get_field('q1').verbose_name, Constants.yesno_payoff, self.player.q1 ],
             [Player._meta.get_field('q2').verbose_name, Constants.yesyes_payoff, self.player.q2 ],
             [Player._meta.get_field('q3').verbose_name, Constants.nono_payoff, self.player.q3 ],
             [q4, Constants.punishment_factor, self.player.q_pun_received],
             [q5, 1, self.player.q_pun_sent],
             [q6, corr_q6, self.player.q_colsan ],]
        self.player.num_correct=sum([1 for _ in ca if _[1]==_[2]])
        self.player.payoff_correct = \
            self.player.num_correct * Constants.correct_answer_payoff

        return {'q_n_a': ca}


class PD(MyPage):
    form_model = models.Player
    form_fields = ['pd_decision']


class WaitPD(CustomWaitPage):
    # template_name = 'colsan/WaitPD.html'

    def after_all_players_arrive(self):
        allplayers = self.group.get_players()
        # assign subgroups
        for i, p in enumerate(allplayers):
            p.subgroup = Constants.groupset[i]
            p.pair = Constants.threesomesets[i]
        for p in allplayers:
            # we define the which random pair will be shown to the participants
            p.random_id = random.choice([_ for _ in
                                        Constants.threesome if _ != p.pair])
            p.set_pd_payoff()


class Pun(MyPage):
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

class Survey(MyPage):
    form_model=models.Player
    def extra_is_displayed(self):
        return self.round_number == 1
    def get_form_fields(self):
        q_set = ['survey_q{}'.format(i) for i in range(1,6)]
        return q_set

page_sequence = [
    # Survey,
    # FirstWP,
    # SecondWP,
    # InstructionsStage1,
    # InstructionsStage2,
    # ControlQuestions1,
    # ControlQuestions2,
    # CheckingAnswers,
    PD,
    WaitPD,
    Pun,
    WaitResults,
    Results,
    # FinalResults,
]
