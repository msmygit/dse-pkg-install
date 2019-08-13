#!/usr/bin/python
# Script to post metrics to statuspage.io
#
import os
import time
import random
import json
import requests

config = '/opt/datastax/scripts/metrics.conf'
api_base = 'https://api.statuspage.io'
opscenter_base = 'http://localhost:8888'
step = 1

if os.path.isfile(config):
   cfgfile=open(config,'r')
   params=json.load(cfgfile)
   cfgfile.close()

   api_key = params['api_key']
   page_id = params['page_id']
   metric_id = params['metric_id']
   opscenter_id = params['opscenter_id']
   username = params['username']
   password = params['password']
else:
   print 'Could not locate configuration file'
   exit

#headers = {"Content-Type": "application/json", "Authorization": "OAuth " + api_key}
#r = requests.get(api_base + "/v1/pages/" + page_id + "/components",headers=headers)
#print json.dumps(r.json())

# First connect to OpsCenter and get a session key
headers = {"Content-Type": "application/json", "Accept": "text/plain"}
payload={"username" : username, "password" : password}
try:
   r = requests.post(opscenter_base + "/login", data = payload)
   r.raise_for_status()
   if r.ok:
      sessionid= r.json()['sessionid']
      opscenter_status={"component":{"status":"operational"}}

      # Use the session key to get the latest reads/sec and writes/sec
      ts_end = int(time.time()-(step*60))
      ts_start = ts_end-(step*120)
      params = {"step": step, "start": ts_start, "end": ts_end, "function" : "average"}
      headers = {"opscenter-session": sessionid}
      r=requests.get(opscenter_base + "/store/cluster-metrics/all/write-ops",params=params,headers=headers)
      if r.ok:
         for ts,value in r.json()['Total']['AVERAGE']:
            print ts,value
            params = {'data[timestamp]': ts, 'data[value]': value}
            headers = {"Content-Type": "application/json","Authorization":"OAuth "+api_key}
            r=requests.post(api_base+"/v1/pages/"+page_id+"/metrics/"+metric_id+"/data.json",params=params,headers=headers)
   else:
      opscenter_status={"component":{"status":"major_outage"}}

except requests.exceptions.RequestException as e:
   print "Could not Connect to OpsCenter"
   opscenter_status={"component":{"status":"major_outage"}}

headers = {"Content-Type": "application/json", "Authorization": "OAuth " + api_key}
r = requests.put(api_base + "/v1/pages/" + page_id + "/components/" + opscenter_id, data=json.dumps(opscenter_status), headers=headers)


