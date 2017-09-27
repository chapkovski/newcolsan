from otree.api import Currency as c, currency_range
from . import models
from ._builtin import Page, WaitPage
from .models import Constants
import boto3
from otree.views.mturk import get_mturk_client
from django.conf import settings


class Survey(Page):
    form_model = models.Player
    form_fields = ['comment']
    timeout_seconds = 60

    def get_form_fields(self):
        if self.session.config.get('name') == 'survey':
            return ['gender', 'q1', 'q2', 'q3', ]
        else:
            return self.form_fields

    def is_displayed(self):
        if self.round_number == 1:
            if not self.subsession.notification_set:
                self.subsession.notification_set = True
                sqs = boto3.resource('sqs',
                                     aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                                     aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                                     region_name='us-east-1',
                                     )
                # Create the queue. This returns an SQS.Queue instance
                queue = sqs.create_queue(QueueName=self.session.code)
                # You can now access identifiers and attributes
                self.subsession.sqs_url = queue.url
                if self.session.mturk_HITId:
                    client = get_mturk_client(use_sandbox=self.session.mturk_use_sandbox)
                    print('CURRENT BALANCE:: ', client.get_account_balance()['AvailableBalance'])
                    HITTypeId = client.get_hit(HITId=self.session.mturk_HITId)['HIT']['HITTypeId']

                    response = client.update_notification_settings(
                        HITTypeId=HITTypeId,
                        Notification={
                            'Destination': self.subsession.sqs_url,
                            'Transport': 'SQS',
                            'Version': '2006-05-05',
                            'EventTypes': [
                                'AssignmentReturned',
                            ]
                        },
                        Active=True
                    )
                    print('@@@@@@@ ', response)

        return True


class Results(Page):
    def is_displayed(self):
        if self.session.mturk_HITId:
            # Get the service resource
            sqs = boto3.resource('sqs',
                                 aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                                 aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                                 region_name='us-east-1',
                                 )
            # Get the queue
            queue = sqs.get_queue_by_name(QueueName=self.session.code)
            # Process messages by printing out body and optional author name
            for message in queue.receive_messages():
                print('Hello, {}'.format(message.body, ))
        return True


page_sequence = [
    Survey,
    Results,
]
