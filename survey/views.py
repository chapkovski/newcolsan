from otree.api import Currency as c, currency_range
from . import models
from ._builtin import Page, WaitPage
from .models import Constants


class Survey(Page):
    form_model = models.Player
    form_fields = ['comment']

    def get_form_fields(self):
        if self.session.config.get('name') == 'survey':
            return ['gender', 'q1', 'q2', 'q3', ]
        else:
            return self.form_fields

    def is_displayed(self):
        print('$$$$$', self.session.mturk_HITId)
        print('#####', self.session.mturk_use_sandbox)
        if self.round_number == 1:
            if not self.subsession.notification_set:
                self.subsession.notification_set = True
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

        return True


page_sequence = [
    Survey,

]
