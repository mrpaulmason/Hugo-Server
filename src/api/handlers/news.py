from handlers.base import BaseHandler
from boto.dynamodb.condition import *
import code, operator

import boto.dynamodb
import time, simplejson
import geohash, sys

import logging
logger = logging.getLogger()

class NewsHandler(BaseHandler):
    def get(self):
        self.write("Error, no parameters were passed")
    
    # TODO: Need key signatuare to prevent data theft
    def post(self):
        hugo_id = self.get_argument("hugo_id", "1")
        prefix = self.get_argument("prefix", "newsfeed")
        signature = self.get_argument("signature","")
                        
        dbconn = boto.dynamodb.connect_to_region('us-west-1', aws_access_key_id='AKIAJG4PP3FPHEQC76HQ',
                                   aws_secret_access_key='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')
        table = dbconn.get_table("newsfeed_data")
        commentTable = dbconn.get_table("comment_data")

        result = table.query(
            hash_key = "%s_%d" % (prefix, int(hugo_id)), 
            max_results = 25, 
            scan_index_forward = False)

        items = []  
#        itemList = []
#        dynamoBatch = dbconn.new_batch_list()
            
        for item in result:
            try:
                commentItem = commentTable.get_item("spotting_%d" % item['id'])
                item['comments'] = simplejson.loads(commentItem['comments'])
            except:
                item['comments'] = []

            try:                
                statusItem = commentTable.get_item("spot_%d_%d" % (int(hugo_id), item['fb_place_id']))
                item['statuses'] = simplejson.loads(statusItem['comments'])
            except:
                item['statuses'] = []

            if 'spot_message' in item:
                item['spot_message'] = simplejson.loads(item['spot_message'])

            if 'spot_phone' in item:
                item['spot_phone'] = simplejson.loads(item['spot_phone'])

            items.append(item)        
            
#        dynamoBatch.add_batch(commentTable, itemList)
        
#        data = dynamoBatch.submit()
#        print data
                        
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(simplejson.dumps(items,sort_keys=True, indent=4))