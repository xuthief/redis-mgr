#!/usr/bin/env python
#coding: utf-8
#file   : migrate.py
#author : ning
#date   : 2014-02-24 12:45:43

from utils import *
from server_modules import *

class Migrate():
    def migrate(self, src, dst):
        '''
        migrate a redis instance to another machine
        '''
        src_host_port, src_path = src.rsplit(':', 1)
        dst_host_port, dst_path = dst.rsplit(':', 1)

        #if src is master.
        #self.all_redis = [ RedisServer(self.args['user'], hp, path) for hp, path in self.args['redis'] ]
        #todo: use find_redis
        src_redis = RedisServer(self.args['user'], src_host_port, src_path)
        dst_redis = RedisServer(self.args['user'], dst_host_port, dst_path)

        dst_redis.deploy()
        dst_redis.start()
        dst_redis.slaveof(src_redis.args['host'], src_redis.args['port'])
        dst_redis.wait_repl()
        src_redis.stop()
        wait_confirm()
        src_redis.cleanup()


        print src, dest
        pass
