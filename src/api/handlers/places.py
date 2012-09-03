from handlers.base import BaseHandler
from boto.dynamodb.condition import *

import boto.dynamodb
import time, simplejson
import geohash

import logging
logger = logging.getLogger()

def levenshtein(seq1, seq2):
    oneago = None
    thisrow = range(1, len(seq2) + 1) + [0]
    for x in xrange(len(seq1)):
        twoago, oneago, thisrow = oneago, thisrow, [0] * len(seq2) + [x + 1]
        for y in xrange(len(seq2)):
            delcost = oneago[y] + 1
            addcost = thisrow[y - 1] + 1
            subcost = oneago[y - 1] + (seq1[x] != seq2[y])
            thisrow[y] = min(delcost, addcost, subcost)
    return thisrow[len(seq2) - 1]

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

        precision = 6

        while True:
            result = table.query(
                hash_key = int(hugo_id), 
                range_key_condition = BEGINS_WITH(geohash.encode(float(latitude), float(longitude), precision=precision)))

            items = []  

            for item in result:
                found = None
                
                if 'spot_name' not in item:
                    continue
                
                for pItem in items:
                    if levenshtein(item['spot_name'], pItem['spot_name']) <= 4:
                        found = pItem

                if found != None:
                    found['authors'].append(item['author_uid'])
                    found['pics'].append(item['person_pic_small'])
                else:
                    item['authors'] = [item['author_uid']]
                    item['pics'] = [item['person_pic_small']]
                    items.append(item)        
            
            if len(items) < 5:
                precision = precision - 1
                continue
            else:
                break

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(simplejson.dumps(items,sort_keys=True, indent=4))
        
        
        