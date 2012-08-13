#!/usr/bin/python
import getopt, sys, os
import boto
import boto.ec2
import subprocess
import time

env = "staging"
server = "webserver"
action = "update"

ip_mapping = {'webserver' : {'local':"50.18.125.100", "staging":"50.18.125.158", "production":"50.18.125.159"}}

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

def check_output(command):
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    output = process.communicate()
    retcode = process.poll()
    if retcode:
        raise subprocess.CalledProcessError(retcode, command, output=output[0])
    return output

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
    if action == "update" and server == "webserver":
        start = time.time()
        uswest = boto.ec2.get_region("us-west-1")
        conn = uswest.connect()
        reservations = conn.get_all_instances()
        instances = [i for r in reservations for i in r.instances]
        instances = [i for i in instances if i.state=="running"]
        for i in instances:
            if i.tags['Environment'] == env and i.tags['Server'] == server and i.tags['Busy'] == "no":
                try:
                    print "Running %s" % ("ssh -o StrictHostKeyChecking=no ubuntu@%s sudo /var/hugo/sysadmin/%s/%s-update.sh" % (i.public_dns_name, server, server))
                    output = check_output("ssh -o StrictHostKeyChecking=no ubuntu@%s sudo /var/hugo/sysadmin/%s/%s-update.sh" % (i.public_dns_name, server, server))
                    print output
                except:
                    print "Failed updating server %s" % i.public_dns_name
        print bcolors.OKBLUE + "Update completed for '%s' on '%s' for '%s' environment (%f s)." % (action, server, env, time.time()-start) + bcolors.ENDC
    elif action == "stop" and server == "webserver":
        uswest = boto.ec2.get_region("us-west-1")
        conn = uswest.connect()
        reservations = conn.get_all_instances()
        instances = [i for r in reservations for i in r.instances]
        instances = [i for i in instances if i.state=="running"]
        for i in instances:
            if i.tags['Environment'] == env and i.tags['Server'] == server and i.tags['Busy'] == "no":
                print bcolors.FAIL + "Terminating machine '%s' for '%s' on '%s' for '%s' environment." % (i.public_dns_name, action, server, env) + bcolors.ENDC                
                i.terminate()
        print bcolors.OKBLUE + "Machines terminated for '%s' on '%s' for '%s' environment." % (action, server, env) + bcolors.ENDC    
    elif action == "restart" and server == "webserver":
        start = time.time()
        f = open('webserver/webserver-init.sh', 'r')
        uswest = boto.ec2.get_region("us-west-1")
        conn = uswest.connect()
        reservations = conn.get_all_instances()
        instances = [i for r in reservations for i in r.instances]
        instances = [i for i in instances if i.state=="running"]
        terminatedNodes = False
        for i in instances:
            if i.tags['Environment'] == env and i.tags['Server'] == server and i.tags['Busy'] == "no":
                print bcolors.FAIL + "Terminating machine '%s' for '%s' on '%s' for '%s' environment." % (i.public_dns_name, action, server, env) + bcolors.ENDC                
                i.terminate()
                terminatedNodes = True
        if terminatedNodes:
            print bcolors.OKBLUE + "Machines terminated for '%s' on '%s' for '%s' environment." % (action, server, env) + bcolors.ENDC    

        user_script = f.read()
        user_script = user_script.replace("!HUGO_SERVER!", server.lower())
        user_script = user_script.replace("!HUGO_ENV!", env.lower())
        reservation = conn.run_instances("ami-db86a39e", key_name="hugo", instance_type="t1.micro", security_groups=["webserver"], user_data =user_script)
        instance = reservation.instances[0]
        status = instance.update()
        while status == 'pending':
            time.sleep(1)
            status = instance.update()
            
        if status == 'running':
            instance.add_tag("Name","%s - %s" % (server.title(), env.title()))
            instance.add_tag("Server","%s" % server)
            instance.add_tag("Environment","%s" % env)
            instance.add_tag("Busy","yes")
        else:
            print('Instance status: ' + status)
            sys.exit(1)
            
        print "Server is up and running at %s" % (instance.public_dns_name)
        
        if status == "running":
            retry = True
            while retry:
                try:
                    output = check_output("ssh -o StrictHostKeyChecking=no ubuntu@%s cat /etc/webserver-init.touchdown|grep FINISHED" % (instance.public_dns_name))
                    retry = False
                except:
                    time.sleep(10)
                    
        if output[0].find("FINISHED") == 0:
            instance.add_tag("Busy", "no")
            addresses = [x for x in conn.get_all_addresses() if x.public_ip == ip_mapping[server][env]]
            try:
                addresses[0].associate(instance.id)                
                print bcolors.OKBLUE + "Successfully ran a '%s' on '%s' for '%s' environment (%f s) with IP %s." % (action, server, env, time.time()-start, ip_mapping[server][env]) + bcolors.ENDC                
            except:
                print bcolors.FAIL + "FAILED associating IP address with '%s' on '%s' for '%s' environment (%f s)." % (action, server, env, time.time()-start) + bcolors.ENDC
                instance.terminate()
            
        else:
            print bcolors.FAIL + "FAILED running a '%s' on '%s' for '%s' environment (%f s)." % (action, server, env, time.time()-start) + bcolors.ENDC
            instance.terminate()
            
        