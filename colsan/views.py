from . import models
from ._builtin import Page, WaitPage
from .models import Constants
import random
from otree.common import safe_json


class Introduction(Page):
    def is_displayed(self):
        return self.subsession.round_number == 1

class InstructionsS1(Page):
    def is_displayed(self):
        return self.subsession.round_number == 1


class QuestionsS1(Page):
    def is_displayed(self):
        return self.subsession.round_number == 1


class PD(Page):
    form_model = models.Player
    form_fields = ['pd_decision']


class WaitPD(WaitPage):
    def after_all_players_arrive(self):
        ...


class InstructionsS2(Page):
    def is_displayed(self):
        midround = (self.subsession.round_number
                    == Constants.num_rounds_first + 1)
        return midround and self.group.outgroup


class QuestionsS2(Page):
    def is_displayed(self):
        midround = (self.subsession.round_number
                    == Constants.num_rounds_first + 1)
        return midround and self.group.outgroup


class InstructionsS3(Page):
    def is_displayed(self):
        midround = (self.subsession.round_number
                    == Constants.num_rounds_first + 1)
        return midround and self.group.ingroup


class QuestionsS3(Page):
    def is_displayed(self):
        midround = (self.subsession.round_number
                    == Constants.num_rounds_first + 1)
        return midround and self.group.ingroup


class OutgroupP(Page):
    form_model = models.Player
    form_fields = ['outgroup_punishment']

    def is_displayed(self):
        return (self.subsession.round_number >
                Constants.num_rounds_first) and self.group.outgroup


class WaitOutgroup(WaitPage):
    def is_displayed(self):
        return (self.subsession.round_number >
                Constants.num_rounds_first) and self.group.outgroup

    def after_all_players_arrive(self):
        ...


class IngroupP(Page):
    def is_displayed(self):
        return (self.subsession.round_number >
                Constants.num_rounds_first) and self.group.ingroup

    form_model = models.Player
    form_fields = ['ingroup_punishment']


class WaitIngroup(WaitPage):
    def is_displayed(self):
        return (self.subsession.round_number >
                Constants.num_rounds_first) and self.group.ingroup

    def after_all_players_arrive(self):
        ...


class Results(Page):
    ...


class FinalResults(Page):
    def is_displayed(self):
        return self.subsession.round_number == Constants.num_rounds

page_sequence = [
    Introduction,
    InstructionsS1,
    QuestionsS1,
    InstructionsS2,
    QuestionsS2,
    InstructionsS3,
    QuestionsS3,
    PD,
    WaitPD,

    OutgroupP,
    WaitOutgroup,
    IngroupP,
    WaitIngroup,
    Results,
    FinalResults,
]
