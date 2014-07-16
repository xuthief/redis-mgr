#!/usr/bin/env python
#coding: utf-8
#file   : gen_conf.py
#author : ning
#date   : 2013-12-20 09:36:42

import urllib, urllib2
import os, sys
import re, time
import logging
from pcl import common

from string import Template as T
T.s = T.substitute

USER = 'ning'

cluster_id = 0
CLUSTER_NAME = 'cluster0'
BASEDIR = '/home/ning/redis-cluster0'

MASTER_PER_MACHINE = 2
HOSTS = [
    '127.0.0.5',
    '127.0.0.5',
]

if not CLUSTER_NAME.endswith(str(cluster_id)):
    print 'bad clusterid'
    exit(1)

def gen_sentinel(port):
    ret = ''
    t_host = HOSTS[:3]
    if len(t_host) < 3:  # host not enough
        t_host = (t_host * 3) [:3]
    for m in t_host:
        templete = ' '*8 + "('$m:$port', '$BASEDIR/sentinel-$port'),\n"
        ret += T(templete).s(dict(globals(), **locals()))
        port += 1
    return ret

def gen_redis(port):
    ret = ''
    for i in range(len(HOSTS)):
        for j in range(MASTER_PER_MACHINE):
            slave_port = port + 1000

            m = HOSTS[i]
            s = HOSTS[(i+1)%len(HOSTS)]
            master_name = '%s-%s' % (CLUSTER_NAME, port)
            templete = ' '*8 + "'$master_name:$m:$port:$BASEDIR/redis-$port', '$master_name:$s:$slave_port:$BASEDIR/redis-$slave_port',\n"
            ret += T(templete).s(dict(globals(), **locals()))
            port += 1
    return ret

def gen_nutcracker(port):
    ret = ''
    for i in range(len(HOSTS)):
        m = HOSTS[i]
        for j in range(MASTER_PER_MACHINE):
            xport = port + j
            templete = ' '*8 + "('$m:$xport', '$BASEDIR/nutcracker-$xport'),\n"
            ret += T(templete).s(dict(globals(), **locals()))
    return ret

def gen_cluster():
    templete = '''
$CLUSTER_NAME = {
    'cluster_name': '$CLUSTER_NAME',
    'user': '$USER',
    'sentinel':[
$sentinel_section
    ],
    'redis': [
$redis_section
    ],
    'nutcracker': [
$nutcracker_section
    ],
}
    '''

    redis_section      = gen_redis(2000+cluster_id*100)
    nutcracker_section = gen_nutcracker(4000+cluster_id*100)
    sentinel_section   = gen_sentinel(9000+cluster_id*100)

    print T(templete).s(dict(globals(), **locals()))

gen_cluster()
