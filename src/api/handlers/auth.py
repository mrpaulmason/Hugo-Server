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


logger = logging.getLogger()


class AuthHandler(BaseHandler):
    def get(self):
        self.write("Error, no parameters were passed")
    
    # TODO: Vulnerable for injection
    def post(self):
        fb_auth_key = self.get_argument("fb_auth_key", "")
        fb_expires = self.get_argument("fb_expires", "")

        # Connect to Facebook API and update MySQLdb
        graph = facebook.GraphAPI(fb_auth_key)
        json = graph.get_object("me", fields="id,name,first_name,last_name,picture,friends,location")
        
        if 'location' in json:
            location_data = graph.get_object(json['location']['id'], fields="location")       
        else:
            location_data = None
                
        user_id = None

        # Update Database
        conn = MySQLdb.connect (host="hugo.caqu3caxjsdg.us-west-1.rds.amazonaws.com", user="hugo", passwd="Huego415",port=3306, db=("hugo_%s"%os.environ['HUGO_ENV'].lower()))
        cur = conn.cursor()
        
        user_id = None
        
        added_user = False

        try:
            if cur.execute("SELECT user_id FROM hugo_%s.users WHERE facebook_id = '%s'" % (os.environ['HUGO_ENV'].lower(), json['id'])) == 0:            
                query = ("INSERT INTO users (facebook_id, facebook_auth_key, facebook_expires, name, first_name, last_name, picture, friends, location_data) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)")
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
            raise tornado.web.HTTPError(403)
            
        if added_user:
            hugo.fb.processCheckins(user_id, fb_auth_key)
        
        # Send confirmation of success
        self.content_type = 'application/json'
        details = {'status':'success', 'fb_auth_key': fb_auth_key, 'fb_expires':fb_expires, 'user_id':user_id}
        self.write(details)


        
