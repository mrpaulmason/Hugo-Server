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

        # To Handle Bad Requests from DynamoDB, watch for infinite loops
        try:
            result = batch_list.submit()
        except:
            put_items(dbconn, table, puts[i:i+25])
            continue

        if table.name in result['UnprocessedItems']:
          unprocessed_items.extend(result['UnprocessedItems'][table.name])

      puts = []
      for unprocessed_item in unprocessed_items:
        attrs = unprocessed_item['PutRequest']['Item']
        puts.append(table.new_item(attrs=attrs))

def updateNewsfeed(hugo_id, dbconn, origin, data):
    table = dbconn.get_table("newsfeed_data")

    lst = dbconn.new_batch_write_list()

    timestampList = {}
    authorList = {}

    items = []

    for item in data:

        # Ignore the item if it has no coordinates
        try:
            if origin != None:
                gtarget = geohash.encode(item['coords']['latitude'], item['coords']['longitude'], precision=4)
                gh = geohash.encode(origin['latitude'], origin['longitude'], precision=4)
            
                isLocal = False
            
                for neighbor in geohash.expand(gh):
                    if neighbor == gtarget:
                        isLocal = True
            
                if not isLocal:
                    continue
            
            # Remove duplicates, helps w/ batch photo uploads.
            if item['timestamp'] in timestampList:
                print "Duplicate: ", item, item['timestamp']
                continue

            if (item['author_uid'],item['spot_name']) in authorList:
                print "ADuplicate: ", item, item['timestamp']
                continue
            
            item_attr = {
                        'bundle_id': "newsfeed_%d" % (hugo_id),
                        'geohash': geohash.encode(item['coords']['latitude'], item['coords']['longitude'], precision=13) + "_" + str(item['id']),
                        'geohash_raw' : geohash.encode(item['coords']['latitude'], item['coords']['longitude'], precision=13),
                        'spot_checkins' : item['spot_checkins'],
                        'me_uid' : item['me_uid'],
                        'author_uid' : item['author_uid'],
                        'fb_place_id' : item['spot_page_id'],
                        'author_name' : item['person_name'],
                        'author_image' : item['person_pic_square'],
                        'bundle_timestamp' : "%s" % (item['timestamp']),
                        'timestamp' : item['timestamp'],
                        'type' : item['type'],
                        'id' : item['id'],
                        'source' : 'facebook',
                        'spot_name' : item['spot_name'],
                        'tagged_uids' : simplejson.dumps(item['tagged_uids']),
                        'spot_categories' : simplejson.dumps(item['spot_categories']),
                        'spot_location' : simplejson.dumps(item['spot_location']),
                        'spot_hours' : simplejson.dumps(item['spot_hours']),
                        'spot_phone' : simplejson.dumps(item['spot_phone']),
                        'spot_website' : simplejson.dumps(item['spot_website'])
            }

            # Convert bad photo checkins to regular checkins
            try:
                if item_attr['type'] == 'photo':
                    item_attr.update({
                        'photo_width': item['photo_src_big_width'],
                        'photo_height' : item['photo_src_big_height'],
                        'photo_src' : item['photo_src_big']
                        })

                if item_attr['type'] == 'checkin':
                    item_attr.update({
                        'type' : 'spotting',
                        'spot_message': simplejson.dumps(item['checkin_message'])
                    })

                if item_attr['type'] == 'status':
                    item_attr.update({
                        'type' : 'spotting',
                        'spot_message': simplejson.dumps(item['status_message'])
                    })

            except:
                item_attr.update({
                    'type' : 'spotting',
                    'spot_message': simplejson.dumps("")
                })


        except:            
            print "updateNewsfeed", sys.exc_info()
            print item
            continue

        timestampList[item_attr['timestamp']] = item_attr
        authorList[(item['author_uid'],item['spot_name'])] = item_attr

        dItem = table.new_item(attrs=item_attr)
        items.append(dItem)
        
        if item_attr['me_uid'] == item_attr['author_uid']:
            item_attr['bundle_id'] = "user_%d" % (hugo_id)
            dItem = table.new_item(attrs=item_attr)
            items.append(dItem)        

    put_items(dbconn, table, items)        


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
                        'me_uid' : item['me_uid'],
                        'author_uid' : item['author_uid'],
                        'author_name' : item['person_name'],
                        'author_image' : item['person_pic_square'],
                        'fb_place_id' : item['spot_page_id'],
                        'timestamp' : item['timestamp'],
                        'type' : item['type'],
                        'id' : item['id'],
                        'source' : 'facebook',
                        'spot_name' : item['spot_name'],
                        'tagged_uids' : simplejson.dumps(item['tagged_uids']),
                        'spot_categories' : simplejson.dumps(item['spot_categories']),
                        'spot_location' : simplejson.dumps(item['spot_location']),
                        'spot_hours' : simplejson.dumps(item['spot_hours']),
                        'spot_phone' : simplejson.dumps(item['spot_phone']),
                        'spot_website' : simplejson.dumps(item['spot_website'])
            }
            


            # Convert bad photo checkins to regular checkins
            try:
                if item_attr['type'] == 'photo':
                    item_attr.update({
                        'photo_width': item['photo_src_big_width'],
                        'photo_height' : item['photo_src_big_height'],
                        'photo_src' : item['photo_src_big']
                        })
                if item_attr['type'] == 'checkin':
                    item_attr.update({
                        'type' : 'spotting',
                        'spot_message': simplejson.dumps(item['checkin_message'])
                    })

                if item_attr['type'] == 'status':
                    item_attr.update({
                        'type' : 'spotting',
                        'spot_message': simplejson.dumps(item['status_message'])
                    })

            except:
                item_attr.update({
                    'type' : 'spotting',
                    'spot_message': simplejson.dumps("")
                })

            
        except:            
            print "updateCheckins",sys.exc_info()
            print item
            continue

        dItem = table.new_item(attrs=item_attr)
        items.append(dItem)
                                
    put_items(dbconn, table, items)        
    
            
