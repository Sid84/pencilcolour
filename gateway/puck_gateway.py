#!/usr/bin/env python3
"""Poll PencilColour jobs and exercise a Puck.js UART connection, not an ESL display."""
import argparse
import asyncio
import json
import logging
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from decimal import Decimal, ROUND_HALF_UP

UART_RX = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
UART_TX = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"
LOG = logging.getLogger("puck_gateway")


def ack_for(job):
    product = job['product']
    sku = product['sku']
    if not isinstance(sku, str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,80}', sku):
        raise ValueError('SKU must contain only letters, digits, underscore, dot or hyphen')
    cents = int((Decimal(str(product['price'])) * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
    if cents < 0:
        raise ValueError('Price must be nonnegative')
    return f'ACK:{sku}:{cents}'


def command_for(ack):
    # Espruino executes newline-terminated JavaScript; the ACK proves UART only.
    return ('Bluetooth.println(' + json.dumps(ack) + ');\n').encode('utf-8')


class LineFramer:
    def __init__(self, expected):
        self.expected = expected
        self.buffer = bytearray()
        self.matched = asyncio.Event()

    def feed(self, _sender, data):
        self.buffer.extend(data)
        while b'\n' in self.buffer:
            line, _, rest = self.buffer.partition(b'\n')
            self.buffer = bytearray(rest)
            # Espruino can echo the command and prompt; only an exact line is an ACK.
            if line.strip(b'\r ').decode('utf-8', errors='replace') == self.expected:
                self.matched.set()
        if len(self.buffer) > 4096:
            self.buffer.clear()


def api_request(url, token, method, path, payload=None):
    data = None if payload is None else json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url.rstrip('/') + path, data=data, method=method,
        headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.load(response)


async def send_test(job, name, address, timeout, attempts):
    # Lazy import keeps parser and API tests runnable without a Bluetooth adapter.
    from bleak import BleakClient, BleakScanner
    ack = ack_for(job)
    for attempt in range(1, attempts + 1):
        try:
            devices = await BleakScanner.discover(timeout=5)
            device = next((d for d in devices if (d.address.lower() == address.lower() if address else d.name == name)), None)
            if device is None:
                raise RuntimeError('Puck not found; check Bluetooth and disconnect other clients')
            async with BleakClient(device) as client:
                framer = LineFramer(ack)
                await client.start_notify(UART_TX, framer.feed)
                try:
                    data = command_for(ack)
                    for offset in range(0, len(data), 20):
                        await client.write_gatt_char(UART_RX, data[offset:offset+20], response=False)
                        await asyncio.sleep(0.05)
                    await asyncio.wait_for(framer.matched.wait(), timeout)
                    return
                finally:
                    await client.stop_notify(UART_TX)
        except (Exception, asyncio.TimeoutError) as exc:
            LOG.warning('BLE test attempt %s/%s failed: %s', attempt, attempts, exc)
            if attempt == attempts:
                raise RuntimeError('BLE test failed after retries') from exc
            await asyncio.sleep(min(2 ** (attempt - 1), 10))


async def run(args, token):
    tested = set()
    while True:
        try:
            response = await asyncio.to_thread(api_request, args.url, token, 'GET', '/api/gateway/jobs')
            for job in response['jobs']:
                if job['id'] in tested:
                    continue
                try:
                    await send_test(job, args.name, args.address, args.timeout, args.attempts)
                    path = '/api/gateway/jobs/' + urllib.parse.quote(job['tagId'], safe='') + '/ack'
                    await asyncio.to_thread(api_request, args.url, token, 'POST', path,
                                            {'jobId': job['id'], 'status': 'ble_test'})
                    tested.add(job['id'])
                    LOG.info('BLE test acknowledged for %s; physical display remains pending', job['tagId'])
                except (Exception, asyncio.TimeoutError) as exc:
                    LOG.warning('Job %s test failed: %s', job.get('id'), exc)
        except (urllib.error.URLError, ValueError, KeyError, OSError) as exc:
            LOG.warning('Polling failed: %s', exc)
        if args.once:
            return
        await asyncio.sleep(args.interval)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default=os.getenv('PENCILCOLOUR_URL', 'http://localhost:3001'))
    parser.add_argument('--name', default=os.getenv('PUCK_NAME', 'Puck.js 2f91'))
    parser.add_argument('--address', default=os.getenv('PUCK_ADDRESS'), help='BLE address overrides name')
    parser.add_argument('--interval', type=float, default=15)
    parser.add_argument('--timeout', type=float, default=5)
    parser.add_argument('--attempts', type=int, default=3)
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    token = os.getenv('GATEWAY_TOKEN')
    if not token:
        parser.error('Set GATEWAY_TOKEN in the environment')
    if args.interval <= 0 or args.timeout <= 0 or args.attempts < 1:
        parser.error('interval, timeout and attempts must be positive')
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    try:
        asyncio.run(run(args, token))
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
