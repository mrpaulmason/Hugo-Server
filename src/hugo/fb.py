#!/usr/bin/python 
import facebook
import time
import simplejson
import sys

oauth_access_token="AAACEdEose0cBAOaZB4tHziIycZB7p9tp7WT45eWMwlb9ZAKo9mYU6tZCZAwiD6QCzP14icR0t7MK6w5hWSkFIXFucxZBCXjfU0ni4CLjipWAZDZD"
graph = facebook.GraphAPI(oauth_access_token)
#json = graph.get_object("me/locations")

#print simplejson.dumps(json, sort_keys = False, indent=2)
#    ret = graph.fql("SELECT id, author_uid, app_id, timestamp, page_id, page_type, coords, type FROM location_post WHERE (author_uid IN (SELECT uid2 FROM friend WHERE uid1=me()) or author_uid=me()) and timestamp < %d limit %d,500" % (ts, 500*page))
#    ret = graph.fql("SELECT id, author_uid, app_id, timestamp, page_id, page_type, coords, type FROM location_post WHERE (author_uid=me()) and timestamp < %d limit %d,500" % (ts, 500*page))
#    ret = graph.fql("SELECT checkin_id, author_uid, app_id, timestamp, page_id, post_id, message, tagged_uids, coords FROM checkin WHERE (author_uid=me()) and timestamp < %d limit %d,500" % (ts, 500*page))

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
        

        
        
