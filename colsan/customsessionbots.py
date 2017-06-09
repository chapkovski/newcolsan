

import logging
from collections import OrderedDict
from unittest import mock

from django.db.migrations.loader import MigrationLoader
from django.conf import settings
import pytest
import sys

import otree.session
import otree.common_internal

# from .bot import ParticipantBot
import datetime
import os
import codecs
import otree.export
from otree.constants_internal import AUTO_NAME_BOTS_EXPORT_FOLDER
import time
# logger = logging.getLogger(__name__)
from otree.bots.bot import ParticipantBot
from otree.bots.runner import SessionBotRunner

class MySessionBotRunner(SessionBotRunner):
    def play(self):
        '''round-robin'''
        self.open_start_urls()
        loops_without_progress = 0
        while True:
            if len(self.bots) == 0:
                return
            # bots got stuck if there's 2 wait pages in a row
            if loops_without_progress > 1000:
                return
            #     raise AssertionError('Bots got stuck')
            print(loops_without_progress)
            time.sleep(2)
            # store in a separate list so we don't mutate the iterable
            playable_ids = list(self.bots.keys())
            progress_made = False
            for pk in playable_ids:
                bot = self.bots[pk]
                if bot.on_wait_page():
                    pass
                else:
                    try:
                        submission = next(bot.submits_generator)
                    except StopIteration:
                        # this bot is finished
                        self.bots.pop(pk)
                        progress_made = True
                    else:
                        bot.submit(submission)
                        progress_made = True
            if not progress_made:
                loops_without_progress += 1
