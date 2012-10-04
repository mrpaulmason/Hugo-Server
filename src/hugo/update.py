import MySQLdb, os, sys, simplejson
import fb
import cloud
import urllib2
import boto
import boto.rds
from time import sleep

def updateDatabase():
    rds_conn = boto.rds.connect_to_region('us-west-1', aws_access_key_id='AKIAJG4PP3FPHEQC76HQ',
                            aws_secret_access_key='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')
    dbList = [x for x in rds_conn.get_all_dbinstances() if x.id=="hugo"]

    if len(dbList) == 0:
        print "Error: database is not running"
        sys.exit(2)

    db = dbList[0]    

    json_data = urllib2.urlopen('http://jsonip.com').read()
    ip = simplejson.loads(json_data)['ip']

    try:
        db.security_group.authorize(ip+"/32")
        print "Authorizing, waiting for authorization to complete."
        sleep(30)
    except:
        print sys.exc_info()
        print "Already authorized!"
    
    sleep(30)
    conn = MySQLdb.connect (host="hugo.caqu3caxjsdg.us-west-1.rds.amazonaws.com", user="hugo", passwd="Huego415",port=3306, db="hugo_staging")
    cur = conn.cursor()
    
    try:
        query = "SELECT name, user_id, facebook_auth_key, current_location from hugo_staging.users"
        cur.execute(query)
        while 1:
           row = cur.fetchone()
           
           if row:           
              fb.processCheckins(row[1], row[2], simplejson.loads(row[3]), incremental=True)
           else:
              break
    except:
        print sys.exc_info()
        pass

if __name__ == "__main__":    
    cloud.cron.register(updateDatabase, "updateDatabase", "0 * * * *", _env="hugo", _profile=True, type='s1')

