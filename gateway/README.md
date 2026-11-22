# PencilColour gateway

The Puck gateway tests Nordic UART communication. It sends JavaScript to an Espruino Puck that prints an ACK containing the job SKU and price in cents. This is a BLE round-trip test: it does not send an image to an E-Ink label or establish that a price was displayed. A successful test is recorded as `bleTest` on the tag; the tag stays pending and its published snapshot is unchanged. Pending jobs remain available to a real delivery gateway. A running Puck gateway tests each job ID once; restarting it can repeat a test.

## Local checks before committing or deploying

In PowerShell, from the repository root:

1. Install dependencies: `npm install --prefix server` and `python -m pip install bleak`.
2. Run `python -m unittest discover -s gateway -p test_puck_gateway.py` and `node --test server/gateway.test.js`. Run `python gateway/mock_esl.py --demo` to verify the separate virtual simulator.
3. Set a temporary local token and isolated data directory, then start the local server:

   ```powershell
   $env:GATEWAY_TOKEN = 'local-test-only'
   $env:DATA_DIR = "$PWD\.local-test-data"
   npm --prefix server start
   ```

   Use a second terminal with the same token. Start the dashboard (`npm install --prefix client`, then `npm --prefix client run dev`) and edit a product or press Publish. Check that the tag is pending and the published snapshot has not changed. Alternatively, inspect `/api/state`.
4. Turn on the Puck, disconnect the Espruino Web IDE, and run:

   ```powershell
   $env:GATEWAY_TOKEN = 'local-test-only'
   $env:PENCILCOLOUR_URL = 'http://localhost:3001'
   python gateway/puck_gateway.py --once --name 'Puck.js 2f91'
   ```

   Use `--address <BLE-address>` if names are ambiguous; omit `--once` for continuous polling. Check the log for a BLE test acknowledgement and `/api/state` for `bleTest`. The tag must still be pending. Run `python gateway/mock_esl.py` with the same environment to inspect the virtual command; it never posts an ACK. Stop the server and remove the temporary test data when finished.

For a Railway test, explicitly set `PENCILCOLOUR_URL` to the Railway URL and provide the matching gateway token through the environment, without printing or committing it. This makes API requests and records BLE test events in that environment, so use it only when authorized. The deployed server must contain the new `ble_test` endpoint behavior first. No production deployment is performed by these instructions.

The existing API is a prototype: job tracking is in memory, pending state is stored in the configured data file, and `delivered` is reserved for a future real display integration. Device selection currently sends each pending job to the selected test Puck, not to a mapped physical ESL. Production use needs durable job identities, per-device routing, authentication and delivery reconciliation.
