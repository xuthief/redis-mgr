#!/usr/bin/env python
#coding: utf-8
#file   : server_modules.py
#author : ning
#date   : 2014-02-24 13:00:28


import os
import sys

from utils import *

class Base:
    '''
    the sub class should implement: _alive, _pre_deploy, status, and init self.args
    '''
    def __init__(self, name, user, host_port, path):
        self.args = {
            'name'      : name,
            'user'      : user,
            'host'      : socket.gethostbyname(host_port.split(':')[0]),
            'port'      : int(host_port.split(':')[1]),
            'path'      : path,

            'localdir'  : '',     #files to deploy

            'startcmd'  : '',     #startcmd and runcmd will used to generate the control script
            'runcmd'    : '',     #process name you see in `ps -aux`, we use this to generate stop cmd
            'logfile'   : '',
        }

    def __str__(self):
        return TT('[$name:$host:$port]', self.args)

    def deploy(self):
        logging.info('deploy %s' % self)
        self.args['localdir'] = TT('tmp/$name-$host-$port', self.args)
        self._run(TT('mkdir -p $localdir/bin && mkdir -p $localdir/conf && mkdir -p $localdir/log && mkdir -p $localdir/data ', self.args))

        self._pre_deploy()
        self._gen_control_script()
        self._init_dir()

        cmd = TT('rsync -ravP $localdir/ $user@$host:$path 1>/dev/null 2>/dev/null', self.args)
        self._run(cmd, timeout=5)

    def _gen_control_script(self):
        content = file('conf/control.sh').read()
        content = TT(content, self.args)

        control_filename = TT('${localdir}/${name}_control', self.args)

        fout = open(control_filename, 'w+')
        fout.write(content)
        fout.close()
        os.chmod(control_filename, 0755)

    def start(self, timeout = 60*5):
        if self._alive():
            logging.warn('%s already running' %(self) )
            return

        logging.debug('starting %s' % self)
        t1 = time.time()
        sleeptime = .5
        self._run(self._remote_start_cmd(), timeout=5) #timeout for run cmd

        while not self._alive():
            lets_sleep(sleeptime)
            if sleeptime < 5:
                sleeptime *= 2
            else:
                sleeptime = 5
                logging.warn('%s still not alive' % self)
            if time.time() - t1 > timeout:
                logging.warn('%s still not alive, Give Up !!! ' % self)
                logging.error('%s still not alive, Give Up !!! ' % self)
                return

        t2 = time.time()
        logging.info('%s start ok in %.2f seconds' %(self, t2-t1) )

    def stop(self, timeout = 15):
        if not self._alive():
            logging.warn('%s already stop' %(self) )
            return

        self._run(self._remote_stop_cmd(), timeout=5)
        t1 = time.time()
        while self._alive():
            lets_sleep()
            if time.time() - t1 > timeout:
                logging.warn('%s still not stop, Give Up !!! ' % self)
                logging.error('%s still not stop, Give Up !!! ' % self)
                return
        t2 = time.time()
        logging.info('%s stop ok in %.2f seconds' %(self, t2-t1) )

    def printcmd(self):
        print common.to_blue(self), self._remote_start_cmd()

    def status(self):
        logging.warn("status: not implement")

    def log(self):
        cmd = TT('tail $logfile', self.args)
        logging.info('log of %s' % self)
        print self._run(self._remote_cmd(cmd))

    def _sshcmd(self, cmd, timeout=60*60*24*30):
        '''
        run a benchmark cmd on this remote machine
        '''
        remote_cmd = self._remote_cmd(cmd)
        logging.info(remote_cmd)
        print self._run(remote_cmd, timeout)

    def _alive(self):
        logging.warn("_alive: not implement")

    def _init_dir(self):
        raw_cmd = TT('mkdir -p $path', self.args)
        self._run(self._remote_cmd(raw_cmd, chdir=False), timeout=5)

    def _remote_start_cmd(self):
        cmd = TT("./${name}_control start", self.args)
        return self._remote_cmd(cmd)

    def _remote_stop_cmd(self):
        cmd = TT("./${name}_control stop", self.args)
        return self._remote_cmd(cmd)

    def _remote_cmd(self, raw_cmd, chdir=True):
        if raw_cmd.find('"') >= 0:
            raise Exception('bad cmd: ' + raw_cmd)
        args = copy.deepcopy(self.args)
        args['cmd'] = raw_cmd
        if chdir:
            return TT('ssh -o "StrictHostKeyChecking no" -n -f $user@$host "cd $path && $cmd"', args)
        else:
            return TT('ssh -o "StrictHostKeyChecking no" -n -f $user@$host "$cmd"', args)

    def _run(self, raw_cmd, timeout=60*60*24*30):
        #ret = common.system(raw_cmd, logging.debug)
        ret = system_with_timeout(raw_cmd, logging.debug, timeout)
        if ret == None:
            logging.warn("cmd timeout: " + raw_cmd)
        ret = str(ret)
        logging.debug('return : [%d] [%s] ' % (len(ret), common.shorten(ret)) )
        return ret

    def host(self):
        return self.args['host']

    def port(self):
        return self.args['port']

