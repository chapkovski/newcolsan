from os import environ
from otree.views import Page


def debug_session(page):
    if isinstance(page, Page):
        env_debug = environ.get('STOFF_DEBUG', False)
        if env_debug:
            return True
        return page.session.config.get('debug', False)

