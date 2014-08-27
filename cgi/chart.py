#!/usr/bin/env python
#coding: utf-8
#file   : chart.py
#author : ning
#date   : 2014-01-22 08:39:19

from cgicommon import *

import utils

#base on http://www.highcharts.com/demo/spline-irregular-time
html = '''
<html>
  <head>
    <title>redis stat</title>
    <script src="http://www.highcharts.com/lib/jquery-1.7.2.js"></script>
    <script src="http://code.highcharts.com/highcharts.js"></script>
    <script src="http://code.highcharts.com/modules/exporting.js"></script>
    <style type="text/css">
        .current {background-color:yellow; text-decoration: none;}
    </style>


    <script type='text/javascript'>

    $(function () {

        Highcharts.setOptions({
            global: {
                useUTC: false
            }
        });

        $('#container').highcharts({
            chart: {
                type: 'spline'
            },
            title: {
                text: 'redis stat of xxx'
            },
            xAxis: {
                type: 'datetime',
                dateTimeLabelFormats: { // don't display the dummy year
                    minute: '%Y-%m-%d<br/>%H:%M',
                    hour: '%Y-%m-%d<br/>%H:%M',
                    day: '%Y<br/>%m-%d',
                },
                title: {
                    text: 'Date'
                }
            },
            yAxis: {
                title: {
                    text: 'xxx'
                },
                min: 0
            },
            tooltip: {
                headerFormat: '<b>{series.name}</b><br>',
                pointFormat: '{point.x: %Y-%m-%d %H:%M}: {point.y:.2f}'
            },

            series: [{
                name: 'xxx',
                data: [
                    [new Date(2014, 6, 18), 250, ],
                ]
            }]
        });
    });

function get_qs() {
    var pairs = window.location.search.substring(1).split("&"), obj = {}, pair;

    for (var i in pairs) {
        if (pairs[i] === "")
            continue;
        pair = pairs[i].split("=");
        obj[decodeURIComponent(pair[0])] = decodeURIComponent(pair[1]);
    }
    return obj;
}

function _to_qs(obj) {
    return Object.keys(obj).reduce(function(a,k){a.push(k+'='+encodeURIComponent(obj[k]));return a},[]).join('&')
}

function set_qs(obj) {
    url = window.location.pathname + '?' + _to_qs(obj);
    window.location=url;
    return false;
}

$(function () {
    $('#cluster_nav a').click(function() {
        qs = get_qs();
        qs['cluster'] = this.id;
        return set_qs(qs);
    });

    $('#query_nav a').click(function() {
        qs = get_qs();
        qs['query'] = this.id;
        return set_qs(qs);
    });

    $('#period_nav a').click(function() {
        qs = get_qs();
        qs['period'] = this.id;
        return set_qs(qs);
    });

    $('#start_nav a').click(function() {
        qs = get_qs();
        qs['start'] = this.id;
        return set_qs(qs);
    });

    //mark current
    qs = get_qs();
    $('#cluster_nav a').each(function() { if (this.id == qs['cluster']){ $(this).addClass('current'); } });
    $('#query_nav a').each(function()   { if (this.id == qs['query']){ $(this).addClass('current'); } });
    $('#period_nav a').each(function()  { if (this.id == qs['period']){ $(this).addClass('current'); } });
    $('#start_nav a').each(function()   { if (this.id == qs['start']){ $(this).addClass('current'); } });

});

    </script>
  </head>
  <body>

    <pre>
    usage     : /chart.py?cluster=cluster0&query=mem_fragmentation_ratio&period=hour&start=2014060100&end=2014060200
    </pre>
    <div id="cluster_nav" style="width:100%;">
    cluster:
        <a id="cluster0" href="">   cluster0 </a>|
        <a id="cluster1" href="">   cluster1 </a>|
        <a id="cluster2" href="">   cluster2 </a>|
        <a id="cluster5" href="">   cluster5 </a>|
        <a id="cluster6" href="">   cluster6 </a>|
        <a id="cluster9" href="">   cluster9 </a>|
    </div>
    <div id="query_nav" style="width:100%;">
    query:
        <a id="qps"                                      href="">   qps                         </a>|
        <a id="mem"                                      href="">   mem                         </a>|
        <a id="keys"                                     href="">   keys                        </a>|
        <a id="_slowlog_per_sec"                         href="">   _slowlog_per_sec            </a>|
        <a id="client_connections"                       href="">   client_connections          </a>|
        <a id="forward_error_INC"                        href="">   forward_error_INC           </a>|
        <a id="latest_fork_usec"                         href="">   latest_fork_usec            </a>|
        <a id="rdb_last_bgsave_time_sec"                 href="">   rdb_last_bgsave_time_sec    </a>|
        <a id="aof_last_rewrite_time_sec"                href="">   aof_last_rewrite_time_sec   </a>|
        <a id="mem_fragmentation_ratio"                  href="">   mem_fragmentation_ratio     </a>|
        <a id="hit_rate"                                 href="">   hit_rate                    </a>|
        <a id="server_err_INC"                           href="">   server_err_INC              </a>|
        <a id="server_timedout_INC"                      href="">   server_timedout_INC         </a>|
        <a id="client_err_INC"                           href="">   client_err_INC              </a>|

    </div>

    <div id="period_nav" style="width:100%;">
    period: <a id="hour" href=""> hour </a>|
           <a id="min" href=""> min </a>|
    </div>

    <div id="start_nav" style="width:100%;">
    start:

    {start_list}
    </div>

    <div id='container' style='width: 90%; height: 500px;'></div>

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
    #print hit, miss

    if hit+miss > 0:
        ret['hit_rate'] = hit / (hit+miss)
    else :
        ret['hit_rate'] = 0

    ret['keys'] = sum_redis_keys()

    ret['server_err_INC']      = sum_proxy('server_err_INC')
    ret['server_timedout_INC'] = sum_proxy('server_timedout_INC')
    ret['client_err_INC']      = sum_proxy('client_err_INC')

    print '[%d, %f ],' % (ret['ts'] * 1000, ret[args['query']])

def json_data(args):
    '''
    history monitor info of the cluster
    '''
    start_ts = utils.parse_time(args['start'])
    end_ts = utils.parse_time(args['end']) + 3600
    for t in range(start_ts, end_ts, 3600):
        try:
            timestr = common.format_time_to_hour(t)
            f = 'data/%s/statlog.%s' % (args['cluster'], timestr )

            for line in file(f):
                try:
                    __print_statlog_line(line, args)
                    if (args['period']) == 'hour':
                        break;
                except:
                    pass
        except:
            pass

@nothrow(IOError)
def main():
    default_start = common.format_time_to_hour( time.time() - 3600*2 )
    default_end = common.format_time_to_hour(time.time())

    args = {
        'cluster' : getQS('cluster', 'cluster0'),
        'query'   : getQS('query', 'qps'),
        'period'  : getQS('period', 'min'),
        'start'   : getQS('start', default_start),
        'end'     : getQS('end', default_end),
    }
    if args['period'] == 'min' and (utils.parse_time(args['end']) - utils.parse_time(args['start'])) / 3600 > 10:
        print ''

        hours = (utils.parse_time(args['end']) - utils.parse_time(args['start']) ) / 3600
        print 'please use period=hour for %d hours of data' % hours
        return

    start_list = [
        common.format_time_to_hour(time.time() - 3600*24*7),
        common.format_time_to_hour(time.time() - 3600*24),
        common.format_time_to_hour(time.time() - 3600* 2 ),
    ]
    start_list = '\n'.join (['<a id="%s" href=""> %s </a>|' %(i, i) for i in start_list])

    print "Content-Type: text/html"
    print ""
    head, tail = html.split('[new Date(2014, 6, 18), 250, ],')
    print head
    json_data(args)
    print tail.replace('{start_list}', start_list)

main()
