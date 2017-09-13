from os import environ


def debug_session(self):
    env_debug = environ.get('STOFF_DEBUG', False)
    if env_debug:
        return True
    return self.session.config.get('debug', False)
