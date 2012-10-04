import MySQLdb, os, sys, simplejson
import fb
import cloud


def updateDatabase():
    print "hi"
    return
    conn = MySQLdb.connect (host="hugo.caqu3caxjsdg.us-west-1.rds.amazonaws.com", user="hugo", passwd="Huego415",port=3306, db=("hugo_%s"%os.environ['HUGO_ENV'].lower()))
    cur = conn.cursor()
    
    try:
        query = ("SELECT name, user_id, facebook_auth_key, current_location from hugo_%s.users" % os.environ['HUGO_ENV'].lower())
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
   cloud.cron.register(updateDatabase, "updateDatabase", "0 * * * *")