class RedisServer(Base):
    def __init__(self, user, host_port, path):
        Base.__init__(self, 'redis', user, host_port, path)

        self.args['startcmd'] = TT('bin/redis-server conf/redis.conf', self.args)
        self.args['runcmd']   = TT('redis-server \*:$port', self.args)

        self.args['conf']     = TT('$path/conf/redis.conf', self.args)
        self.args['pidfile']  = TT('$path/log/redis.pid', self.args)
        self.args['logfile']  = TT('$path/log/redis.log', self.args)
        self.args['dir']      = TT('$path/data', self.args)

        self.args['REDIS_CLI'] = conf.BINARYS['REDIS_CLI']

    def _info_dict(self):
        cmd = TT('$REDIS_CLI -h $host -p $port INFO', self.args)
        info = self._run(cmd, timeout=5)

        info = [line.split(':', 1) for line in info.split('\r\n') if not line.startswith('#')]
        info = [i for i in info if len(i)>1]
        ret = defaultdict(str, info) #this is a defaultdict, be Notice
        try:
            ret['_slowlog_per_sec'] = self._slowlog_per_sec()
        except:
            pass
        return ret

    def _slowlog_per_sec(self):
        CNT = 10
        conn = redis.Redis(self.args['host'], self.args['port'])
        ret = conn.execute_command('SLOWLOG', 'GET', CNT)
        if not ret:
            return 0
        timediff = time.time() - ret[-1][1]  # time diff of the first-last slow log.
        slow_per_sec = 1.0 * CNT / timediff
        return slow_per_sec

    def _ping(self):
        cmd = TT('$REDIS_CLI -h $host -p $port PING', self.args)
        return self._run(cmd, timeout=5)

    def _alive(self):
        return strstr(self._ping(), 'PONG')

    def _gen_conf(self):
        content = file('conf/redis.conf').read()
        return TT(content, self.args)

    def _pre_deploy(self):
        self.args['BINS'] = conf.BINARYS['REDIS_SERVER_BINS']
        self._run(TT('cp $BINS $localdir/bin/', self.args))

        fout = open(TT('$localdir/conf/redis.conf', self.args), 'w+')
        fout.write(self._gen_conf())
        fout.close()

    def status(self):
        uptime = self._info_dict()['uptime_in_seconds']
        if uptime:
            logging.info('%s uptime %s seconds' % (self, uptime))
        else:
            logging.error('%s is down' % self)

    def isslaveof(self, master_host, master_port):
        info = self._info_dict()
        if info['master_host'] == master_host and int(info['master_port']) == master_port:
            logging.debug('already slave of %s:%s' % (master_host, master_port))
            return True

    def slaveof(self, master_host, master_port):
        cmd = 'SLAVEOF %s %s' % (master_host, master_port)
        return self.rediscmd(cmd)

    def rediscmd(self, cmd):
        args = copy.deepcopy(self.args)
        args['cmd'] = cmd
        cmd = TT('$REDIS_CLI -h $host -p $port $cmd', args)
        logging.info('%s %s' % (self, cmd))
        print self._run(cmd)


