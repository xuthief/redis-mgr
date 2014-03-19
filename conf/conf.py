#coding: utf-8
#the port: role: x, cluster_id: x, instance:xx
#       2        0              x           xx

#port standard 1
#redis-master   22xxx
#redis-slave    23xxx
#proxy          24xxx 25xxx(status-port)
#sentinel       29xxx

#port standard 2

#redis-master   2xxx
#redis-slave    3xxx
#proxy          4xxx 5xxx(status-port)
#sentinel       9xxx

#we will generate:
#port
#pidfile
#logfile
#dir

#path in the deploy machine
BINARYS = {
    'REDIS_SERVER_BINS' : '/home/ning/idning-github/redis/src/redis-*',
    'REDIS_CLI' : '/home/ning/idning-github/redis/src/redis-cli',
    'REDIS_SENTINEL_BINS' : '/home/ning/idning-github/redis/src/redis-sentinel',
    'NUTCRACKER_BINS' : '/home/ning/idning-github/twemproxy/src/nutcracker',
}

RDB_SLEEP_TIME = 1

#optional
REDIS_MONITOR_EXTRA = {
    'used_cpu_user':              (0, 50),
}

#optional
NUTCRACKER_MONITOR_EXTRA = {
    'client_connections':  (0, 10),
    "forward_error_INC":   (0, 1000),  # in every minute
    "client_err_INC":      (0, 1000),  # in every minute
    'in_queue':            (0, 10),
    'out_queue':           (0, 10),
}

cluster0 = {
    'cluster_name': 'cluster0',
    'user': 'ning',
    'sentinel':[
        ('127.0.0.5:29001', '/tmp/r/sentinel-29001'),
        ('127.0.0.5:29002', '/tmp/r/sentinel-29002'),
        ('127.0.0.5:29003', '/tmp/r/sentinel-29003'),
    ],
    'redis': [
        # master(host:port, install path)       ,  slave(host:port, install path)
        ('127.0.0.5:22000', '/tmp/r/redis-22000'), ('127.0.0.5:23000', '/tmp/r/redis-23000'),
        ('127.0.0.5:22001', '/tmp/r/redis-22001'), ('127.0.0.5:23001', '/tmp/r/redis-23001'),
        ('127.0.0.5:22002', '/tmp/r/redis-22002'), ('127.0.0.5:23002', '/tmp/r/redis-23002'),
        ('127.0.0.5:22003', '/tmp/r/redis-22003'), ('127.0.0.5:23003', '/tmp/r/redis-23003'),
    ],
    'nutcracker': [
        ('127.0.0.5:24000', '/tmp/r/nutcracker-24000'),
        ('127.0.0.5:24001', '/tmp/r/nutcracker-24001'),
        ('127.0.0.5:24002', '/tmp/r/nutcracker-24002'),
        ('127.0.0.5:24003', '/tmp/r/nutcracker-24003'),
    ],
}

cluster0['migration'] = []
cluster0['migration'].append('cluster0-22000:127.0.0.5:22000:/tmp/r/redis-22000=>cluster0-22000:127.0.0.5:52000:/tmp/r/redis-52000')
cluster0['migration'].append('cluster0-22000:127.0.0.5:23000:/tmp/r/redis-23000=>cluster0-22000:127.0.0.5:53000:/tmp/r/redis-53000')
cluster0['migration'].append('cluster0-22000:127.0.0.5:53000:/tmp/r/redis-53000=>cluster0-22000:127.0.0.5:54000:/tmp/r/redis-54000')
cluster0['migration'].append('cluster0-22000:127.0.0.5:54000:/tmp/r/redis-54000=>cluster0-22000:127.0.0.5:55000:/tmp/r/redis-55000')
cluster0['migration'].append('cluster0-22000:127.0.0.5:52000:/tmp/r/redis-52000=>cluster0-22000:127.0.0.5:56000:/tmp/r/redis-56000')
cluster0['migration'].append('cluster0-22000:127.0.0.5:55000:/tmp/r/redis-55000=>cluster0-22000:127.0.0.5:52000:/tmp/r/redis-52000')
cluster0['migration'].append('cluster0-22000:127.0.0.5:56000:/tmp/r/redis-56000=>cluster0-22000:127.0.0.5:57000:/tmp/r/redis-57000')
cluster0['migration'].append('cluster0-22000:127.0.0.5:52000:/tmp/r/redis-52000=>cluster0-22000:127.0.0.5:58000:/tmp/r/redis-58000')
cluster0['migration'].append('cluster0-22000:127.0.0.5:57000:/tmp/r/redis-57000=>cluster0-22000:127.0.0.5:59000:/tmp/r/redis-59000')
cluster0['migration'].append('cluster0-22000:127.0.0.5:58000:/tmp/r/redis-58000=>cluster0-22000:127.0.0.5:60000:/tmp/r/redis-60000')
cluster0['migration'].append('cluster0-22000:127.0.0.5:59000:/tmp/r/redis-59000=>cluster0-22000:127.0.0.5:61000:/tmp/r/redis-61000')
cluster0['migration'].append('cluster0-22000:127.0.0.5:60000:/tmp/r/redis-60000=>cluster0-22000:127.0.0.5:62000:/tmp/r/redis-62000')
cluster0['migration'].append('cluster0-22000:127.0.0.5:61000:/tmp/r/redis-61000=>cluster0-22000:127.0.0.5:63000:/tmp/r/redis-63000')
cluster0['migration'].append('cluster0-22000:127.0.0.5:62000:/tmp/r/redis-62000=>cluster0-22000:127.0.0.5:65000:/tmp/r/redis-65000')
cluster0['migration'].append('cluster0-22000:127.0.0.5:63000:/tmp/r/redis-63000=>cluster0-22000:127.0.0.5:63001:/tmp/r/redis-63001')
