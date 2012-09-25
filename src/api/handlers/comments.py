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

        items = []  
            
        for item in result:
            items.append(item)        
                        
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(simplejson.dumps(items,sort_keys=True, indent=4))
    
    # TODO: Vulnerable for injection
    def post(self):
        fb_auth_key = self.get_argument("fb_auth_key", "")
        fb_expires = self.get_argument("fb_expires", "")
        fb_post_id = self.get_argument("fb_post_id","")
        comment_message = self.get_argument("comment_message", "")
        comment_type = self.get_argument("comment_type","")
                
        # Move this to BaseAuthHandler
        if comment_type == "" or fb_auth_key == "" or fb_expires == "" or (comment_type == "chat" and comment_message == ""):
            raise tornado.web.HTTPError(403)
                
        graph = facebook.GraphAPI(fb_auth_key, timeout=5)

        try:
           json = graph.get_object("me", fields="id,name")
        except:
            raise tornado.web.HTTPError(403)
                        
        conn = MySQLdb.connect (host="hugo.caqu3caxjsdg.us-west-1.rds.amazonaws.com", user="hugo", passwd="Huego415",port=3306, db=("hugo_%s"%os.environ['HUGO_ENV'].lower()))
        cur = conn.cursor()
        
        user_id = None
        
        try:
            if cur.execute("SELECT user_id FROM hugo_%s.users WHERE facebook_id = '%s'" % (os.environ['HUGO_ENV'].lower(), json['id'])) != 0:            
                user_id = cur.fetchone()[0]                
            else:
                raise tornado.web.HTTPError(403)
        except:
            raise tornado.web.HTTPError(403)

        dbconn = boto.dynamodb.connect_to_region('us-west-1', aws_access_key_id='AKIAJG4PP3FPHEQC76HQ',
                                   aws_secret_access_key='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')
        table = dbconn.get_table("newsfeed_data")
                
        item_attr = {
                        'bundle_id': "spotting_%s" % (fb_post_id),
                        'timestamp' : int(time.mktime(time.gmtime())),
                        'comment_type' : comment_type,
                        'comment_message' : comment_message
            }
        
        try:
            dItem = table.new_item(attrs=item_attr)
            dItem.put()
        except:
            raise tornado.web.HTTPError(403)
                    
        # Send confirmation of success
        self.content_type = 'application/json'
        details = {'status':'success', 'user_id':user_id}
        self.write(details)


        
