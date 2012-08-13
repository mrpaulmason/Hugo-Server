#!/usr/bin/python
import getopt, sys, os
import boto
import boto.ec2

env = "local"
server = "webserver"
action = "update"

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

    def disable(self):
        self.HEADER = ''
        self.OKBLUE = ''
        self.OKGREEN = ''
        self.WARNING = ''
        self.FAIL = ''
        self.ENDC = ''

def usage():
    print "hugo-admin.py [--env=local|staging|production] [--server=webserver] [--action=update|restart|stop]"

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


if __name__ == "__main__":
    main()
    print bcolors.OKBLUE + "Running a '%s' on '%s' for '%s' environment." % (action, server, env) + bcolors.ENDC
    if action == "restart" and server == "webserver":
        f = open('webserver/webserver-init.sh', 'r')
        uswest = boto.ec2.get_region("us-west-1")
        conn = uswest.connect()
        user_script = f.read()
        user_script = user_script.replace("!HUGO_SERVER!", server.lower())
        user_script = user_script.replace("!HUGO_ENV!", env.lower())
        reservation = conn.run_instances("ami-db86a39e", key_name="hugo", instance_type="t1.micro", security_groups=["webserver"], user_data =user_script)
    
    
    