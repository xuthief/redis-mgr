#!/usr/bin/env python
#coding: utf-8
#file   : migrate.py
#author : ning
#date   : 2014-02-24 12:45:43

from utils import *
import pprint

class Migrate():
    def migrate(self, src, dst):
        '''
        migrate a redis instance to another machine
        src/dst format: cluster0-22000:127.0.0.5:23000:/tmp/r/redis-23000 cluster0-22000:127.0.0.5:50015:/tmp/r/redis-50015

        0. pre_check
        1. if src is master, force sentinel a failover, make src be slave, wait sync
        2. deploy dst
        3. add dst as slave to the group master, wait repl
        4. confirm, stop and cleanup src
        5. force sentinel reset this group
        6. update config
        '''
        def wait_repl(m, s):
            while True:
                info = s._info_dict()
                d = { 'master_link_status':       info['master_link_status'],
                      'used_memory':              info['used_memory'],
                      #'master_sync_in_progress':  info['master_sync_in_progress'],
                      'slave_repl_offset':        info['slave_repl_offset'],
                    }
                logging.info('%s: %s' % (s, str(d)))
                if info['master_link_status'] == 'up':
                    break
                time.sleep(1)

        #TODO: schedular must be stoped here(it can not find the new redis instance)
        #but we need schedular to reconfig proxy here
        src_redis = self._make_redis(src)
        dst_redis = self._make_redis(dst)

        def pre_check():
            if src_redis.args['server_name'] != dst_redis.args['server_name']:
                raise Exception('server_name not match')

            src_host_port = TT('$host:$port', src_redis.args)
            if str(src_redis) != str(self._find_redis(src_host_port, '')):
                raise Exception('src_redis %s not found in this cluster' % src_redis)


            #check the old master-slave is ok
            sentinel = self._get_available_sentinel()
            master_name = src_redis.args['server_name']
            master = sentinel.get_raw_masters()[master_name]
            slaves = sentinel.get_raw_slaves(master_name)

            if master['is_disconnected']:
                raise Exception('master %s not ok for %s' % (master, master_name))
            if len(slaves) == 0:
                raise Exception('no slave for %s' % master_name)
            for slave in slaves:
                if slave['is_disconnected']:
                    raise Exception('slave %s not ok for %s' % (slave, master_name))

            #check if dst exists
            if dst_redis._alive():
                raise Exception('dst_redis is alive')

        def force_src_be_slave():
            sentinel = self._get_available_sentinel()
            if src_redis._info_dict()['role'] == 'master':
                logging.notice('%s is master, make it be slave' % (src_redis))
                sentinel.failover(src_redis.args['server_name'])
                wait_repl(None, src_redis)

        def deploy_dst():
            dst_redis.deploy()
            dst_redis.start()

        def add_dst_as_slave():
            sentinel = self._get_available_sentinel()
            h = src_redis._info_dict()['master_host']
            p = src_redis._info_dict()['master_port']

            dst_redis.slaveof(h, p)

            wait_repl(None, dst_redis)

        def cleanup():
            src_redis.stop()
            #wait_confirm()
            #src_redis.cleanup()
            pass

        def sentinel_reset():
            self.sentinel_cmd_reset(src_redis.args['server_name'])

        def update_config():
            '''
            we can generate a right config file, but not readable. so we just append to it
            '''
            fout = file('conf/%s.py'%config_name, 'a')
            def append_config(s):
                logging.info('AppendConfig:' + s)
                print >>fout, s

            if 'migration' not in self.args:
                append_config("%s['migration'] = []" % self.args['cluster_name'])
            append_config("%s['migration'].append('%s=>%s')" % (self.args['cluster_name'], src, dst))

        steps = [
               pre_check,
               force_src_be_slave,
               deploy_dst,
               add_dst_as_slave,
               cleanup,
               sentinel_reset,
               update_config,
            ]

        for step in steps:
            try:
                logging.notice(step.__name__)
                step()
            except Exception, e:
                logging.error('exception: %s ' %e )
                return

