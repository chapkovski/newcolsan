import os
from os import environ

import dj_database_url
from boto.mturk import qualification

import otree.settings

EXTENSION_APPS = ['colsan_small']

SENTRY_DSN = 'http://2d6137799b914e1693146c5011f39030:46838e8caa374937a91b14b59ebbe164@sentry.otree.org/36'
POINTS_DECIMAL_PLACES = 2
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# the environment variable OTREE_PRODUCTION controls whether Django runs in
# DEBUG mode. If OTREE_PRODUCTION==1, then DEBUG=False
if environ.get('OTREE_PRODUCTION') not in {None, '', '0'}:
    DEBUG = False
else:
    DEBUG = True

ADMIN_USERNAME = 'admin'

# for security, best to set admin password in an environment variable
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD')

# don't share this with anybody.
SECRET_KEY = '_mln&o1xg)6!du0$mgj=i2_r8db0lo^5ce1)h6-#b^k%vn#xkp'

# To use a database other than sqlite,
# set the DATABASE_URL environment variable.
# Examples:
# postgres://USER:PASSWORD@HOST:PORT/NAME
# mysql://USER:PASSWORD@HOST:PORT/NAME

DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///' + os.path.join(BASE_DIR, 'db.sqlite3')
    )
}

# AUTH_LEVEL:
# If you are launching a study and want visitors to only be able to
# play your app if you provided them with a start link, set the
# environment variable OTREE_AUTH_LEVEL to STUDY.
# If you would like to put your site online in public demo mode where
# anybody can play a demo version of your game, set OTREE_AUTH_LEVEL
# to DEMO. This will allow people to play in demo mode, but not access
# the full admin interface.

AUTH_LEVEL = environ.get('OTREE_AUTH_LEVEL')

# setting for integration with AWS Mturk
AWS_ACCESS_KEY_ID = environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = environ.get('AWS_SECRET_ACCESS_KEY')

# e.g. EUR, CAD, GBP, CHF, CNY, JPY
REAL_WORLD_CURRENCY_CODE = 'USD'
USE_POINTS = True

# e.g. en, de, fr, it, ja, zh-hans
# see: https://docs.djangoproject.com/en/1.9/topics/i18n/#term-language-code
LANGUAGE_CODE = 'en'

# if an app is included in SESSION_CONFIGS, you don't need to list it here
INSTALLED_APPS = ['otree',
                  'otree_export_utils'
                  ]

# SENTRY_DSN = ''

DEMO_PAGE_INTRO_TEXT = """
oTree games
"""

# from here on are qualifications requirements for workers
# see description for requirements on Amazon Mechanical Turk website:
# http://docs.aws.amazon.com/AWSMechTurk/latest/AWSMturkAPI/ApiReference_QualificationRequirementDataStructureArticle.html
# and also in docs for boto:
# https://boto.readthedocs.org/en/latest/ref/mturk.html?highlight=mturk#module-boto.mturk.qualification

mturk_hit_settings = {
    'keywords': ['bonus', 'choice', 'study', 'academic'],
    'title': 'Academic study on collective decision making (up to $4 bonus payment)',
    'description': '20 min long study. Participants have to work in groups of 6 mTurkers. If you have any issues please write as immediately at chapkovskii@soziologie.uzh.ch',
    'frame_height': 1000,
    'preview_template': 'global/MTurkPreview.html',
    'minutes_allotted_per_assignment': 180,
    'expiration_hours': 12,
    'grant_qualification_id': '3DDNYIPUQOE0H17OL5WJNNVK1E6RZB',  # colsan_outgrouponly - the name of this qualification
    'qualification_requirements': [
        {
            # Worker_Locale
            'QualificationTypeId': "00000000000000000071",
            'Comparator': "EqualTo",
            'LocaleValues': [{
                'Country': "US",
            }]
        },
        {
            # Worker_​PercentAssignmentsApproved
            'QualificationTypeId': "000000000000000000L0",
            'Comparator': "GreaterThanOrEqualTo",
            "IntegerValues": [95],
        },
        {
            # Worker_​NumberHITsApproved
            'QualificationTypeId': "00000000000000000040",
            'Comparator': "GreaterThanOrEqualTo",
            "IntegerValues": [300],
        },
        {
            'QualificationTypeId': "3CIRY6VDUW5WSALPOBLQ22DKVHVVB0",
            'Comparator': "DoesNotExist",
        },
        {
            'QualificationTypeId': "3OY1URRDRY4R2QV6PQDSN7TCTMNTIF",
            'Comparator': "DoesNotExist",
        },
        {
            'QualificationTypeId': "3BH2VZXPB8PDRPCZKDE5783ZRKC7CF",
            'Comparator': "DoesNotExist",
        },
        {
            'QualificationTypeId': "32DH4YCIPHCJENE6HELR7P0RLZNYJ6",
            'Comparator': "DoesNotExist",
        },
        {
            'QualificationTypeId': "3JQA2VZA3H07L5GGAPCKFZHKDN54IT",
            'Comparator': "DoesNotExist",
        },
        {
            'QualificationTypeId': "3DDNYIPUQOE0H17OL5WJNNVK1E6RZB",
            'Comparator': "DoesNotExist",
        },

    ],
}

#

# if you set a property in SESSION_CONFIG_DEFAULTS, it will be inherited by all configs
# in SESSION_CONFIGS, except those that explicitly override it.
# the session config can be accessed from methods in your apps as self.session.config,
# e.g. self.session.config['participation_fee']

SESSION_CONFIG_DEFAULTS = {
    'real_world_currency_per_point': 0.01,
    'participation_fee': .25,
    'doc': "",
    'mturk_hit_settings': mturk_hit_settings,
}

SESSION_CONFIGS = [
    {
        'name': 'colsan_small',
        'display_name': 'Colsan outgroup only',
        'num_demo_participants': 6,
        'app_sequence': [
            'consent',
            'colsan_small',
        ],
        'colsan': True,
        'ingroup': False,
        'outgroup': True,
        # 'debug': True,
        'outgrouponly': True,

    },

]

# anything you put after the below line will override
# oTree's default settings. Use with caution.

otree.settings.augment_settings(globals())
