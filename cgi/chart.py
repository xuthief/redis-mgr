#!/usr/bin/env python
#coding: utf-8
#file   : chart.py
#author : ning
#date   : 2014-01-22 08:39:19

from cgicommon import *

import utils

html = '''
<html>
  <head>
    <script type='text/javascript' src='http://www.google.com/jsapi'></script>
    <script type='text/javascript'>
      google.load('visualization', '1.1', {'packages':['annotationchart']});
      google.setOnLoadCallback(drawChart);
      function drawChart() {
        var data = new google.visualization.DataTable();
        data.addColumn('date', 'Date');
        data.addColumn('number', '$cmd');
        data.addRows([
          [new Date(2014, 6, 18), 250, ],
        ]);

        var chart = new google.visualization.AnnotationChart(document.getElementById('chart_div'));
        var options = {
            min: 0, 
            dateFormat: 'yyyy-MM-dd HH:mm'
        };

        chart.draw(data, options);
      }
    </script>
  </head>
  <body>
    <pre>
    usage     : /chart.py?cluster=cluster0&cmd=mem_fragmentation_ratio&period=hour&start=2014060100
    peirod    : hour/min
    start/end : in format '2014060110'
    cmd       : qps /mem /keys /_slowlog_per_sec /client_connections /forward_error_INC 
                latest_fork_usec /rdb_last_bgsave_time_sec /aof_last_rewrite_time_sec
                mem_fragmentation_ratio /hit_rate /server_err_INC /server_timedout_INC /client_err_INC
    </pre>
    <div id='chart_div' style='width: 90%; height: 500px;'></div>
  </body>
</html>
'''

def __print_statlog_line(line, args):
    ret = {}
    try:
        js = common.json_decode(line)
    except Exception, e:
        print 'badline'
        return

    def cnt_redis():
        val = 0
        for k,v in js['infos'].items():
            if k.startswith('[redis') and v['role'] == 'master':
                #print k, v['instantaneous_ops_per_sec']
                val += 1
        return val

    def sum_redis(what):
        val = 0
        for k,v in js['infos'].items():
            if k.startswith('[redis') and v['role'] == 'master' and what in v:
                #print k, v['instantaneous_ops_per_sec']
                val += float(v[what])
        return val

    def sum_redis_keys():
        val = 0
        for k,v in js['infos'].items():
            if k.startswith('[redis') and v['role'] == 'master' and 'db0' in v:
                kv = dict([item.split('=') for item in v['db0'].split(',')])
                val += float(kv['keys'])
        return val

    def sum_proxy(what):
        val = 0
        for k,v in js['infos'].items():
            if not k.startswith('[nut') :
                continue

            v = v[args['cluster']]
            if what in v:
                val += float(v[what])
        return val

    cnt            = cnt_redis()
    ret['timestr'] = js['timestr']
    ret['ts']      = int(js['ts'])

    ret['qps']     = sum_redis('instantaneous_ops_per_sec')
    ret['mem']     = sum_redis('used_memory')/1024/1024/1024
    ret['_slowlog_per_sec']   = sum_redis('_slowlog_per_sec')
    ret['client_connections'] = sum_proxy('client_connections')
    ret['forward_error_INC']  = sum_proxy('forward_error_INC')

    ret['latest_fork_usec']          = sum_redis('latest_fork_usec') / cnt
    ret['rdb_last_bgsave_time_sec']  = sum_redis('rdb_last_bgsave_time_sec') / cnt
    ret['aof_last_rewrite_time_sec'] = sum_redis('aof_last_rewrite_time_sec') / cnt
    ret['mem_fragmentation_ratio']   = sum_redis('mem_fragmentation_ratio') / cnt

    hit = sum_redis('keyspace_hits') 
    miss = sum_redis('keyspace_misses')
    ret['hit_rate'] = hit / (hit+miss)

    ret['keys'] = sum_redis_keys()

    ret['server_err_INC']      = sum_proxy('server_err_INC')
    ret['server_timedout_INC'] = sum_proxy('server_timedout_INC')
    ret['client_err_INC']      = sum_proxy('client_err_INC')

    print '[new Date(%d), %f ],' % (ret['ts'] * 1000, ret[args['cmd']])

def json_data(args):
    '''
    history monitor info of the cluster
    '''
    start_ts = utils.parse_time(args['start'])
    end_ts = utils.parse_time(args['end']) + 3600
    for t in range(start_ts, end_ts, 3600):
        timestr = common.format_time_to_hour(t)
        f = 'data/%s/statlog.%s' % (args['cluster'], timestr )

        for line in file(f):
            try:
                __print_statlog_line(line, args)
                if (args['period']) == 'hour':
                    break;
            except:
                pass

@nothrow(IOError)
def main():
    default_start = common.format_time_to_hour( time.time() - 3600*2 )
    default_end = common.format_time_to_hour(time.time())

    args = {
        'cluster' : getQS('cluster', 'cluster0'),
        'cmd'     : getQS('cmd', 'qps'),
        'period'  : getQS('period', 'min'),
        'start'   : getQS('start', default_start),
        'end'     : getQS('end', default_end),
    }
    if args['period'] == 'min' and (utils.parse_time(args['end']) - utils.parse_time(args['start'])) / 3600 > 10:
        print ''

        hours = (utils.parse_time(args['end']) - utils.parse_time(args['start']) ) / 3600
        print 'please use period=hour for %d hours of data' % hours
        return 

    print "Content-Type: text/html"
    print ""
    head, tail = html.split('[new Date(2014, 6, 18), 250, ],')
    print TT(head, args)
    json_data(args)
    print TT(tail, args)

main()
