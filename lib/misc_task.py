#!/usr/bin/env python
#coding: utf-8
#file   : misc_task.py
#author : ning
#date   : 2014-03-19 17:37:32


from utils import *
import pprint
from multiprocessing import Process
from threading import Thread

class MiscTask():
    def keys(self, match):
        '''
        list keys (match='p-*')
        '''

        class Worker(Thread):
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
                    cursor, keys = conn.scan(cursor, match, 1000)
                    for k in keys:
                        #print s, 'key', cnt, k
                        sys.stdout.write('%s\n' % k)
                        cnt += 1

                    if '0' == cursor:
                        break

                logging.notice('%s done, keys: %d' % (s, cnt))

        workers = []
        for s in self._active_masters():
            logging.info('get key from %s' % s)
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
                    cursor, keys = conn.scan(cursor, match, 1000)
                    pipe = conn.pipeline(transaction=False)
                    for k in keys:
                        pipe.delete(k)
                        cnt += 1
                        if cnt % 10000 == 0:
                            msg = '%s [key:%s]: %d keys done in %s seconds ' % (s, k, cnt, time.time() - START)
                            logging.info(msg)
                    pipe.execute()
                    if '0' == cursor :
                        break
                logging.notice('%s done, cleankeys: %d' % (s, cnt))

        workers = []
        for s in self._active_masters():
            logging.info('clean key on %s' % s)
            t = Worker(s)
            t.start()
            workers.append(t)
        for t in workers:
            t.join()

    def upgrade_nutcracker(self):
        '''
        upgrade nutcracker instance, support --filter
        '''
        masters = self._active_masters()

        i = 0
        pause_cnt = len(self.all_nutcracker) / 3 + 1

        for m in self.all_nutcracker:
            if self.cmdline.filter and not strstr(str(m), self.cmdline.filter):
                logging.notice("Ignore :%s" % m)
            else:
                logging.notice("Upgrade :%s" % m)
                m.reconfig(masters)
            if i % pause_cnt == 0 and i+1<len(self.all_nutcracker):
                while 'yes' != raw_input('do you want to continue yes/ctrl-c: '):
                    pass
            i+=1

        logging.notice('reconfig all nutcracker Done!')

    def upgrade_sentinel_danger(self):
        '''
        this may reset all masert-slave relation at sentinel
        '''
        for m in self.all_sentinel:
            m.stop()
            m.deploy()

        for m in self.all_sentinel:
            m.start()

        logging.notice('reconfig all sentinel Done!')

    def randomkill(self, cnt=10):
        '''
        random kill master every mintue (for test failover)
        '''
        cnt = int(cnt)
        for i in range(cnt):
            r = random.choice(self._active_masters())
            logging.notice('%d/%d: will restart %s' % (i, cnt, r))
            r.stop()
            time.sleep(80)
            r.start()
            time.sleep(60)


class BenchThread(threading.Thread):
    def __init__ (self, redis, cmd):
        threading.Thread.__init__(self)
        self.redis = redis
        self.cmd = cmd
    def run(self):
        self.redis._sshcmd(self.cmd)


class Benchmark():
    def nbench(self, cnt=100000):
        '''
        run benchmark against nutcracker
        '''
        i = 0
        masters= self._active_masters()
        for s in self.all_nutcracker:
            args = copy.deepcopy(s.args)
            args['cnt'] = cnt
            cmd = TT('bin/redis-benchmark --csv -h $host -p $port -r 100000 -t set,get -n $cnt -c 100 ', args)

            BenchThread(masters[i], cmd).start()
            i += 1
            i %= len(masters)

    def mbench(self, cnt=100000):
        '''
        run benchmark against redis master
        '''
        for s in self._active_masters():
            args = copy.deepcopy(s.args)
            args['cnt'] = cnt
            cmd = TT('bin/redis-benchmark --csv -h $host -p $port -r 100000 -t set,get -n $cnt -c 100 ', args)
            BenchThread(s, cmd).start()

    def stopbench(self):
        '''
        you will need this for stop benchmark
        '''
        return self.sshcmd("pkill -f 'bin/redis-benchmark'")


