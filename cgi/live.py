#!/usr/bin/env python
#coding: utf-8
#file   : live_overview.py
#author : ning
#date   : 2014-01-22 08:39:19

from cgicommon import *

def clean_line(line):
    return line.replace('\033[94m', '').replace('\033[0m', '')

#http://localhost:8000/cgi/live.py?conf=conf&cluster=cluster0&cmd=live_master_mem
@nothrow(IOError)
def main():
    print "HTTP/1.0 200 OK"
    print "Content-Type: application/x-javascript"
    print ""
    print 'SUPPORT CMD: live_master_qps/live_master_mem/live_overview/history n'

    args = {
        'workdir': WORKDIR,
        'conf': getQS('conf', 'conf'),
        'cluster': getQS('cluster', 'cluster0'),
        'cmd': getQS('cmd', 'live_master_qps'),
    }
    cmd = TT('cd $workdir && export REDIS_DEPLOY_CONFIG=$conf && ./bin/deploy.py $cluster $cmd', args)

    print cmd
    print ''

    from subprocess import Popen, PIPE
    p = Popen(cmd, shell=True, bufsize = 100, stdout=PIPE)

    sys.stdout.flush()
    while True:
        line = p.stdout.readline()
        if line != '':
            print clean_line(line),
            sys.stdout.flush()
        else:
            break

main()
