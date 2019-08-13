#!/usr/bin/python
# Script to post metrics to statuspage.io
#
import os
import time
import random
import json
import requests
from cassandra.cluster import Cluster
from cassandra.policies import DCAwareRoundRobinPolicy
from cassandra import ConsistencyLevel

config = '/opt/datastax/scripts/metrics.conf'
api_base = 'https://api.statuspage.io'
inserted_value=999

if os.path.isfile(config):
   cfgfile=open(config,'r')
   params=json.load(cfgfile)
   cfgfile.close()

   api_key = params['api_key']
   page_id = params['page_id']
   metric_id = params['metric_id']
   opscenter_id = params['cluster_id']
   hosts = params['cluster']
else:
   print 'Could not locate configuration file'
   exit

#headers = {"Content-Type": "application/json", "Authorization": "OAuth " + api_key}
#r = requests.get(api_base + "/v1/pages/" + page_id + "/components",headers=headers)
#print json.dumps(r.json())

key = random.randint(1,21)
value = random.randint(1,21)

# First connect to the cluster and create a keyspace and table
# and insert a random value into a random key
cluster=Cluster(hosts)

try:
   session=cluster.connect()
   session.default_consistency_level=ConsistencyLevel.LOCAL_QUORUM
   rows=session.execute("CREATE KEYSPACE IF NOT EXISTS cloudops WITH REPLICATION = {'class':'NetworkTopologyStrategy','DCx':3}")
   rows=session.execute("CREATE TABLE IF NOT EXISTS cloudops.slacheck(key int, value int, primary key (key))")
   rows=session.execute("INSERT into cloudops.slacheck(key,value) VALUES(%s, %s)",[key,value])
   cluster.shutdown()
except Exception as e:
   print "Exception : ",e

# next reconnect and try and read that value
cluster=Cluster(hosts)

try:
   session=cluster.connect()
   session.default_consistency_level=ConsistencyLevel.LOCAL_QUORUM
   rows=session.execute("SELECT value FROM cloudops.slacheck where key = %s",[key])
   inserted_value=rows[0][0]
   cluster.shutdown()
except Exception as e:
   print "Exception : ",e

if value==inserted_value:
   print 'SLA Check OK ',key,value,inserted_value
   cluster_status={"component":{"status":"operational"}}
else:
   print 'values do not match',key,value,inserted_value
   cluster_status={"component":{"status":"major_outage"}}

headers = {"Content-Type": "application/json", "Authorization": "OAuth " + api_key}
r = requests.put(api_base + "/v1/pages/" + page_id + "/components/" + cluster_id, data=json.dumps(cluster_status), headers=headers)

