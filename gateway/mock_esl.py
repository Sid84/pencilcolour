#!/usr/bin/env python3
"""Virtual ESL transport: inspect commands without BLE or falsely syncing tags."""
import argparse, hashlib, json, os, urllib.request
from datetime import datetime, timezone

class VirtualESL:
    def __init__(self, tag_id):
        self.tag_id = tag_id
        self.display = None
    def receive(self, message):
        assert message['protocol'] == 'pencilcolour.mock.v1'
        assert message['deviceId'] == self.tag_id
        assert message['command'] == 'DISPLAY_PRODUCT'
        payload = message['payload']
        assert isinstance(payload['priceCents'], int) and payload['priceCents'] >= 0
        self.display = payload
        return {'deviceId': self.tag_id, 'status': 'SIMULATED_ACK', 'messageId': message['messageId']}

def build_message(job):
    p = job['product']
    payload = {'sku': p.get('sku'), 'name': p['name'], 'size': p.get('size'),
               'priceCents': round(float(p['price']) * 100),
               'previousPriceCents': None if p.get('previousPrice') is None else round(float(p['previousPrice']) * 100)}
    return {'protocol': 'pencilcolour.mock.v1', 'messageId': job['id'],
            'deviceId': job['tagId'], 'command': 'DISPLAY_PRODUCT', 'payload': payload}

def jobs_from_api(url, token):
    req = urllib.request.Request(url.rstrip('/')+'/api/gateway/jobs',
                                 headers={'Authorization': 'Bearer '+token})
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.load(response)['jobs']

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--demo', action='store_true', help='Run with a sample price change job, no server required')
    args = parser.parse_args()
    if args.demo:
        jobs = [{'id':'demo-001', 'tagId':'tag-demo-01', 'product':
                 {'sku':'MILK-001','name':'Milk','size':'2 L','price':3.80,'previousPrice':3.50}}]
    else:
        token = os.environ.get('GATEWAY_TOKEN')
        if not token:
            parser.error('Set GATEWAY_TOKEN or use --demo')
        jobs = jobs_from_api(os.getenv('PENCILCOLOUR_URL','http://localhost:3001'),token)
    if not jobs:
        print('No pending jobs. Edit a product in the dashboard to generate one.')
    for job in jobs:
        msg = build_message(job)
        virtual = VirtualESL(job['tagId'])
        ack = virtual.receive(msg)
        print('GENERATED_COMMAND:', json.dumps(msg, indent=2))
        print('VIRTUAL_DISPLAY:', json.dumps(virtual.display, indent=2))
        print('VIRTUAL_RESPONSE:', json.dumps(ack, indent=2))
        print('NOTE: No physical BLE write occurred. No delivered ACK sent to PencilColour server.')
if __name__ == '__main__':
    main()
