#!/usr/bin/env python
#coding: utf-8
#file   : cgicommon.py
#author : ning
#date   : 2014-01-22 08:49:01

import os
import sys

PWD = os.path.dirname(os.path.realpath(__file__))
WORKDIR = os.path.join(PWD,  '../')

sys.path.insert(0, os.path.join(WORKDIR, 'lib/'))
sys.path.insert(0, os.path.join(WORKDIR, 'conf/'))
sys.path.insert(0, os.path.join(WORKDIR, 'bin/'))

from utils import *

import cgi
import logging
import cgitb; cgitb.enable()

log_path = os.path.dirname(os.path.realpath(__file__)) + '/../log/web.log'
common.init_logging(logging.root, logging.DEBUG, False, log_path)

qs = cgi.FieldStorage()
def getQS(key, default):
    if (key not in qs) : return default
    else: return qs[key].value

