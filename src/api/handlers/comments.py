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
        comment_type = self.get_argument("comment_type", "spotting")
        user_id = self.get_argument("user_id","")
        fb_post_id = self.get_argument("fb_post_id","")

        if fb_post_id == "":
            raise tornado.web.HTTPError(403)
                
        dbconn = boto.dynamodb.connect_to_region('us-west-1', aws_access_key_id='AKIAJG4PP3FPHEQC76HQ',
                                   aws_secret_access_key='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')
        table = dbconn.get_table("comment_data")

        json_response = {}

        if comment_type == "spotting":
            json_response['post_id'] = fb_post_id
            item = table.get_item("spotting_%s" % fb_post_id)
        else:
            json_response['spot_id'] = fb_post_id
            json_response['user_id'] = user_id
            item = table.get_item("spot_%s_%s" % (user_id, fb_post_id))

        json_response['results'] = simplejson.loads(item['comments']) 
                        
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
        table = dbconn.get_table("comment_data")
                
        if comment_type=='unlike':
            try:
                item = table.get_item("spotting_%s" % fb_post_id)
            except:
                raise tornado.web.HTTPError(404)
            
            comments = simplejson.loads(item['comments'])
            
            filteredComments = [x for x in comments if not (x['comment_type'] == "like" and x['user_id'] == user_id) ]
            
            item['comments'] = simplejson.dumps(filteredComments)

            try:
                item.save()
            except:
                raise tornado.web.HTTPError(500)
            
            self.content_type = 'application/json'
            details = {'status':'success', 'user_id':user_id}
            details['results'] = filteredComments 
            self.write(details)
        elif comment_type=="spot_status":
            item = None
            
            try:
                item = table.get_item("spot_%d_%s" % (user_id, fb_post_id))
            except:
                item = table.new_item(hash_key="spot_%d_%s" % (user_id, fb_post_id))
                
            try:
                statuses = simplejson.loads(item['comments'])
            except:
                statuses = []
                
            item_attr = {
                        'user_id' : user_id,
                        'timestamp' : int(time.mktime(time.gmtime())),
                        'comment_message' : comment_message,
                        'comment_type' : comment_type,
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
        elif comment_type=="like" or comment_type == "chat":
            item = None

            try:    
                item = table.get_item("spotting_%s" % fb_post_id)
            except:
                item = table.new_item(hash_key="spotting_%s" % fb_post_id)
                
            try:
                comments = simplejson.loads(item['comments'])
            except:
                comments = []            

            item_attr = {
                        'user_id' : user_id,
                        'timestamp' : int(time.mktime(time.gmtime())),
                        'comment_message' : comment_message,
                        'comment_type' : comment_type,
                        'name' : json['name']
                        }

            comments.append(item_attr)
            item['comments'] = simplejson.dumps(comments)

            try:
                item.save()
            except:
                raise tornado.web.HTTPError(500)
                    
            # Send confirmation of success
            details = {'status':'success', 'user_id':user_id}
            details['results'] = comments 
            
            self.content_type = 'application/json'
            self.write(details)
        else:
            raise tornado.web.HTTPError(404)


        
