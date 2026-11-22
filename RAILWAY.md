# Railway deployment

1. Push this folder to a GitHub repository.
2. In Railway create a project > Deploy from GitHub repo. Railway detects the root Dockerfile.
3. Add a volume to the service and mount it at `/data`.
4. Set `DATA_DIR=/data` in service variables.
5. In Networking generate a public domain. Railway supplies `PORT` automatically.
6. Visit the URL and test editing a product, publishing a tag, then redeploying and checking persistence.

The React frontend and Express API are served by one service. Local dev still works with `npm run install:all` then `npm run dev`.

IMPORTANT: This is a public, unauthenticated demo with simulated tags and local JSON storage. Do not use for real retailer pricing or sensitive data. Add authentication, audit trails and a database before production. Run only one service replica with this JSON storage approach.
