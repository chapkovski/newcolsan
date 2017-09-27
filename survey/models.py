from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)
import random

author = 'Your name here'

doc = """
Your app description
"""


class Constants(BaseConstants):
    name_in_url = 'survey'
    players_per_group = None
    num_rounds = 1


class Subsession(BaseSubsession):
    def creating_session(self):
        print('$$$$$', self.session.mturk_HITId)
        print('#####', self.session.mturk_use_sandbox)

        if self.round_number == 1:
            if self.session.mturk_HITId:
                if self.session.mturk_use_sandbox:
                    endpoint_url = 'https://mturk-requester-sandbox.us-east-1.amazonaws.com'
                else:
                    endpoint_url = 'https://mturk-requester.us-east-1.amazonaws.com'
                client = boto3.client('mturk', endpoint_url=endpoint_url)
                print('CURRENT BALANCE:: ', client.get_account_balance()['AvailableBalance'])
                HITTypeId = client.get_hit(HITId=self.session.mturk_HITId)['HIT']['HITTypeId']

                response = client.update_notification_settings(
                    HITTypeId=HITTypeId,
                    Notification={
                        'Destination': 'chapkovski@gmail.com',
                        'Transport': 'Email',
                        'Version': '2006-05-05',
                        'EventTypes': [
                            'AssignmentReturned',
                        ]
                    },
                    Active=True
                )
                print('@@@@@@@ ', response)


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    gender = models.CharField(verbose_name='Please indicate your gender',
                              choices=(('M', 'Male'), ('F', 'Female'), ('O', 'Other')))
    q1 = models.CharField(verbose_name='Have you ever participated in interactive experiments in mTurk',
                          choices=(('Y', 'Yes'), ('N', 'Now'), ('O', 'I do not know')))
    q2 = models.TextField(
        verbose_name='If you participated in interactive experiiments before, what kind of technical issues did you face? '
                     '(Too long waiting time, Small bonus payments, Non-cooperative behaviour of other participants etc..). If you did not participated in interactive experiments,'
                     'what kind of technical or other issues you would expect?')
    q3 = models.TextField(
        verbose_name='Many participants do not trust experimenters: they believe that there are no real mTurkers playing against them, but just a computer. '
                     'In your opinion what should be done in order to increase the credibility of these claims? In other words, when you would believe that you play against real mTurkers?')
    q4 = models.TextField(
        verbose_name='Have you ever experienced the situation that your bonus in academic studies has not been paid? Can you describe this situation?')
    comment = models.TextField(verbose_name='Please, provide a comment about the current experiment.'
                                            ' If you had any technical issues or questions, any remarks about how the study'
                                            ' was organized, please leave them here. Thank you!')
    last_page = models.BooleanField()

    def set_payoffs(self):
        self.payoff = random.randint(1, 10)
