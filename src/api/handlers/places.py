from handlers.base import BaseHandler
from boto.dynamodb.condition import *

import boto.dynamodb
import time, simplejson
import geohash

import logging
logger = logging.getLogger()


class PlacesHandler(BaseHandler):
    def get(self):
        self.write("Error, no parameters were passed")
    
    # TODO: Need key signatuare to prevent data theft
    def post(self):
        hugo_id = self.get_argument("hugo_id", "1")
        latitude = self.get_argument("lat", "37.7621353")
        longitude = self.get_argument("long", "-122.4661777")
        signature = self.get_argument("signature","")
        
        dbconn = boto.dynamodb.connect_to_region('us-west-1', aws_access_key_id='AKIAJG4PP3FPHEQC76HQ',
                                   aws_secret_access_key='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')
        table = dbconn.get_table("checkin_data")

        result = table.query(
          hash_key = 1, 
          range_key_condition = BEGINS_WITH(geohash.encode(float(latitude), float(longitude), precision=6)))

        items = []  

        for item in result:
            items.append(item)
        
        self.write(simplejson.dump(items,indent=4))
        