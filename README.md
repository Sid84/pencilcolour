# PencilColour MVP

A local-first electronic shelf label (ESL) dashboard and simulator. **No real devices are connected.**

## Prerequisites
- Node.js 20 or later, npm

## Run
```bash
npm run install:all
npm run dev
```
Open http://localhost:5173. The Express API runs on http://localhost:3001.

## What works
- Product catalogue with six sample products
- Edit prices, names, pack sizes and optional previous prices
- Four simulated electronic shelf labels
- Assign labels to products
- Explicit publish action: displayed content stays unchanged until published
- Simulated offline / online toggling; offline labels reject publishing
- Pending/synced/offline status, activity history and overview metrics
- Data saved to `server/data/store.json` between server restarts

## API
- `GET /api/state`
- `PATCH /api/products/:id` with e.g. `{ "price": 3.99 }`
- `POST /api/tags/:id/publish`
- `POST /api/tags/:id/assign` with `{ "productId": "p2" }`
- `POST /api/tags/:id/connectivity` with `{ "offline": true }`

## Architecture
- React + Vite frontend
- Express REST API
- JSON file persistence (prototype only)
- Simulated tag display renders the *published snapshot*, not the draft price

## Important limitations
- No real wireless communication, firmware, image transmission, barcode encoding or device acknowledgements
- 'Synced' means the simulator accepted the publish, **not** that a physical screen confirmed receipt
- Battery levels are illustrative, not live readings
- No authentication, multi-store tenancy, rate limiting or concurrency-safe production database
- No unit-price calculations or Australian retail pricing compliance checks
- No payment/POS integration or bulk CSV import yet
- A real device adapter should use queued jobs, retry handling, signed device credentials, and confirmed acknowledgements

## Suggested next milestone
Integrate a single supported ESP32/E-Ink display behind a `DeviceAdapter` interface; keep simulated and real transports interchangeable. Then move storage to SQLite/Postgres and add per-store authentication.


## PencilColour branding and hardware roadmap

Working brand: **PencilColour** (not yet trademark or ASIC cleared).

This demo uses simulated E-Ink tags only. Publishing updates the simulated tag
state; it does not send commands to physical displays.

Next hardware milestone: ESP32 + compatible E-Ink display proof of concept,
with a secure authenticated device API, queued updates, acknowledgement and
retries. Avoid connecting devices to the public unauthenticated demo API.

## Gateway prototype
See `gateway/README.md` for the outbound polling integration and BLE hardware next steps. This prototype does not yet communicate with physical ESL tags.
