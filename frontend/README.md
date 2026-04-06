# Frontend

## Local Run

```bash
npm install
npm run dev
```

Dev server starts on the standard Next.js port unless `PORT` is overridden.

For Docker-based local development, `deploy/docker-compose.dev.yml` mounts `.next` into a named volume. This isolates build cache from the host workspace and avoids stale lock/owner issues after switching between container and local runs.

## Performance Debugging

Set `NEXT_PUBLIC_PERF_DEBUG=1` to emit request timing logs from the shared axios client. This is intended for local diagnostics of admin flows such as `groups -> group -> student`.

Example:

```bash
NEXT_PUBLIC_PERF_DEBUG=1 npm run dev
```

The logger records:

- request method
- request URL
- response status
- duration in milliseconds

## Smoke Tests

Run the admin smoke suite with:

```bash
npm run build
npm run test:smoke
```

`test:smoke` starts the production build through `scripts/start-smoke.mjs`, which prepares the standalone output for Playwright by linking required static assets before booting the server.

## Related Backend Perf Flags

The frontend perf flow added matching backend flags for local profiling:

- `API_SLOW_ROUTE_MS`
- `SQL_SLOW_QUERY_MS`

When these are greater than `0`, backend logs will report slow HTTP routes and SQL queries.
