#!/usr/bin/env python
#coding: utf-8
#file   : example.py
#author : ning
#date   : 2014-01-22 08:39:19

from cgicommon import *
def main():
    print "HTTP/1.0 200 OK"
    print "Content-Type: html"
    print ""

    if not getQS('conf', '') or not getQS('cluster', ''):
        print '?conf=conf&cluster=cluster0'
        return

    live_desc = [
        ('live_master_qps', 'live_master_qps'),
        ('live_master_mem', 'live_master_mem'),
        ('live_overview', 'live_overview(every minute)'),
        ('history', 'history of live overview'),
    ]

    for key, desc in live_desc:
        args = {
            'conf': getQS('conf', 'conf'),
            'cluster': getQS('cluster', 'cluster0'),
            'key': key,
            'desc': desc,
        }
        print TT('<a href="/cgi/live.py?conf=$conf&cluster=$cluster&cmd=$key"> $desc </a><br/>', args)

main()