class Sentinel(RedisServer):
    def __init__(self, user, host_port, path, masters):
        RedisServer.__init__(self, user, host_port, path)

        self.args['startcmd'] = TT('bin/redis-sentinel conf/sentinel.conf', self.args)
        self.args['runcmd']   = TT('redis-sentinel \*:$port', self.args)

        self.args['conf']     = TT('$path/conf/sentinel.conf', self.args)
        self.args['pidfile']  = TT('$path/log/sentinel.pid', self.args)
        self.args['logfile']  = TT('$path/log/sentinel.log', self.args)

        self.args['name']     = 'sentinel'
        self.masters = masters

    def _gen_conf_section(self):
        template = '''\
sentinel monitor $server_name $host $port 2
sentinel down-after-milliseconds  $server_name 60000
sentinel failover-timeout $server_name 180000
sentinel parallel-syncs $server_name 1
        '''
        cfg = '\n'.join([TT(template, master.args) for master in self.masters])
        return cfg

    def _gen_conf(self):
        content = file('conf/sentinel.conf').read()
        content = TT(content, self.args)
        return content + self._gen_conf_section()

    def _pre_deploy(self):
        self.args['BINS'] = conf.BINARYS['REDIS_SENTINEL_BINS']
        self._run(TT('cp $BINS $localdir/bin/', self.args))

        fout = open(TT('$localdir/conf/sentinel.conf', self.args), 'w+')
        fout.write(self._gen_conf())
        fout.close()

    def get_masters(self):
        '''return currnet master list of (host:port, name)'''
        conn = redis.Redis(self.args['host'], self.args['port'])
        masters = conn.sentinel_masters()
        logging.debug('sentinel got masters: %s' % masters)
        return [('%s:%s' % (m['ip'], m['port']), m['name']) for m in masters.values()]

    def get_raw_masters(self):
        '''return currnet master list of (host:port, name)'''
        conn = redis.Redis(self.args['host'], self.args['port'])
        masters = conn.sentinel_masters()
        logging.debug('sentinel got masters: %s' % masters)
        return masters

    def get_raw_slaves(self, master_name):
        conn = redis.Redis(self.args['host'], self.args['port'])
        slaves = conn.sentinel_slaves(master_name)
        logging.debug('sentinel got slaves: %s' % slaves)
        return slaves

    def reset(self, master_name):
        '''
        reset all the masters with matching name.
        '''
        conn = redis.Redis(self.args['host'], self.args['port'])
        slaves = conn.sentinel('reset', master_name)
        logging.debug('sentinel reset')
        return slaves

    def failover(self, master_name):
        '''
        Force a failover as if the master was not reachable
        '''
        conn = redis.Redis(self.args['host'], self.args['port'])
        slaves = conn.sentinel('failover', master_name)
        logging.debug('sentinel failover %s' % master_name)
        return slaves

    def get_failover_event(self):
        self._sub = redis.Redis(self.args['host'], self.args['port']).pubsub()
        self._sub.subscribe('+switch-master')
        logging.info('subscribe +switch-master on %s' % self)
        iterator = self._sub.listen()
        if next(iterator)['channel'] != '+switch-master':
            raise Exception('error on subscribe')

        for msg in iterator:
            logging.info('got msg: %s' % msg)
            yield msg

