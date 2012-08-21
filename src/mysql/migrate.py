#!/usr/bin/python
import getopt, sys, os
import boto, boto.rds
from subprocess import Popen, PIPE
import MySQLdb
import code, curl, simplejson


env = "staging"

def authorizeLocalComputer():
    rds_conn = boto.rds.connect_to_region('us-west-1')
    dbList = [x for x in rds_conn.get_all_dbinstances() if x.id=="hugo"]

    if len(dbList) == 0:
        print "Error: database is not running"
        sys.exit(2)


    db = dbList[0]    

    json_data = curl.Curl("jsonip.com").get()
    ip = simplejson.loads(json_data)['ip']

    try:
        db.security_group.authorize(ip+"/32")
        print "Authorizing, waiting for authorization to complete."
        sleep(30)
    except:
        print "Already authorized!"
    
    return db.endpoint

def performMigration(v):
    global env
    dbhost, dbport = authorizeLocalComputer()
    print "Performing migration on %s with %d (%s, %d)" % (env, v, dbhost, dbport)
    conn = MySQLdb.connect (host=dbhost, user="hugo", passwd="Huego415",port=dbport)
    cur = conn.cursor()
    
    # Database doesn't exist
    if cur.execute("SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = 'hugo_%s'" % (env.lower())) == 0:
        if v == 0:
            print "Running initial migration..."
            try:
                cur.execute("CREATE DATABASE hugo_%s" % (env.lower()))
                files = os.listdir(str(v))            
                for file in files:
                    process = Popen('mysql %s -h%s -P%d -u%s -p%s' % ("hugo_%s" % (env.lower()), dbhost, dbport, "hugo", "Huego415"),
                                    stdout=PIPE, stdin=PIPE, shell=True)
                    output = process.communicate('source ' + "%d/%s" % (v, file))[0]
                    print output
                print "Executing: %s" % ("INSERT INTO hugo_%s.version_info (version) VALUES(0)" % (env.lower()))
                cur.execute("INSERT INTO hugo_%s.version_info (version) VALUES(0)" % (env.lower()))
                conn.commit()
            except:
                cur.execute("DROP DATABASE hugo_%s" % (env.lower()))
                print "Error running migration"
                sys.exit(2)
            print "Migration complete!"
        else:
            print "Error: please run initial migration since the database doesn't exist"
            sys.exit(2)            
    elif cur.execute("SELECT max(version) from hugo_%s.version_info" % (env.lower())) == 1:
        lastVersion = cur.fetchone()[0]
        if lastVersion == v:
            print "Error: database is already up to date!"
        elif lastVersion != v-1:
            print "Error: please run migrations in order, the current database version is %d" % lastVersion
            sys.exit(2)
        else:
            print "Running upgrade to %d." % v
            try:
                cur.execute("CREATE DATABASE hugo_%s_tmp" % (env.lower()))
                
                cur.execute("SHOW TABLES FROM hugo_%s" % (env.lower()))
                
                results = cur.fetchall()
                for item in results:
                    cur.execute("CREATE TABLE hugo_%s_tmp.%s like hugo_%s.%s" % (env.lower(), item[0], env.lower(), item[0]))
                    cur.execute("INSERT INTO hugo_%s_tmp.%s SELECT * FROM hugo_%s.%s" % (env.lower(), item[0], env.lower(), item[0]))                                
                    
                conn.commit()
                
                
                files = os.listdir(str(v))            
                for file in files:
                    process = Popen('mysql %s -h%s -P%d -u%s -p%s' % ("hugo_%s_tmp" % (env.lower()), dbhost, dbport, "hugo", "Huego415"),
                                    stdout=PIPE, stdin=PIPE, shell=True)
                    output = process.communicate('source ' + "%d/%s" % (v, file))[0]
                    print output
                print "Executing: %s" % ("INSERT INTO hugo_%s_tmp.version_info (version) VALUES(0)" % (env.lower()))
                cur.execute("INSERT INTO hugo_%s_tmp.version_info (version) VALUES(0)" % (env.lower()))
                conn.commit()
                
                # If we made it this far without an error, we can run the commands on our primary database
                print "Migration complete on backup database, running migration on real database"
                files = os.listdir(str(v))            
                for file in files:
                    process = Popen('mysql %s -h%s -P%d -u%s -p%s' % ("hugo_%s" % (env.lower()), dbhost, dbport, "hugo", "Huego415"),
                                    stdout=PIPE, stdin=PIPE, shell=True)
                    output = process.communicate('source ' + "%d/%s" % (v, file))[0]
                    print output
                print "Executing: %s" % ("INSERT INTO hugo_%s.version_info (version) VALUES(0)" % (env.lower()))
                cur.execute("INSERT INTO hugo_%s.version_info (version) VALUES(%d)" % (env.lower(), v))
                conn.commit()

                print "Cleaning up!"
                cur.execute("DROP DATABASE hugo_%s_tmp" % (env.lower()))                
                
            except:
                cur.execute("DROP DATABASE hugo_%s_tmp" % (env.lower()))
                print "Error running migration"
                sys.exit(2)
            print "Migration complete!"
                
    

def usage():
    print "migrate.py [--env=local|staging|production] version_number"

def main():
    global env, server, action
    try:
        opts, args = getopt.getopt(sys.argv[1:], "e:s:a:", ["env=", "server=", "action="])
    except getopt.GetoptError, err:
        print str(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)
    output = None
    verbose = False
    for o, a in opts:
        if o in ("-e", "--env"):
            if a not in ("local", "staging", "production"):
                usage()
                sys.exit(2)    
            env = a    
        elif o in ("-s", "--server"):
            if a not in ("webserver"):
                usage()
                sys.exit(2)        
            server = a
        elif o in ("-a", "--action"):
            if a not in ("update", "restart", "stop"):
                usage()
                sys.exit(2)        
            action = a
        else:
            assert False, "unhandled option"

    if len(args) != 1:
        usage()
        sys.exit(2)
        
    try:
        version_number = int(args[0])
    except:
        usage()
        sys.exit(2)
    
    performMigration(version_number)


if __name__ == "__main__":
    main()