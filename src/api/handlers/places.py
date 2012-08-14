from handlers.base import BaseHandler

import logging
logger = logging.getLogger('boilerplate.' + __name__)


class PlacesHandler(BaseHandler):
    def get(self):
        self.render("places.json")