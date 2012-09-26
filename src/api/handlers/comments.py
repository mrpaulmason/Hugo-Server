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
from boto.dynamodb.condition import *


logger = logging.getLogger()


class CommentsHandler(BaseHandler):
    def get(self):
        fb_post_id = self.get_argument("fb_post_id","")
        if fb_post_id == "":
            raise tornado.web.HTTPError(403)
        
        print fb_post_id
        
        dbconn = boto.dynamodb.connect_to_region('us-west-1', aws_access_key_id='AKIAJG4PP3FPHEQC76HQ',
                                   aws_secret_access_key='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')
        table = dbconn.get_table("newsfeed_data")
        result = table.query(
            hash_key = "spotting_%s" % fb_post_id) 

        json_response = {}
        json_response['post_id'] = fb_post_id

        items = []  
            
        for item in result:
            items.append(item)        

        json_response['results'] = items 
                        
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(simplejson.dumps(json_response,sort_keys=True, indent=4))
    
    # TODO: Vulnerable for injection
    def post(self):
        fb_auth_key = self.get_argument("fb_auth_key", "")
        fb_expires = self.get_argument("fb_expires", "")
        fb_post_id = self.get_argument("fb_post_id","")
        comment_message = self.get_argument("comment_message", "")
        comment_type = self.get_argument("comment_type","")
                
        # Move this to BaseAuthHandler
        if comment_type == "" or fb_auth_key == "" or fb_expires == "" or (comment_type == "chat" and comment_message == ""):
            raise tornado.web.HTTPError(400)
                
        graph = facebook.GraphAPI(fb_auth_key, timeout=5)

        try:
           json = graph.get_object("me", fields="id,name")
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
        table = dbconn.get_table("newsfeed_data")
                
        if comment_type=='unlike':
            found = False
            result = table.query(
                    hash_key = "spotting_%s" % fb_post_id, 
                    range_key_condition = BEGINS_WITH("%d_" % (user_id)))

            for item in result:           
                if item['comment_type'] == 'like':
                    item.delete() 
                    found = True
            
            if found == True:
                self.content_type = 'application/json'
                details = {'status':'success', 'user_id':user_id}
                self.write(details)
            else:
                raise tornado.web.HTTPError(404)
        elif comment_type=="like" or comment_type == "chat":
            try:    
                item_attr = {
                        'bundle_id': "spotting_%s" % (fb_post_id),
                        'bundle_timestamp' : "%d_%d" % (user_id,int(time.mktime(time.gmtime()))),
                        'user_id' : user_id,
                        'timestamp' : int(time.mktime(time.gmtime())),
                        'comment_type' : comment_type,
                        }

                if comment_message != "":
                    item_attr['comment_message'] = comment_message
                
                dItem = table.new_item(attrs=item_attr)
                dItem.put()
            except:
                print sys.exc_info()
                raise tornado.web.HTTPError(403)
                    
            # Send confirmation of success
            self.content_type = 'application/json'
            details = {'status':'success', 'user_id':user_id, 'item_data': item_attr}
            self.write(details)
        else:
            raise tornado.web.HTTPError(404)


        
