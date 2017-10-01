from otree.api import Currency as c, currency_range
from . import models
from ._builtin import Page, WaitPage
from .models import Constants
from django.conf import settings
import boto3
from otree.views.mturk import get_mturk_client

import json

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
                qname = self.session.code
                from django.conf import settings
                sqs = boto3.resource('sqs',
                                     aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                                     aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                                     region_name='us-east-1',
                                     )
                response = sqs.create_queue(
                    QueueName=qname,
                    Attributes={
                        'ReceiveMessageWaitTimeSeconds': '1',
                        'VisibilityTimeout': '0',
                    }
                )

                q =sqs.get_queue_by_name(QueueName=qname)
                #
                qarn = q.attributes.get('QueueArn')
                print(qarn)
                settings = {'qarn': qarn}
            
                qpolicy = {
                    "Version": "2012-10-17",
                    "Id": "{qarn}/SQSDefaultPolicy".format(**settings),
                    "Statement": [
                        {
                            "Sid": "Sid1506848932798{}".format(self.session.code),
                            "Effect": "Allow",
                            "Principal": "*",
                            "Action": "SQS:SendMessage",
                            "Resource": qarn,
                            "Condition": {
                                "StringEquals": {
                                    "aws:SecureTransport": "true"
                                }
                            }
                        }
                    ]
                }

                queue_attrs = {"Policy": json.dumps(qpolicy), }
                q.set_attributes(Attributes=queue_attrs)
                print(q.attributes)
                # endpoint_url = 'https://mturk-requester.us-east-1.amazonaws.com'



                # q.delete()
                self.subsession.sqs_url = q.url
                if self.session.mturk_HITId:
                    client = get_mturk_client(use_sandbox=self.session.mturk_use_sandbox)
                    HITTypeId = client.get_hit(HITId=self.session.mturk_HITId)['HIT']['HITTypeId']

                    response = client.update_notification_settings(
                        HITTypeId=HITTypeId,
                        Notification={
                            'Destination': self.subsession.sqs_url,
                            'Transport': 'SQS',
                            'Version': '2006-05-05',
                            'EventTypes': [
                                'AssignmentAccepted', 'AssignmentAbandoned', 'AssignmentReturned',
                                'AssignmentSubmitted', 'HITExpired',
                            ]
                        },
                        Active=True,
                    )
                    print('$$$$$$$$$$$$$$$$$$ ', response)
                    # response = client.send_test_event_notification(
                    #     Notification={
                    #         'Destination': q.url,
                    #         'Transport': 'SQS',
                    #         'Version': '2006-05-05',
                    #         'EventTypes': [
                    #             'Ping'
                    #         ]
                    #     },
                    #     TestEventType='Ping'
                    # )

        return True


class Results(Page):
    def is_displayed(self):
        # if self.session.mturk_HITId:
        #     sqs = boto3.resource('sqs',
        #                          aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        #                          aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        #                          region_name='us-east-1',
        #                          )
        #     # Get the queue
        #     q = sqs.get_queue_by_name(QueueName=self.session.code)
        #     counter = 0
        #     while len(q.receive_messages()) > 0:
        #         counter += 1
        #         for message in q.receive_messages():
        #             d = json.loads(message.body)
        #             print(d)
        #             # if d.get('Events'):
        #             #     for e in d['Events']:
        #             #         print('EVENT TYPE: {event}'.format(event=e['EventType']))
        #             #         print('EVENT ASSIGNMENT: {event}'.format(event=e['AssignmentId']))
        #             message.delete()
        return True


page_sequence = [
    Survey,
    Results,
]
