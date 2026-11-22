#!/usr/bin/env python3
"""PencilColour Gateway: dry-run integration only; no BLE radio driver yet."""
import json, os, time, urllib.request, urllib.error
URL=os.getenv('PENCILCOLOUR_URL','http://localhost:3001').rstrip('/')
TOKEN=os.environ['GATEWAY_TOKEN']
INTERVAL=max(5,int(os.getenv('POLL_SECONDS','15')))
def request(method,path,payload=None):
    data=None if payload is None else json.dumps(payload).encode()
    req=urllib.request.Request(URL+path,data=data,method=method,headers={
        'Authorization':'Bearer '+TOKEN,'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=15) as response:
        return json.load(response)
while True:
    try:
        for job in request('GET','/api/gateway/jobs')['jobs']:
            # IMPORTANT: dry-run mode only. Does not prove a physical label changed.
            print('SIMULATED ESL UPDATE:',job['tagId'],job['product'],flush=True)
            # Do not ACK as delivered: that would falsely report a physical update.
    except (urllib.error.URLError,ValueError,KeyError) as exc:
        print('Gateway polling error:',exc,flush=True)
    time.sleep(INTERVAL)
