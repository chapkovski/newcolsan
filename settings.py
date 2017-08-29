import os
from os import environ

import dj_database_url
from boto.mturk import qualification

import otree.settings
CHANNEL_ROUTING = 'customwp.routing.channel_routing'
SENTRY_DSN = 'http://7c5c585cf09a40a99907285d455d12cd:c33248dd43e04a27a9129191629bf453@sentry.otree.org/64'
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
INSTALLED_APPS = ['otree']

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
    'keywords': ['easy', 'bonus', 'choice', 'study'],
    'title': 'Title for your experiment',
    'description': 'Description for your experiment',
    'frame_height': 500,
    'preview_template': 'global/MTurkPreview.html',
    'minutes_allotted_per_assignment': 60,
    'expiration_hours': 7*24,  # 7 days
    # 'grant_qualification_id': 'YOUR_QUALIFICATION_ID_HERE',# to prevent retakes
    'qualification_requirements': [
        # qualification.LocaleRequirement("EqualTo", "US"),
        # qualification.PercentAssignmentsApprovedRequirement("GreaterThanOrEqualTo", 50),
        # qualification.NumberHitsApprovedRequirement("GreaterThanOrEqualTo", 5),
        # qualification.Requirement('YOUR_QUALIFICATION_ID_HERE', 'DoesNotExist')
    ]
}

# if you set a property in SESSION_CONFIG_DEFAULTS, it will be inherited by all configs
# in SESSION_CONFIGS, except those that explicitly override it.
# the session config can be accessed from methods in your apps as self.session.config,
# e.g. self.session.config['participation_fee']

SESSION_CONFIG_DEFAULTS = {
    'real_world_currency_per_point': 0.000,
    'participation_fee': 0.00,
    'doc': "",
    'mturk_hit_settings': mturk_hit_settings,
}


SESSION_CONFIGS = [
    {
        'name': 'nocolsan',
        'display_name': 'Individual sanctions - Outgroup and Ingroup',
        'num_demo_participants': 6,
        'app_sequence': ['customwp', 'colsan'],
        'colsan':False,
        'ingroup': True,
        'outgroup': True,
    },
    {
        'name': 'colsan',
        'display_name': 'Collective sanctions - Outgroup and Ingroup',
        'num_demo_participants': 6,
        'app_sequence': ['customwp', 'colsan'],
        'colsan':True,
        'ingroup': True,
        'outgroup': True,
    },
    {
        'name': 'colsanoutgroup',
        'display_name': 'Individual sanctions - Outgroup only',
        'num_demo_participants': 6,
        'app_sequence': ['customwp', 'colsan'],
        'colsan':False,
        'ingroup': False,
        'outgroup': True,
    },
    {
        'name': 'indsanoutgroup',
        'display_name': 'Collective sanctions - Outgroup only',
        'num_demo_participants': 6,
        'app_sequence': ['customwp', 'colsan'],
        'colsan': True,
        'ingroup': False,
        'outgroup': True,
    },

]

# anything you put after the below line will override
# oTree's default settings. Use with caution.

otree.settings.augment_settings(globals())
# print('BEFORE::: ', CHANNEL_LAYERS['inmemory']['BACKEND'])
# CHANNEL_LAYERS['inmemory']['BACKEND'] = 'otree.channels.asgi_redis.RedisChannelLayer'
# print('AFTER::: ', CHANNEL_LAYERS['inmemory']['BACKEND'])
