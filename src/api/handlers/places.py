from handlers.base import BaseHandler
from boto.dynamodb.condition import *
import code, operator

import boto.dynamodb
import time, simplejson
import geohash, sys

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
    def get(self, place_id="103", slug=""):
        
        self.render('places.html', title=slug.replace("_"," "))
    
    # TODO: Need key signatuare to prevent data theft
    def post(self):
        hugo_id = self.get_argument("hugo_id", "1")
        latitude = self.get_argument("lat", "37.7621353")
        longitude = self.get_argument("long", "-122.4661777")
        category = self.get_argument("category","")
        signature = self.get_argument("signature","")
        fb_place_id = self.get_argument("fb_place_id","")
        precision = self.get_argument("precision", "6")
        
        precision = int(precision)
        
        if category == "All Nearby":
            category = ""
                
        dbconn = boto.dynamodb.connect_to_region('us-west-1', aws_access_key_id='AKIAJG4PP3FPHEQC76HQ',
                                   aws_secret_access_key='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')
        table = dbconn.get_table("checkin_data")
        tableComments = dbconn.get_table("comment_data")

        while True:
                        
            result = table.query(
                hash_key = int(hugo_id), 
                range_key_condition = BEGINS_WITH(geohash.encode(float(latitude), float(longitude), precision=precision)))

            items = []  
            
            for item in result:
                found = None

                if ('spot_categories' not in item or item['spot_categories'].find(category) == -1) and ('spot_category' not in item or item['spot_category'].find(category) == -1):
                    continue
                                    
                for pItem in items:
                    spotMatch = levenshtein(item['spot_name'], pItem['spot_name'])/float(max(len(item['spot_name']), len(pItem['spot_name'])))
                    locationMatch = levenshtein(item['geohash_raw'], pItem['geohash_raw'])/13.0
                    
                    if spotMatch < 0.50 and locationMatch < 0.50:
                        found = pItem

                if found != None:
                    
                    if len(found['spot_location']) < len(item['spot_location']):
                        found['spot_location'] = item['spot_location']

                    if found['spot_checkins'] < item['spot_checkins']:
                        found['spot_checkins'] = item['spot_checkins']
                                            
                    # remove duplicates
                    if item['author_uid'] in found['authors']:
                        continue
                    
                    if 'author_hugo_id' in item:
                        found['authors_hugo'].append((item['author_uid'], item['author_hugo_id']))
                        
                    found['authors'].append(item['author_uid'])
                    found['pics'].append(item['author_image'])
                else:
                    if 'author_hugo_id' in item:
                        item['authors_hugo'] = [(item['author_uid'], item['author_hugo_id'])]
                    else:
                        item['authors_hugo'] = []
                    item['authors'] = [item['author_uid']]
                    item['pics'] = [item['author_image']]
                    if fb_place_id == "":
                        items.append(item)        
                    elif str(item['fb_place_id']) == fb_place_id:
                        items.append(item)
                        
            
            items = sorted(items, key=operator.itemgetter('spot_checkins'))
            items.reverse()
            
            if (len(items) < 1 or (category == "" and fb_place_id == "" and len(items) < 5)) and precision > 4:
                precision = precision - 1
                continue
            else:
                break

        self.set_header("Content-Type", "application/json; charset=UTF-8")
            
        for item in items:
            dStatus = {}
            
            try:                
                statusItem = tableComments.get_item("spot_%s_%s" % (item['user_id'], item['fb_place_id']))
                item['statuses'] = simplejson.loads(statusItem['comments'])
            except:
                print "spot_%s_%s" % (item['user_id'], fb_place_id),sys.exc_info()
                item['statuses'] = []
            
            for x,y in item['authors_hugo']:
                print x,y
                try:
                    commentsRow = tableComments.get_item(hash_key='spot_%s_%s' % (str(y), item['fb_place_id']))
                    commentsData = simplejson.loads(commentsRow['comments'])
                    lTimestamp = None
                    lComment = None
                    for comment in commentsData:
                        if comment['comment_type'] == "spot_status" and lTimestamp == None or comment['timestamp'] > lTimestamp:
                            lTimestamp = comment['timestamp']
                            lComment = comment['comment_message']                                                             
                    dStatus[x] = (lTimestamp, lComment)
                except:
                    print 'spot_%s_%s' % (str(y), fb_place_id)
                    print sys.exc_info()
                    pass
            item['spot_statuses'] = dStatus

                    
        self.write(simplejson.dumps(items,sort_keys=True, indent=4))
        
class CategoriesHandler(BaseHandler):
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

            cats = []  
            

            for item in result:
                
                if 'spot_category' in item:
                    cats.append(item['spot_category'])
                
                try:
                    item_categories = simplejson.loads(item['spot_categories'])
                    for cat in item_categories:
                        cats.append(cat['name'])
                except:
                    pass

            cat_hash = {}
        
            for item in cats:
                if item in cat_hash:
                    cat_hash[item] = cat_hash[item] + 1
                else:
                    cat_hash[item] = 1

            sorted_cats = sorted(cat_hash.iteritems(), key=operator.itemgetter(1))
            sorted_cats.reverse()
        
            print sorted_cats
        
            cats = [x for (x, a) in sorted_cats if a > 1]

            if len(cats) < 5 and precision > 4:
                precision = precision - 1
                continue
            else:
                break

        cats.insert(0,"All Nearby")
        
        json = {}
        json['precision'] = precision
        json['categories'] = cats

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(simplejson.dumps(json,sort_keys=True, indent=4))
        