# PencilColour Gateway — integration scaffold

This folder contains an **outbound-only gateway polling prototype**, not a BLE driver. The agent deliberately does **not** acknowledge a simulated update as delivered. Existing dashboard publish remains a demo-only simulation.

## Local run

1. Set a strong `GATEWAY_TOKEN` environment variable on the PencilColour server.
2. Start the server, then run `GATEWAY_TOKEN=<same-token> PENCILCOLOUR_URL=http://localhost:3001 python3 gateway/agent.py`.
3. Edit a product in the dashboard to create a pending update. The agent logs it but does not change a physical tag.

## Hardware integration target

Silicon Labs Bluetooth ESL reference implementation (ESL Tag + NCP access point). Its Python host example supports discovery, provisioning, OTS image upload, and PAwR/ESL Control Point commands. Hardware board compatibility and licence must be reviewed before integration. See https://docs.silabs.com/bluetooth/latest/bluetooth-electronic-shelf-label/ and https://github.com/SiliconLabs/simplicity_sdk/tree/sisdk-2025.6/app/bluetooth/example_host/bt_host_esl_ap .

## Next engineering tasks

- Choose and purchase a specific compatible radio board and physical EPD tag; verify actual display driver and image format.
- Replace dry-run output with a hardware adapter using the vendor ESL AP host interface.
- ACK only after device-level confirmation, and separately track displayed image version.
- Add durable job storage, per-gateway identities, rate limiting, replay protection, store isolation, key rotation and audit logs.
- Ensure retail price updates are reconciled with POS and failures alert staff.

**Security:** This is a prototype. The current PencilColour MVP has no dashboard user authentication. Do not deploy it for live retail prices or expose it publicly with sensitive data.