class NutCracker(Base):
    def __init__(self, user, host_port, path, masters, verbose=4):
        Base.__init__(self, 'nutcracker', user, host_port, path)

        self.masters = masters

        self.args['conf']        = TT('$path/conf/nutcracker.conf', self.args)
        self.args['pidfile']     = TT('$path/log/nutcracker.pid', self.args)
        self.args['logfile']     = TT('$path/log/nutcracker.log', self.args)
        self.args['status_port'] = self.args['port'] + 1000
        self.args['verbose']     = verbose

        self.args['startcmd']    = TT('bin/nutcracker -d -c $conf -o $logfile -p $pidfile -s $status_port -v $verbose', self.args)
        self.args['runcmd']      = TT('bin/nutcracker -d -c $conf -o $logfile -p $pidfile -s $status_port', self.args)

        if 'MON_BINS' in conf.BINARYS and os.path.exists(conf.BINARYS['MON_BINS']):
            self.args['startcmd']    = TT('bin/mon -a 60 -d "bin/nutcracker -c $conf -o $logfile -p $pidfile -s $status_port -v $verbose"', self.args) # put -d at mon
            self.args['runcmd']      = TT('bin/nutcracker -c $conf -o $logfile -p $pidfile -s $status_port', self.args)

        self._last_info = None

    def _alive(self):
        return self._info_dict()

    def _gen_conf_section(self):
        template = '    - $host:$port:1 $server_name'
        cfg = '\n'.join([TT(template, master.args) for master in self.masters])
        return cfg

    def _gen_conf(self):
        content = '''
$cluster_name:
  listen: 0.0.0.0:$port
  hash: fnv1a_64
  distribution: modula
  preconnect: true
  auto_eject_hosts: false
  redis: true
  hash_tag: "{}"
  backlog: 512
  timeout: 400
  client_connections: 0
  server_connections: 1
  server_retry_timeout: 2000
  server_failure_limit: 2
  servers:
'''
        content = TT(content, self.args)
        return content + self._gen_conf_section()

    def _pre_deploy(self):
        self.args['BINS'] = conf.BINARYS['NUTCRACKER_BINS']
        self._run(TT('cp $BINS $localdir/bin/', self.args))
        if 'MON_BINS' in conf.BINARYS and os.path.exists(conf.BINARYS['MON_BINS']):
            self.args['MON_BINS'] = conf.BINARYS['MON_BINS']
            self._run(TT('cp $MON_BINS $localdir/bin/', self.args))

        fout = open(TT('$localdir/conf/nutcracker.conf', self.args), 'w+')
        fout.write(self._gen_conf())
        fout.close()

    def _info_dict(self):
        '''
                                                        | We will add fields in the info dict
        "uptime": 370,                                  |
        "timestamp": 1389231960,                        | timestamp_INC
        ....                                            |
        "cluster0": {                                   |
            "client_connections": 100,                  |
            "client_eof": 500,                          |
            "forward_error": 0,                         | calc forward_error_INC
            "client_err": 0,                            | calc client_err_INC
            "fragments": 0,                             |
            "server_ejects": 0,                         |
                                                        | add global in_queue/out_queue/
                                                        | add global requests/responses/
                                                        | add global server_timedout/server_err
                                                        | calc requests_INC responses_INC
                                                        | calc server_timedout_INC server_err_INC
            "cluster0-20001": {       #a backend        |
                "server_timedout": 0,                   |
                "server_err": 0,                        |
                "responses": 125406,                    |
                "response_bytes": 828478,               |
                "in_queue_bytes": 0,                    |
                "server_connections": 1,                |
                "request_bytes": 5189724,               |
                "out_queue": 0,                         |
                "server_eof": 0,                        |
                "requests": 125406,                     |
                "in_queue": 0,                          |
                "out_queue_bytes": 0                    |
            },                                          |
        '''
        info = self._raw_info_dict()
        #logging.debug(info)
        if not info:
            return None

        def calc_inc(cluster_name, info, last_info):
            TO_CALC_INC = ('forward_error', 'client_err', 'requests', 'responses', 'server_timedout', 'server_err')
            for item in TO_CALC_INC:
                info[item + '_INC'] = info[item] - last_info[item]

        def aggregation(cluster_name, info):
            TO_AGGREGATION = ('in_queue', 'out_queue', 'requests', 'responses', 'server_timedout', 'server_err')
            for item in TO_AGGREGATION:
                info[item] = 0
            for k, v, in info.items():
                if type(v) == dict: # a backend
                    for item in TO_AGGREGATION:
                        info[item] += v[item]

        if self._last_info:
            info['timestamp_INC'] = info['timestamp'] - self._last_info['timestamp']

        for k, v in info.items():
            if type(v) == dict:
                cluster_name = k
                cluster_info = v
                aggregation(cluster_name, cluster_info)
                if self._last_info:
                    calc_inc(cluster_name, cluster_info, self._last_info[cluster_name])

        self._last_info = info
        logging.debug(info)
        return info

    def _raw_info_dict(self):
        try:
            ret = telnetlib.Telnet(self.args['host'], self.args['status_port'], timeout=2).read_all()
            return common.json_decode(ret)
        except Exception, e:
            logging.debug('--- can not get _info_dict of nutcracker, [Exception: %s]' % (e, ))
            return None

    def status(self):
        ret = self._info_dict()
        if ret:
            uptime = ret['uptime']
            logging.info('%s uptime %s seconds' % (self, uptime))
        else:
            logging.error('%s is down' % self)

    def get_config(self):
        '''return currnet config file content, Ignore the listen: line'''
        cmd = TT('cat $conf', self.args)
        content = self._run(self._remote_cmd(cmd), timeout=5)
        content = re.sub('listen: .*', '', content)
        content = re.sub('Permanently added.*', '', content)
        return content.strip()

    def get_masters(self):
        '''return currnet master list of (host:port, name)'''
        cmd = TT('cat $conf', self.args)
        content = self._run(self._remote_cmd(cmd), timeout=5)
        logging.debug('current proxy config: %s' % content)

        def parse_line(line):
            _x, host_port_w, name = line.split()
            host, port, _w = host_port_w.split(':')
            return ('%s:%s' % (host, port), name)
        return [parse_line(line) for line in content.split('\n') if line.startswith('    -')]

    def reconfig(self, masters):
        self.masters = masters
        self.stop(timeout = 5)
        self.deploy()
        self.start(timeout = 5)
        logging.info('proxy %s:%s is updated' % (self.args['host'], self.args['port']))


# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4


