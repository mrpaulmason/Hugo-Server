from handlers.base import BaseHandler

import logging
logger = logging.getLogger()


class PlacesHandler(BaseHandler):
    def get(self):
        self.render("places.json")