def query_checkins(hugo_id, oauth_access_token, origin, timestamp, delta):
    page = 0
    num_results = 500
    graph = facebook.GraphAPI(oauth_access_token, timeout=60)
    

    #print simplejson.dumps(json, sort_keys = False, indent=2)
    #select latitude, longitude, name from place where page_id='114952118516947' to get current location latitude, longitude
    
    query = {
    "query1" : "SELECT id, author_uid, app_id, timestamp, page_id, page_type, coords, type, tagged_uids  FROM location_post WHERE (author_uid=me() OR (author_uid IN (SELECT uid2 from friend where uid1=me()))) and timestamp < "+str(timestamp)+" and timestamp > "+str(timestamp-delta)+" limit "+str(page*num_results)+","+str(num_results),
    "query2" : "SELECT page_id, categories, name, website, location, checkins, phone, hours, price_range, pic, parking, fan_count from page where page_id in (SELECT page_id from #query1)",
    "query3" : "SELECT uid, name, pic_square, sex, relationship_status, significant_other_id, activities, interests, is_app_user, friend_count, mutual_friend_count, current_location, hometown_location, devices from user where uid in (SELECT author_uid from #query1)",
    "query4" : "SELECT object_id, src_big, src_big_width, src_big_height from photo where object_id in (SELECT id from #query1)",
    "query5" : "SELECT status_id, message from status where status_id in (SELECT id from #query1)",
    "query6" : "SELECT checkin_id, message from checkin where checkin_id in (SELECT id from #query1)"
    }
    
    retries = 5
    
    while retries > 0:
        try:
            ret = graph.fql(query)
            me_uid = graph.get_object('me', fields="id")['id']
        except:
            print "Error querying FB %d" % (retries)
            print sys.exc_info()
            time.sleep(10)
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
        query1[i]['me_uid'] = int(me_uid)
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

    table = dbconn.get_table("fb_hugo")
                
    for i in range(0,len(query1)):
        try:    
            item = table.get_item("%s" % str(query1[i]['author_id']))
            query1[i]['author_hugo_id'] = item['hugo_id']
        except:
            print sys.exc_info()
            pass
    
    updateCheckins(hugo_id, dbconn, query1)                
    updateNewsfeed(hugo_id, dbconn, origin, query1)                
    
    return None

def processCheckins(hugo_id, oauth_access_token, location_data=None):
    cloud.setkey( api_key="4667", api_secretkey="31a2945a0c955406be6d669f98e17ed9e9ee3ed7")

    tmp_ts = int(time.mktime(time.gmtime()))
    # 2 years
    delta = 3600*24*7
    numPeriods = 104

    hugo_ids = []
    oauth_tokens = []
    origins = []
    times = []
    deltas = []
    
    while numPeriods > 0:        
        hugo_ids.append(hugo_id)
        oauth_tokens.append(oauth_access_token)
        times.append(tmp_ts)
        deltas.append(delta)
        if location_data == None:
            origins.append(None)
        else:
            origins.append(location_data['location'])
        tmp_ts = tmp_ts - delta         
        numPeriods = numPeriods -1    

    retries = 3
    while retries > 0:
        try:
            jids = cloud.map(query_checkins, hugo_ids, oauth_tokens, origins, times, deltas, _env="hugo", _profile=True, type='s1')
            retries = 0
        except:
            time.sleep(5)
            retries = retries - 1
            continue

# 7038 checkins with 31 days
# 7355 checkins with 3 weeks

if __name__ == "__main__":    
    processCheckins(1, oauth_access_token, {"location": {"latitude": 37.7793, "longitude": -122.4192}, "id": "114952118516947"})
    processCheckins(2, "BAAGqkpC1J78BAEuprMC5ReD2uk8G4mvCzPtxjA7iRpi9nwLBgAkVH4fKOlbNyhs6QcZBLCtmbw5Hjlwy0jsDLkg2cSuDlnmbYIu4LdZAGuyyQAO17i",  {"location": {"latitude": 37.7793, "longitude": -122.4192}, "id": "114952118516947"})
    processCheckins(3, "BAAGqkpC1J78BAIBMZBDKZC8AMWozRa45evrZCDdFLCw0ZCXGWLMRmvihEGZBYmmdyygTIbZBkRkMdGv6GzWU1ZBZBXsRCj6dEZBQVoLS72nXfc7jeq4mKxGxNIK53fOj9Jb0ZD",  {"location": {"latitude": 37.7793, "longitude": -122.4192}, "id": "114952118516947"})
    
#    query_checkins(1, "BAAGqkpC1J78BAF3RnWBOr30iU7yRT7s1byWZCE8VYfwuYSZB5IL0rcFzlEPQ5U4gcNYn3kZAp8kOBwyHBIvBue64eWsui5Eg7yzojWw2pvc9ZBR1vCmX",{"latitude": 37.7793, "longitude": -122.4192}, int(time.time()), 3600*24*7)        


        
        
