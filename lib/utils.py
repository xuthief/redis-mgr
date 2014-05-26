import os
import re
import sys
import time
import copy
import thread
import socket
import threading
import logging
import inspect
import argparse
import telnetlib
import redis
import random
import redis
import json
import glob

from collections import defaultdict
from argparse import RawTextHelpFormatter

from pcl import common
from pcl import crontab
from string import Template

# we have to do this here, so that lib/monitor.py can use conf.xxx
# import config in conf/REDIS_DEPLOY_CONFIG.py
if 'REDIS_DEPLOY_CONFIG' not in os.environ:
    logging.error('please export REDIS_DEPLOY_CONFIG=conf && . ./bin/active')
    exit(1)
config_name = os.environ['REDIS_DEPLOY_CONFIG']
conf = __import__(config_name, globals(), locals(), [], 0)        #import config_module

common.system('mkdir -p data tmp', None)

def my_json_encode(j):
    return json.dumps(j, cls=common.MyEncoder)

def strstr(s1, s2):
    return s1.find(s2) != -1

def lets_sleep(SLEEP_TIME = 0.1):
    time.sleep(SLEEP_TIME)

def TT(template, args): #todo: modify all
    return Template(template).substitute(args)

def system_with_timeout(cmd, log_fun=logging.info, timeout=60*60*24*30):
    if log_fun: log_fun(cmd)
    from subprocess import Popen, PIPE
    import signal
    tstart = time.time()
    p = Popen(cmd, shell=True, bufsize = 102400, stdout=PIPE, stderr=PIPE)
    while p.poll() is None: #python2.7 Popen.wait() has no timeout
        time.sleep(time.time() - tstart)
        if time.time() - tstart > timeout:
            os.kill(p.pid, signal.SIGKILL)
            os.waitpid(-1, os.WNOHANG)
            return None
    r = p.stdout.read()
    return r

def nothrow(ExceptionToCheck=Exception, logger=None):
    def deco_retry(f):
        def f_retry(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except ExceptionToCheck, e:
                if logger:
                    logger.info(e)
                else:
                    print str(e)
        return f_retry  # true decorator
    return deco_retry

@nothrow(Exception)
def test_nothrow():
    raise Exception('exception: xx')

if __name__ == "__main__":
    test_nothrow()

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
