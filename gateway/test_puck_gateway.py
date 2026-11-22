import asyncio
import unittest
from unittest.mock import patch
import puck_gateway as gateway


class GatewayTests(unittest.IsolatedAsyncioTestCase):
    def test_command_and_price(self):
        job = {'product': {'sku': 'MILK-001', 'price': 4.40}}
        ack = gateway.ack_for(job)
        self.assertEqual(ack, 'ACK:MILK-001:440')
        self.assertEqual(gateway.command_for(ack), b'Bluetooth.println("ACK:MILK-001:440");\n')
        with self.assertRaises(ValueError):
            gateway.ack_for({'product': {'sku': 'bad\ncode', 'price': 1}})

    async def test_fragmented_ack_and_echo(self):
        framer = gateway.LineFramer('ACK:MILK-001:440')
        framer.feed(None, b'Bluetooth.println("ACK:MILK-001:440");\r\nACK:MIL')
        self.assertFalse(framer.matched.is_set())
        framer.feed(None, b'K-001:44')
        self.assertFalse(framer.matched.is_set())
        framer.feed(None, b'0\r\n')
        self.assertTrue(framer.matched.is_set())

    async def test_poll_reports_ble_test_only(self):
        job = {'id': 'j1', 'tagId': 'tag/1', 'product': {'sku': 'MILK-001', 'price': 4.4}}
        calls = []
        def request(url, token, method, path, payload=None):
            calls.append((method, path, payload))
            return {'jobs': [job]} if method == 'GET' else {'ok': True}
        class Args:
            url='http://localhost'; name='Puck'; address=None; timeout=1; attempts=1; once=True; interval=1
        with patch.object(gateway, 'api_request', side_effect=request), patch.object(gateway, 'send_test', new_callable=unittest.mock.AsyncMock):
            await gateway.run(Args(), 'test')
        self.assertEqual(calls[1], ('POST', '/api/gateway/jobs/tag%2F1/ack', {'jobId': 'j1', 'status': 'ble_test'}))

if __name__ == '__main__':
    unittest.main()
