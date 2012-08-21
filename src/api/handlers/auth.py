from handlers.base import BaseHandler
from tornado.escape import *

import logging
logger = logging.getLogger()


class AuthHandler(BaseHandler):
    def get(self):
        self.write("Error, no parameters were passed")
    
    def post(self):
        fb_auth_key = self.get_argument("fb_auth_key", "")
        fb_expires = self.get_argument("fb_expires", "")

        # Connect to Facebook API and update MySQLdb
        
        # Send confirmation of success
        details = {'status':'success', 'fb_auth_key': fb_auth_key, 'fb_expires':fb_expires}
        json = json_encode(details)
        self.write(json)

        
