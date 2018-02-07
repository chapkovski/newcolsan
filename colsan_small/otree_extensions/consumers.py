# There are two classes of GenericWatcher.
# GenericWatcher
# ***** it returns on disconnect, connect, and on request message how many participants from the group are in the
# waiting room
# ***** it returns how much time has been spent so far on all waiting pages
# ***** it returns how much money has been earned by waiting so far
# # GroupWatcher also does:
# ***** checking whether there are no dropouts in a group
# FirstWPWatcher does:
# ***** checking for the first waiting page whether there are enough players in subsession


from channels.generic.websockets import WebsocketConsumer, JsonWebsocketConsumer
from colsan_small.models import Group, Player, TimeStamp, Constants
from otree.models import Participant
import json
# from django.db.models import F, DateTimeField, ExpressionWrapper, IntegerField, DurationField, FloatField, Sum
from django.db.models import Q
import datetime
import statuses
from functions import check_and_update_NEPS
from colsan_small.views import FIRST_WP, OTHER_WP
from django.core.exceptions import ObjectDoesNotExist

CONNECT = 1
DISCONNECT = 0


class GenericWatcher(WebsocketConsumer):
    url_pattern = (
        r'^/watcher' +
        '/group/(?P<group_pk>[0-9]+)' +
        '/participant/(?P<participant_code>[a-zA-Z0-9_-]+)' +
        '/player/(?P<player_pk>[a-zA-Z0-9_-]+)' +
        '/page_type/(?P<page_type>[0-9]+)' +
        '$')
    event_type = None

    def get_group(self, group_pk):
        return 'watcher_for_group_{}'.format(group_pk)

    def connection_groups(self, **kwargs):
        group_name = self.get_group(self.kwargs['group_pk'])
        return [group_name]

    def get_cur_page(self):
        participant_code = self.kwargs['participant_code']
        return Participant.objects.get(code__exact=participant_code)._index_in_pages

    def get_those_with_us(self):
        group_pk = self.kwargs['group_pk']
        cur_page = self.get_cur_page()
        try:
            cur_group = Group.objects.get(pk__exact=group_pk)
            players_with_us = cur_group.player_set.filter(participant___index_in_pages=cur_page)
            parts_with_us = [p.participant for p in players_with_us]
            return parts_with_us
        except ObjectDoesNotExist:
            print('We tried to find a group {} and failed'.format(group_pk))
            return []

    def get_num_connected_in_group(self):
        return len(self.get_those_with_us())

    def update_time_stamp(self):
        participant = Participant.objects.get(code__exact=self.kwargs['participant_code'])
        if self.event_type == CONNECT:
            timestamp, _ = participant.timestamps.update_or_create(cur_page=self.get_cur_page(),
                                                              defaults={'opened': True})
        if self.event_type == DISCONNECT:
            timestamp, _ = participant.timestamps.update_or_create(cur_page=self.get_cur_page(),
                                                              defaults={'opened': False,
                                                                        'closed_at': datetime.datetime.now()})

    def get_time_earned(self):
        participant = Participant.objects.get(code__exact=self.kwargs['participant_code'])
        ts = participant.timestamps.exclude(Q(created_at__isnull=True))

        for t in ts:
            closed = t.closed_at or datetime.datetime.now(datetime.timezone.utc)
            t.diff = closed - t.created_at
            t.save()
        if ts.exists():
            time_earned = sum([t.diff.total_seconds() for t in participant.timestamps.all() if t.diff is not None])
            return time_earned
        else:
            return 0

    # checking that there is enough participants left in subsession
    # NEPS stays for Not Enough Players in Session
    # Returns True if NEPS


    def _check_NEPS(self):
        player = Player.objects.get(pk__exact=self.kwargs['player_pk'])
        return check_and_update_NEPS(player.session, self.get_cur_page(), player.round_number, player.group)

    def process_connection(self):
        num_connected = self.get_num_connected_in_group()
        self.update_time_stamp()
        group_name = self.get_group(self.kwargs['group_pk'])
        group_msg = {'number_connected': num_connected, }
        msg = self.get_back_request()
        page_type = self.kwargs['page_type']
        if int(page_type) == FIRST_WP:
            NEPS = {'not_enough_players_in_subsession': self._check_NEPS()}
            group_msg.update(NEPS)
            msg.update(NEPS)
        self.group_send(name=group_name, text=json.dumps(group_msg))
        self.send(text=json.dumps(msg))

    def connect(self, message, **kwargs):
        self.event_type = CONNECT
        self.process_connection()

    def disconnect(self, message, **kwargs):
        self.event_type = DISCONNECT
        self.process_connection()

    def get_back_request(self):
        time_so_far = self.get_time_earned()
        player = Player.objects.get(pk__exact=self.kwargs['player_pk'])
        session = player.session
        earn_so_far = time_so_far/60 * float(Constants.payment_per_minute.to_real_world_currency(session))
        return {'time_earned': time_so_far,
                'earn_so_far': round(earn_so_far, 2),
                }

    def receive(self, text=None, bytes=None, **kwargs):
        try:
            jsn_msg = json.loads(text)
            if jsn_msg.get('update_request'):
                self.send(text=json.dumps(self.get_back_request()))
        except ValueError:
            print('no json received')
