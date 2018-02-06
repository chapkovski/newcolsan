from os import environ
from otree.views import Page
from otree.models import Participant
from colsan_small.models import Constants, Player
import statuses


def debug_session(page):
    if isinstance(page, Page):
        env_debug = environ.get('STOFF_DEBUG', False)
        if env_debug:
            return True
        return page.session.config.get('debug', False)


def check_and_update_NEPS(session, index_in_pages, round_number, group):
    if round_number == 1:
        healthy_statuses = [statuses.HEALTHY, statuses.NON_INITIATED]
        all_parts_to_notify = Participant.objects.filter(_index_in_pages__lte=index_in_pages, session=session)
        participants_same_group = [p.participant for p in group.get_players() if
                                   p.participant.vars['status'] in healthy_statuses]

        all_parts_to_notify = [p for p in all_parts_to_notify if p.vars['status'] in healthy_statuses]
        total_set = set(participants_same_group + all_parts_to_notify)
        NEPS = len(total_set) < Constants.players_per_group
        if NEPS:
            for p in all_parts_to_notify:
                p.vars['status'] = statuses.NOT_ENOUGH_PLAYERS_IN_SESSION
                p.save()
        return NEPS
