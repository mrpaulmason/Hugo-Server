#!/usr/bin/python 
import facebook
import time
import simplejson
import sys
import MySQLdb
import os
import code

oauth_access_token="BAAGqkpC1J78BAF3RnWBOr30iU7yRT7s1byWZCE8VYfwuYSZB5IL0rcFzlEPQ5U4gcNYn3kZAp8kOBwyHBIvBue64eWsui5Eg7yzojWw2pvc9ZBR1vCmX"
graph = facebook.GraphAPI(oauth_access_token)
json = graph.get_object("me", fields="id,name,first_name,last_name,picture,friends")
fb_auth_key = oauth_access_token
fb_expires = 1000

# Update Database
conn = MySQLdb.connect (host="hugo.caqu3caxjsdg.us-west-1.rds.amazonaws.com", user="hugo", passwd="Huego415",port=3306, db=("hugo_%s"%os.environ['HUGO_ENV'].lower()))
cur = conn.cursor()

user_id = None

try:
    if cur.execute("SELECT user_id FROM hugo_%s.users WHERE facebook_id = '%s'" % (os.environ['HUGO_ENV'].lower(), json['id'])) == 0:            
        query = ("INSERT INTO users (facebook_id, facebook_auth_key, facebook_expires, name, first_name, last_name, picture) VALUES(%s, %s, %s, %s, %s, %s, %s)")
        cur.execute(query, (json['id'], fb_auth_key, fb_expires, json['name'], json['first_name'], json['last_name'], json['picture']['data']['url']))
        conn.commit()
        user_id = cur.lastrowid
    else:
        user_id = cur.fetchone()[0]                
        query = ("UPDATE users SET facebook_auth_key=%s, facebook_expires=%s where user_id=%s")
        cur.execute(query,  (fb_auth_key, fb_expires, user_id))
        conn.commit()
except:
    print("Unexpected error:" + str(sys.exc_info()))
    print(json)
    code.interact(local=locals())


sys.exit(2)
#print simplejson.dumps(json, sort_keys = False, indent=2)
#    ret = graph.fql("SELECT id, author_uid, app_id, timestamp, page_id, page_type, coords, type FROM location_post WHERE (author_uid IN (SELECT uid2 FROM friend WHERE uid1=me()) or author_uid=me()) and timestamp < %d limit %d,500" % (ts, 500*page))
#    ret = graph.fql("SELECT id, author_uid, app_id, timestamp, page_id, page_type, coords, type FROM location_post WHERE (author_uid=me()) and timestamp < %d limit %d,500" % (ts, 500*page))
#    ret = graph.fql("SELECT checkin_id, author_uid, app_id, timestamp, page_id, post_id, message, tagged_uids, coords FROM checkin WHERE (author_uid=me()) and timestamp < %d limit %d,500" % (ts, 500*page))
# boto.dynamodb.connect_to_region('us-west-1')

query = {
"query1" : "SELECT id, author_uid, app_id, timestamp, page_id, page_type, coords, type, tagged_uids  FROM location_post WHERE (author_uid IN (SELECT uid2 from friend where uid1=me()) or author_uid=me()) limit 0,500",
"query2" : "SELECT page_id, categories, name, website, location, checkins from page where page_id in (SELECT page_id from #query1)",
"query3" : "SELECT name, hometown_location from user where uid in (SELECT author_uid from #query1)",
}

ret = graph.fql(query)
print simplejson.dumps(ret, sort_keys=False, indent=2)

sys.exit(1)

total = 0
friends = graph.fql("SELECT uid2 FROM friend WHERE uid1=me()")

friends.append({'uid2':"me()"})
user_count = 0

while True:
#for friend in friends:
#    uid = friend['uid2']
    user_total = 0
    user_count = user_count + 1

    page = 0
    ts = int(time.time())
    nts = None
    while True:
        # Throws: urllib2.HTTPError: HTTP Error 500: Internal Server Error
        try:
#            query = "SELECT checkin_id, author_uid, app_id, timestamp, page_id, post_id, message, tagged_uids, coords FROM checkin WHERE author_uid=%s and timestamp < %d limit %d,500" % (str(uid),ts, 500*page)
            query = "SELECT id, author_uid, app_id, timestamp, page_id, page_type, coords, type FROM location_post WHERE (author_uid IN (SELECT uid2 FROM friend WHERE uid1=me()) or author_uid=me()) and timestamp < %d and type != \"photo\" limit %d,500" % (ts, 500*page)
            print "%s : results so far %d" % (query, total)
            ret = graph.fql(query)
        except Exception as detail:
            print query
            print "Unexpected error:", detail
            time.sleep(2)   
            break
        page = page + 1
        
        for item in ret:
            if nts == None:
                nts = item['timestamp']
            else:
                nts = min(nts,item['timestamp'])
#            print "%s : %s %s : %s" % (time.ctime(item['timestamp']), item['tagged_uids'], item['coords'], item['message'])
        
        total = total + len(ret)
        user_total = user_total + len(ret)

        if len(ret) == 0:
            break
        elif len(ret) < 500:
            ts = nts
            page = 0
            continue
    break
#    print "%s has %s checkins, running total %d (%d users left)" % (uid, user_total, total, len(friends)-user_count)            


print "Total items: %s minimum timestamp is %s" % (total, ts)       
        

        
        
