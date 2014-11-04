#!/usr/bin/env python

import subprocess
import sys
import getopt


mmdiag='/usr/lpp/mmfs/bin/mmdiag'
mmlscluster='/usr/lpp/mmfs/bin/mmlscluster'

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

def run(c):
    '''
    Helper function to execute shell commands and return stdout.
    '''
    p = subprocess.Popen(c, shell=True, stdout=subprocess.PIPE)
    return p.stdout.next().rstrip()

def check(left,right):
    '''
    Check is the contition that IBM recommend for token manager tuning coniditions:
    # nodes (local and remote) * (MFTC + MSC) < (#manager nodes -1) * 1.2M * (512M/TML)
    '''
    ratio = round((left/right),2)
    if ratio < 1:
        sys.stdout.write(bcolors.OKGREEN)
        state = "OK"
    else:
        sys.stdout.write(bcolors.FAIL)
        state = "FAIL"
    print "%s (%s)%s" % (ratio,state,bcolors.ENDC)
    return left < right

def usage():
    print "USAGE: %s [-n <n>] [-f <n>] [-s <n>] [-m <n>] [-t <n>] [-l <n>]" % sys.argv[0]
    print "\t-n Override number of nodes (global and local)"
    print "\t-f Override maxFilesToCache"
    print "\t-s Override maxStateCache"
    print "\t-m Override number of manager nodes"
    print "\t-t Override tokemMemLimit"
    print "\t-l Override number of local nodes"

try:
    opts, args = getopt.getopt(sys.argv[1:], "n:f:s:m:t:l:", ["help", "output="])
except getopt.GetoptError, err:
    # print help information and exit:
    print str(err) # will print something like "option -a not recognized"
    usage()
    sys.exit(2)

# Grab parameters
num_nodes=int(run("%s --network | grep '<c0' | wc -l" % (mmdiag)))
mftc=int(run("%s --config | grep maxFilesToCache | awk {'print $3'}" % (mmdiag)))
msc=int(run("%s --config | grep maxStatCache | awk {'print $3'}" % (mmdiag)))
manager_nodes=int(run("%s| grep manager | wc -l" % (mmlscluster)))
tml=int(run("%s --config | grep tokenMemLimit | awk {'print $2'}" % (mmdiag)))
local_nodes=int(run("%s| grep '^   [0-9]' | wc -l" % (mmlscluster)))

# Set any overrides
for o, a in opts:
    if o == "-n":
        num_nodes = int(a)
    elif o == "-f":
        mftc = int(a)
    elif o == "-s":
        msc = int(a)
    elif o == "-m":
        manager_nodes = int(a)
    elif o == "-t":
        tml = int(a)
    elif o == "-l":
        local_nodes = int(a)


# Print parameters to user
print "%s %s" % ("#nodes (local and remote):".rjust(30,' '),num_nodes)
print "%s %s" % ("maxFilesToCache:".rjust(30,' '),mftc)
print "%s %s" % ("maxStatCache:".rjust(30,' '),msc)
print "%s %s" % ("#manager nodes:".rjust(30,' '),manager_nodes)
print "%s %s" % ("tokenMemLimit:".rjust(30,' '),tml)
print ""
print "Checking nodes (local and remote) * (MFTC + MSC) < (#manager nodes -1) * 1.2M * (512M/TML)..."
print ""


# Calculate condition for n to n/2+1 local nodes being active in the cluster.
for i in range(0,(local_nodes/2)+1):
    left = (num_nodes-i) * (mftc + msc)
    right = ( manager_nodes -1-i ) * 1200000 * ( 512000000 / float(tml) )
    sys.stdout.write("%s/%s nodes: " % (local_nodes-i,local_nodes))
    check(left,right)
