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
from colsan_small.models import Group, Player
from otree.models import Participant
import json

CONNECT = 1
DISCONNECT = 0


class GenericWatcher(WebsocketConsumer):
    url_pattern = (
        r'^/watcher' +
        '/group/(?P<group_pk>[0-9]+)' +
        '/participant/(?P<participant_code>[a-zA-Z0-9_-]+)' +
        '/player/(?P<player_pk>[a-zA-Z0-9_-]+)' +
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

    def get_num_connected_in_group(self):
        group_pk = self.kwargs['group_pk']
        cur_page = self.get_cur_page()
        cur_group = Group.objects.get(pk__exact=group_pk)
        num_those_here = cur_group.player_set.filter(participant___index_in_pages=cur_page).count()
        return num_those_here

    def update_connected(self):
        number_connected = self.get_num_connected_in_group()
        group_name = self.get_group(self.kwargs['group_pk'])
        self.group_send(name=group_name, text=json.dumps({'number_connected': number_connected}))

    def update_time_stamp(self):
        player = Player.objects.get(pk__exact=self.kwargs['player_pk'])
        if self.event_type == CONNECT:
            timestamp, _ = player.timestamps.update_or_create(player=player,  cur_page=self.get_cur_page(),
                                                              defaults={'opened': True})
        if self.event_type == DISCONNECT:
            timestamp, _ = player.timestamps.update_or_create(player=player, cur_page=self.get_cur_page(),
                                                              defaults={'opened': False})



    def process_connection(self):
        self.update_connected()
        self.update_time_stamp()

    def connect(self, message, **kwargs):
        self.event_type = CONNECT
        self.process_connection()

    def disconnect(self, message, **kwargs):
        self.event_type = DISCONNECT
        self.process_connection()

    def receive(self, text=None, bytes=None, **kwargs):
        self.send(text=text, bytes=bytes)
