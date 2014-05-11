#!/usr/bin/env python
#coding: utf-8
#file   : misc_task.py
#author : ning
#date   : 2014-03-19 17:37:32


from utils import *
import pprint
from multiprocessing import Process

class MiscTask():

    def keys(self, match):
        '''
        list keys (match='p-*')
        '''

        class Worker(Process):
            def __init__(self, s):
                super(Worker, self).__init__()
                self.s = s

            def run(self):
                s = self.s
                cnt = 0
                START = time.time()
                cursor = '0'

                conn = redis.Redis(s.args['host'], s.args['port'])
                while True:
                    cursor, keys = conn.scan(cursor, match, 10000)
                    for k in keys:
                        print s, 'key', cnt, k
                        cnt += 1

                    if '0' == cursor or not keys :
                        break

        workers = []
        for s in self._active_masters():
            t = Worker(s)
            t.start()
            workers.append(t)
        for t in workers:
            t.join()

    def cleankeys(self, match):
        '''
        cleankeys (match='p-*')
        '''

        class Worker(Process):
            def __init__(self, s):
                super(Worker, self).__init__()
                self.s = s

            def run(self):
                s = self.s
                cnt = 0
                START = time.time()
                cursor = '0'

                conn = redis.Redis(s.args['host'], s.args['port'])
                while True:
                    cursor, keys = conn.scan(cursor, match, 10000)
                    pipe = conn.pipeline(transaction=False)
                    if not keys:
                        break
                    for k in keys:
                        pipe.delete(k)
                        cnt += 1
                        if cnt % 10000 == 0:
                            msg = '%s [key:%s]: %d keys done in %s seconds ' % (s, k, cnt, time.time() - START)
                            logging.info(msg)
                    pipe.execute()
                logging.notice('%s done' % s)

        workers = []
        for s in self._active_masters():
            t = Worker(s)
            t.start()
            workers.append(t)
        for t in workers:
            t.join()

