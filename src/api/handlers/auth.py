from handlers.base import BaseHandler

import logging
logger = logging.getLogger()


class AuthHandler(BaseHandler):
    def get(self):
        self.write("Error, no parameters were passed")
    
    def post(self):
        fb_auth_key = self.get_argument("fb_auth_key", "")
        fb_expires = self.get_argument("fb_expires", "")
        self.write("Success! We received '%s' and '%s'" % (fb_auth_key, fb_expires))
        
