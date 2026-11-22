# PencilColour virtual ESL test

No ESL or Puck.js required. Uses Python 3 standard library only.

## Quick standalone demonstration

```bash
python3 gateway/mock_esl.py --demo
```

This prints a generated `DISPLAY_PRODUCT` command with `priceCents: 380`, a virtual display state and `SIMULATED_ACK`.

## Test with the actual PencilColour backend

Terminal 1:
```bash
npm run install:all
GATEWAY_TOKEN=local-test-token npm run dev
```

Change a product price in the dashboard at http://localhost:5173. The associated tag should become pending.

Terminal 2:
```bash
GATEWAY_TOKEN=local-test-token python3 gateway/mock_esl.py
```

The script fetches pending jobs from the API and prints the command sent to the virtual label. It **does not** report physical delivery or mark the tag as synced. The message schema is PencilColour's own *mock contract*, **not** a confirmed Gicisky BLE protocol. Never use this test token on a public deployment.
