import logging
import tornado
import tornado.template
import os
from tornado.options import define, options

import environment
import logconfig

# Make filepaths relative to settings.
path = lambda root,*a: os.path.join(root, *a)
ROOT = os.path.dirname(os.path.abspath(__file__))

define("port", default=8888, help="run on the given port", type=int)
define("config", default=None, help="tornado config file")
define("debug", default=False, help="debug mode")
tornado.options.parse_command_line()

MEDIA_ROOT = path(ROOT, 'media')
TEMPLATE_ROOT = path(ROOT, 'templates')

# Deployment Configuration

class DeploymentType:
    PRODUCTION = "PRODUCTION"
    SOLO = "LOCAL"
    STAGING = "STAGING"
    dict = {
        SOLO: 1,
        PRODUCTION: 2,
        STAGING: 3
    }

if 'HUGO_ENV' in os.environ:
    DEPLOYMENT = os.environ['HUGO_ENV'].upper()
else:
    DEPLOYMENT = DeploymentType.SOLO

settings = {}
settings['debug'] = DEPLOYMENT == DeploymentType.SOLO or options.debug
settings['static_path'] = MEDIA_ROOT
settings['cookie_secret'] = "paulryanserena"
settings['xsrf_cookies'] = True
settings['template_loader'] = tornado.template.Loader(TEMPLATE_ROOT)


if settings['debug']:
    LOG_LEVEL = logging.DEBUG
else:
    LOG_LEVEL = logging.INFO

logging.getLogger().setLevel(LOG_LEVEL)

if options.config:
    tornado.options.parse_config_file(options.config)