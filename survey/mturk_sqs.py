import boto3
import json
qname='asdf'
sqs= boto3.resource('sqs', )
response = sqs.create_queue(
    QueueName=qname,
    Attributes={
        'ReceiveMessageWaitTimeSeconds': '1',
        'VisibilityTimeout':'0',
    }
)

q = boto3.resource("sqs").get_queue_by_name(QueueName=qname)
#
qarn = q.attributes.get('QueueArn')
print(qarn)
settings = {'qarn': qarn}

qpolicy = {
    "Version": "2012-10-17",
    "Id": "{qarn}/SQSDefaultPolicy".format(**settings),
    "Statement": [
        {
            "Sid": "Sid1506848932798",
            "Effect": "Allow",
            "Principal": {
                "Service": "mturk-requester.amazonaws.com"
            },
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
endpoint_url = 'https://mturk-requester.us-east-1.amazonaws.com'
response = boto3.client('mturk').send_test_event_notification(
    Notification={
        'Destination': q.url,
        'Transport': 'SQS',
        'Version': '2006-05-05',
        'EventTypes': [
            'Ping'
        ]
    },
    TestEventType='Ping'
)

counter = 0
while len(q.receive_messages()) > 0:
    counter += 1
    for message in q.receive_messages():
        d = json.loads(message.body)
        if d.get('Events'):
            for e in d['Events']:
                print('EVENT TYPE: {event}'.format(event=e['EventType']))
                print('EVENT ASSIGNMENT: {event}'.format(event=e['AssignmentId']))
        message.delete()

q.delete()