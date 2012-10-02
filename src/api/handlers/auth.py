from handlers.base import BaseHandler
from tornado.escape import *
import tornado.web
import logging, os, sys
import facebook
import time
import simplejson
import sys
import MySQLdb
#import hugo.fb
from boto.dynamodb.condition import *
import boto.dynamodb

logger = logging.getLogger()


class AuthHandler(BaseHandler):
    def get(self):
        user_id = self.get_argument("user_id")

        conn = MySQLdb.connect (host="hugo.caqu3caxjsdg.us-west-1.rds.amazonaws.com", user="hugo", passwd="Huego415",port=3306, db=("hugo_%s"%os.environ['HUGO_ENV'].lower()))
        cur = conn.cursor()
        
        try:
            query = ("SELECT name, picture, friends, current_location from hugo_%s.users where user_id =" % os.environ['HUGO_ENV'].lower())
            query = query + "%s"
            cur.execute(query, (user_id))
            row = cur.fetchone()
        except:
            print sys.exc_info()
            raise tornado.web.HTTPError(403)            
        # Send confirmation of success
        self.content_type = 'application/json'
        details = {'status':'success', 'name': row[0], 'picture':row[1], 'friends':len(simplejson.loads(row[2])), 'current_location': row[3]}
        self.write(details)
        
            
    # TODO: Vulnerable for injection
    def post(self):
        fb_auth_key = self.get_argument("fb_auth_key", "")
        fb_expires = self.get_argument("fb_expires", "")

        graph = facebook.GraphAPI(fb_auth_key, timeout=5)
        # Connect to Facebook API and update MySQLdb
        retries = 5

        while retries > 0:
            try:
                json = graph.get_object("me", fields="id,name,first_name,last_name,picture,friends,location")
            except:
                print "Error querying FB %d" % (retries)
                retries = retries - 1
                if retries == 0:
                    self.send_error()
                    return
                else:
                    continue
            break
        
        if 'location' in json:
            location_data = graph.get_object(json['location']['id'], fields="location")       
        else:
            location_data = None
                
        user_id = None

        # Update Database
        conn = MySQLdb.connect (host="hugo.caqu3caxjsdg.us-west-1.rds.amazonaws.com", user="hugo", passwd="Huego415",port=3306, db=("hugo_%s"%os.environ['HUGO_ENV'].lower()))
        cur = conn.cursor()
        
        user_id = None
        name = json['name']
        
        added_user = False

        try:
            if cur.execute("SELECT user_id FROM hugo_%s.users WHERE facebook_id = '%s'" % (os.environ['HUGO_ENV'].lower(), json['id'])) == 0:            
                query = ("INSERT INTO users (facebook_id, facebook_auth_key, facebook_expires, name, first_name, last_name, picture, friends, current_location) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)")
                cur.execute(query, (json['id'], fb_auth_key, fb_expires, json['name'], json['first_name'], json['last_name'], json['picture']['data']['url'], simplejson.dumps(json['friends']['data']), simplejson.dumps(location_data)))
                conn.commit()
                user_id = cur.lastrowid
                added_user = True
            else:
                user_id = cur.fetchone()[0]                
                query = ("UPDATE users SET facebook_auth_key=%s, facebook_expires=%s, friends=%s, current_location=%s where user_id=%s")
                cur.execute(query, (fb_auth_key, fb_expires, simplejson.dumps(json['friends']['data']), simplejson.dumps(location_data), user_id))
                conn.commit()
                added_user = False
        except:
            print sys.exc_info()
            raise tornado.web.HTTPError(403)
            
        if added_user:
            hugo.fb.processCheckins(user_id, fb_auth_key, location_data)

        dbconn = boto.dynamodb.connect_to_region('us-west-1', aws_access_key_id='AKIAJG4PP3FPHEQC76HQ',
                               aws_secret_access_key='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')
        table = dbconn.get_table("fb_hugo")
        
        hasRecord = False
            
        try:    
            item = table.get_item("%s" % str(json['id']))
            hasRecord = True
        except:
            item = table.new_item(hash_key="%s" % str(json['id']))                    
#            item['places'] = set()
                
        item['hugo_id'] = str(user_id)
        
        try:       
            item.save()
        except:
            print sys.exc_info()
            raise tornado.web.HTTPError(500)
                
        # Send confirmation of success
        self.content_type = 'application/json'
        details = {'status':'success', 'fb_auth_key': fb_auth_key, 'fb_expires':fb_expires, 'user_id':user_id, 'name': name}
        self.write(details)


        
