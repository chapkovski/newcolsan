from os import environ
from otree.views import Page


def debug_session(page):
    if isinstance(page, Page):
        env_debug = environ.get('STOFF_DEBUG', False)
        if env_debug:
            return True
        return page.session.config.get('debug', False)


class Struct:
    def __init__(self, **entries):
        self.__dict__.update(entries)

from otree.models import Participant
from colsan_small.models import Constants
import statuses

def check_and_update_NEPS(session, index_in_pages):
    all_parts_to_notify = Participant.objects.filter(_index_in_pages__lte=index_in_pages, session=session)
    healthy_statuses = [statuses.HEALTHY, statuses.NON_INITIATED]
    all_parts_to_notify = [p for p in all_parts_to_notify if p.vars['status'] in healthy_statuses]
    NEPS = len(all_parts_to_notify) < Constants.players_per_group
    if NEPS:
        for p in all_parts_to_notify:
            p.vars['status'] = statuses.NOT_ENOUGH_PLAYERS_IN_SESSION
            p.save()
    return NEPS