from handlers.base import BaseHandler
from tornado.escape import *
import tornado.web
import logging, os, sys
import facebook
import time
import simplejson
import sys
import MySQLdb
import boto.dynamodb
import geohash
from boto.dynamodb.condition import *


logger = logging.getLogger()


class AddPostHandler(BaseHandler):
    def get(self):
        raise tornado.web.HTTPError(404)
    
    # TODO: Vulnerable for injection
    def post(self):
        fb_auth_key = self.get_argument("fb_auth_key", "")
        fb_expires = self.get_argument("fb_expires", "")
        fb_place_id = self.get_argument("fb_place_id","")
        spot_message = self.get_argument("spot_message", "")
        photo_src = self.get_argument("photo_src","")
        photo_height = self.get_argument("photo_height",0)
        photo_width = self.get_argument("photo_width",0)
        spot_type = self.get_argument("spot_type", "here")
                
        # Move this to BaseAuthHandler
        if fb_auth_key == "" or fb_expires == "" or fb_place_id == "" or spot_type == "":
            raise tornado.web.HTTPError(400)
                
        graph = facebook.GraphAPI(fb_auth_key, timeout=5)

        try:
           json = graph.get_object("me", fields="id,name,picture,friends")
           place = graph.get_object(fb_place_id, fields="id,name,location,category,hours,phone,website,checkins")
        except:
            raise tornado.web.HTTPError(500)
                        
        conn = MySQLdb.connect (host="hugo.caqu3caxjsdg.us-west-1.rds.amazonaws.com", user="hugo", passwd="Huego415",port=3306, db=("hugo_%s"%os.environ['HUGO_ENV'].lower()))
        cur = conn.cursor()
        
        user_id = None
        
        try:
            if cur.execute("SELECT user_id FROM hugo_%s.users WHERE facebook_id = '%s'" % (os.environ['HUGO_ENV'].lower(), json['id'])) != 0:            
                user_id = cur.fetchone()[0]                
            else:
                raise tornado.web.HTTPError(400)
        except:
            raise tornado.web.HTTPError(500)

        dbconn = boto.dynamodb.connect_to_region('us-west-1', aws_access_key_id='AKIAJG4PP3FPHEQC76HQ',
                                   aws_secret_access_key='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')
        table = dbconn.get_table("comment_data")
        tableNewsfeed = dbconn.get_table("newsfeed_data")
        tableCheckin = dbconn.get_table("checkin_data")
        tableFBHugo = dbconn.get_table("fb_hugo")

        # Update own newsfeed
        item_attr = {
                    'user_id': user_id,
                    'author_hugo_id' : user_id,
                    'bundle_id': "newsfeed_%d" % (user_id),
                    'geohash': geohash.encode(place['location']['latitude'], place['location']['longitude'], precision=13) + "_" + str(int(time.mktime(time.gmtime()))),
                    'geohash_raw' : geohash.encode(place['location']['latitude'], place['location']['longitude'], precision=13),
                    'spot_checkins' : place['checkins'],
                    'me_uid' : json['id'],
                    'author_uid' : json['id'],
                    'fb_place_id' : fb_place_id,
                    'author_name' : json['name'],
                    'author_image' : json['picture']['data']['url'],
                    'bundle_timestamp' : "%d" % (int(time.mktime(time.gmtime()))),
                    'timestamp' : "%d" % (int(time.mktime(time.gmtime()))),
                    'type' : "checkin",
                    'id' : geohash.encode(place['location']['latitude'], place['location']['longitude'], precision=13) + "_" + str(int(time.mktime(time.gmtime()))),
                    'source' : 'hugo',
                    'spot_name' : place['name'],
                    'spot_category' : place['category'],
                    'spot_location' : simplejson.dumps(place['location'])
        }
                
        if 'hours' in place:
            item_attr.update({
                'spot_hours':simplejson.dumps(place['hours'])
            })

        if 'phone' in place:
            item_attr.update({
                'spot_phone':simplejson.dumps(place['phone'])
            })

        if 'website' in place:
            item_attr.update({
                'spot_website':simplejson.dumps(place['website'])
            })
        
        if photo_src != "":
                item_attr.update({
                    'photo_width': photo_width,
                    'photo_height' : photo_height,
                    'photo_src' : photo_src
                    })
        
        if spot_message != "":
            item_attr.update({
                'spot_message': simplejson.dumps(spot_message),
                })        

        dItem = tableNewsfeed.new_item(attrs=item_attr)
        dItem.put()
        dItem = tableCheckin.new_item(attrs=item_attr)
        dItem.put()

        # Loop through all friends and add update
        
        for friend in json['friends']['data']:
            try:
                fArr = tableFBHugo.get_item(friend['id'])
                item_attr['me_uid'] = friend['id']
                item_attr['bundle_id'] = "newsfeed_%s" % (fArr['hugo_id'])
                dItem = tableNewsfeed.new_item(attrs=item_attr)
                dItem.put()                 
            except:
#                print sys.exc_info()
                pass            
                
        # Add statuses to comment table
        item = None
        
        try:
            item = table.get_item("spot_%d_%s" % (user_id, fb_place_id))
        except:
            item = table.new_item(hash_key="spot_%d_%s" % (user_id, fb_place_id))
            
        try:
            statuses = simplejson.loads(item['comments'])
        except:
            statuses = []
            
        item_attr = {
                    'user_id' : user_id,
                    'timestamp' : int(time.mktime(time.gmtime())),
                    'comment_message' : spot_type,
                    'comment_type' : "spot_status",
                    'name' : json['name']
                    }

        statuses.append(item_attr)
        item['comments'] = simplejson.dumps(statuses)

        try:
            item.save()
        except:
            raise tornado.web.HTTPError(500)
                
        # Send confirmation of success
        details = {'status':'success', 'user_id':user_id}
        details['results'] = statuses 
        
        self.content_type = 'application/json'
        self.write(details)                

    
