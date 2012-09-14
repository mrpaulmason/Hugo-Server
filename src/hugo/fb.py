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
import geohash
from boto.dynamodb.condition import *


oauth_access_token="BAAGqkpC1J78BAF3RnWBOr30iU7yRT7s1byWZCE8VYfwuYSZB5IL0rcFzlEPQ5U4gcNYn3kZAp8kOBwyHBIvBue64eWsui5Eg7yzojWw2pvc9ZBR1vCmX"
MAX_BATCH_REQUEST=25

def put_items(dbconn, table, puts):
    while(len(puts) > 0):
      unprocessed_items = []
      for i in xrange(0, len(puts), 25):
        batch_list = dbconn.new_batch_write_list()
        batch_list.add_batch(table, puts=puts[i:i+25])
        result = batch_list.submit()
        if table.name in result['UnprocessedItems']:
          unprocessed_items.extend(result['UnprocessedItems'][table.name])

      puts = []
      for unprocessed_item in unprocessed_items:
        attrs = unprocessed_item['PutRequest']['Item']
        puts.append(table.new_item(attrs=attrs))

def updateCheckins(hugo_id, dbconn, data):
    table = dbconn.get_table("checkin_data")
    
    lst = dbconn.new_batch_write_list()
    
    items = []

    for item in data:
        
        # Ignore the item if it has no coordinates
        try:
            item_attr = {
                        'user_id': hugo_id,
                        'geohash': geohash.encode(item['coords']['latitude'], item['coords']['longitude'], precision=13) + "_" + str(item['id']),
                        'geohash_raw' : geohash.encode(item['coords']['latitude'], item['coords']['longitude'], precision=13),
                        'spot_checkins' : item['spot_checkins'],
                        'author_uid' : item['author_uid'],
                        'author_name' : item['person_name'],
                        'author_image' : item['person_pic_square'],
                        'timestamp' : item['timestamp'],
                        'tagged_uids' : simplejson.dumps(item['tagged_uids']),
                        'spot_categories' : simplejson.dumps(item['spot_categories']),
                        'spot_location' : simplejson.dumps(item['spot_location']),
                        'spot_hours' : simplejson.dumps(item['spot_hours']),
                        'spot_name' : simplejson.dumps(item['spot_name']),
                        'spot_phone' : simplejson.dumps(item['spot_phone']),
                        'spot_website' : simplejson.dumps(item['spot_website']),
                        'spot_type' : simplejson.dumps(item['type'])
            }
            
            if item_attr['spot_type'] == 'photo':
                item_attr.update({
                    'photo_width': item['photo_src_big_width'],
                    'photo_height' : item['photo_src_big_height'],
                    'photo_src' : item['photo_src_big']
                })

            if item_attr['spot_type'] == 'checkin':
                item_attr.update({
                    'spot_type' : 'spotting',
                    'spot_message': item['checkin_message']
                })

            if item_attr['spot_type'] == 'status':
                item_attr.update({
                    'spot_type' : 'spotting',
                    'spot_message': item['status_message']
                })

            
        except:
            print sys.exc_info()
            continue

        dItem = table.new_item(attrs=item_attr)
        items.append(dItem)
                                
    put_items(dbconn, table, items)        
    
            
