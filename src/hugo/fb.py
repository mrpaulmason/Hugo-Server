#!/usr/bin/python 
import cloud
import facebook
import time
import simplejson
import sys
import MySQLdb
import os
import code
import boto
import boto.dynamodb
import datetime
import cloud

oauth_access_token="BAAGqkpC1J78BAF3RnWBOr30iU7yRT7s1byWZCE8VYfwuYSZB5IL0rcFzlEPQ5U4gcNYn3kZAp8kOBwyHBIvBue64eWsui5Eg7yzojWw2pvc9ZBR1vCmX"

def query_checkins(oauth_access_token, timestamp, delta):
    page = 0
    num_results = 500
    graph = facebook.GraphAPI(oauth_access_token)
    

    #print simplejson.dumps(json, sort_keys = False, indent=2)
#    dbconn = boto.dynamodb.connect_to_region('us-west-1', aws_access_key_id='AKIAJG4PP3FPHEQC76HQ',
#            aws_secret_access_key='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')
    
    query = {
    "query1" : "SELECT id, author_uid, app_id, timestamp, page_id, page_type, coords, type, tagged_uids  FROM location_post WHERE (author_uid IN (SELECT uid2 from friend where uid1=me()) or author_uid=me()) and timestamp < "+str(timestamp)+" and timestamp > "+str(timestamp-delta)+" limit "+str(page*num_results)+","+str(num_results),
    "query2" : "SELECT page_id, categories, name, website, location, checkins from page where page_id in (SELECT page_id from #query1)",
    "query3" : "SELECT uid, name from user where uid in (SELECT author_uid from #query1)",
    }
    
    print(datetime.datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S'))
    print query

    ret = graph.fql(query)
    
    query1 = ret[0]['fql_result_set']
    query2 = ret[1]['fql_result_set']
    query3 = ret[2]['fql_result_set']
    
    for i in range(0,len(query1)):
        for j in range(0,len(query2)):
            if query2[j]['page_id'] == query1[i]['page_id']:
                for key in query2[j]:
                    query1[i]['spot_'+key] = query2[j][key]
        for j in range(0,len(query3)):
            if query3[j]['uid'] == query1[i]['author_uid']:
                for key in query3[j]:
                    query1[i]['person_'+key] = query3[j][key]
    return query1


# 7038 checkins with 31 days
# 7355 checkins with 3 weeks

if __name__ == "__main__":    
    results = []    
    ts = int(time.time())
    tmp_ts = ts
    pg = 0
    delta = 3600*24*21
    numMonths = 34    

    oauth_tokens = []
    times = []
    deltas = []
 
#    tmp_results = query_checkins(oauth_access_token, pg, 500, tmp_ts, delta)    

    while numMonths > 0:        
        oauth_tokens.append(oauth_access_token)
        times.append(tmp_ts)
        deltas.append(delta)
        tmp_ts = tmp_ts - delta         
        numMonths = numMonths -1

    jids = cloud.map(query_checkins, oauth_tokens, times, deltas)
    
    for ret in cloud.iresult(jids):
        print len(ret)
        results.extend(ret)
        
    print len(results), (time.time()-ts)
#    print simplejson.dumps(results, sort_keys = False, indent = 4)
    

"""

graph = facebook.GraphAPI(oauth_access_token)

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
"""        

        
        