def query_checkins(hugo_id, oauth_access_token, timestamp, delta):
    page = 0
    num_results = 500
    graph = facebook.GraphAPI(oauth_access_token)
    

    #print simplejson.dumps(json, sort_keys = False, indent=2)
    #select latitude, longitude, name from place where page_id='114952118516947' to get current location latitude, longitude
    
    query = {
    "query1" : "SELECT id, author_uid, app_id, timestamp, page_id, page_type, coords, type, tagged_uids  FROM location_post WHERE (author_uid IN (SELECT uid2 from friend where uid1=me()) or author_uid=me()) and timestamp < "+str(timestamp)+" and timestamp > "+str(timestamp-delta)+" limit "+str(page*num_results)+","+str(num_results),
    "query2" : "SELECT page_id, categories, name, website, location, checkins, phone, hours, price_range, pic, parking, fan_count from page where page_id in (SELECT page_id from #query1)",
    "query3" : "SELECT uid, name, pic_square, sex, relationship_status, significant_other_id, activities, interests, is_app_user, friend_count, mutual_friend_count, current_location, hometown_location, devices from user where uid in (SELECT author_uid from #query1)",
    "query4" : "SELECT object_id, src_big, src_big_width, src_big_height from photo where object_id in (SELECT id from #query1)",
    "query5" : "SELECT status_id, message from status where status_id in (SELECT id from #query1)",
    "query6" : "SELECT checkin_id, message from checkin where checkin_id in (SELECT id from #query1)",
    }
    
    retries = 3
    
    while retries > 0:
        try:
            ret = graph.fql(query)
        except:
            print "Error querying FB %d" % (retries)
            time.sleep(30)
            retries = retries - 1
            if retries == 0:
                return
            continue
        break
        
    query1 = ret[0]['fql_result_set']
    query2 = ret[1]['fql_result_set']
    query3 = ret[2]['fql_result_set']
    query4 = ret[3]['fql_result_set']
    query5 = ret[4]['fql_result_set']
    query6 = ret[5]['fql_result_set']
        
    for i in range(0,len(query1)):
        for j in range(0,len(query2)):
            if query2[j]['page_id'] == query1[i]['page_id']:
                for key in query2[j]:
                    query1[i]['spot_'+key] = query2[j][key]
        for j in range(0,len(query3)):
            if query3[j]['uid'] == query1[i]['author_uid']:
                for key in query3[j]:
                    query1[i]['person_'+key] = query3[j][key]
        for j in range(0,len(query4)):
            if query4[j]['object_id'] == query1[i]['id']:
                for key in query4[j]:
                    query1[i]['photo_'+key] = query4[j][key]
        for j in range(0,len(query5)):
            if query5[j]['status_id'] == query1[i]['id']:
                for key in query5[j]:
                    query1[i]['status_'+key] = query5[j][key]
        for j in range(0,len(query6)):
            if query6[j]['checkin_id'] == query1[i]['id']:
                for key in query6[j]:
                    query1[i]['checkin_'+key] = query6[j][key]



                                                        
    dbconn = boto.dynamodb.connect_to_region('us-west-1', aws_access_key_id='AKIAJG4PP3FPHEQC76HQ',
                            aws_secret_access_key='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')
    
    updateCheckins(hugo_id, dbconn, query1)                
    
    return None

def processCheckins(hugo_id, oauth_access_token):
    cloud.setkey( api_key="4667", api_secretkey="31a2945a0c955406be6d669f98e17ed9e9ee3ed7")

    tmp_ts = int(time.time())
    delta = 3600*24*21
    numMonths = 34

    hugo_ids = []
    oauth_tokens = []
    times = []
    deltas = []
    
    while numMonths > 0:        
        hugo_ids.append(hugo_id)
        oauth_tokens.append(oauth_access_token)
        times.append(tmp_ts)
        deltas.append(delta)
        tmp_ts = tmp_ts - delta         
        numMonths = numMonths -1    

    jids = cloud.map(query_checkins, hugo_ids, oauth_tokens, times, deltas, _env="hugo", _profile=True, type='s1')


# 7038 checkins with 31 days
# 7355 checkins with 3 weeks

if __name__ == "__main__":    
    processCheckins(1, oauth_access_token)
    processCheckins(2, "BAAGqkpC1J78BAEuprMC5ReD2uk8G4mvCzPtxjA7iRpi9nwLBgAkVH4fKOlbNyhs6QcZBLCtmbw5Hjlwy0jsDLkg2cSuDlnmbYIu4LdZAGuyyQAO17i")
    processCheckins(3, "BAAGqkpC1J78BAIBMZBDKZC8AMWozRa45evrZCDdFLCw0ZCXGWLMRmvihEGZBYmmdyygTIbZBkRkMdGv6GzWU1ZBZBXsRCj6dEZBQVoLS72nXfc7jeq4mKxGxNIK53fOj9Jb0ZD")
    
#    print simplejson.dumps(cloud.result(jids[0]), indent=4)
#    query_checkins(1, "BAAGqkpC1J78BAF3RnWBOr30iU7yRT7s1byWZCE8VYfwuYSZB5IL0rcFzlEPQ5U4gcNYn3kZAp8kOBwyHBIvBue64eWsui5Eg7yzojWw2pvc9ZBR1vCmX", int(time.time()), 3600*24*7)        
#    for ret in cloud.iresult(jids):
#        print len(ret)
#        results.extend(ret)
        
#    print results[0]
#    print len(results), (time.time()-ts)
#    print simplejson.dumps(results, sort_keys = False, indent = 4)
    

"""
import boto.dynamodb
import time, simplejson

from boto.dynamodb.condition import *

b = time.time()

dbconn = boto.dynamodb.connect_to_region('us-west-1', aws_access_key_id='AKIAJG4PP3FPHEQC76HQ',
                           aws_secret_access_key='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')
table = dbconn.get_table("checkin_data")

result = table.query(
  hash_key = 1) 
#  range_key_condition = BETWEEN("9q8yy", "9q8yy{"))

items = []  
  
for item in result:
    item.delete()


f = time.time()
print simplejson.dumps(items, indent=4)
print len(item), f-b



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

        
        
