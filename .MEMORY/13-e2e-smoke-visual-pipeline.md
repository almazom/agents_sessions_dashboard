# Memory Card: E2E Smoke Visual Pipeline

Use this card when:

- you need a quick published smoke test with screenshots
- you need step-by-step browser evidence
- you need to send Playwright screenshots to the user through `t2me`

Command:

```bash
cd frontend
npm run smoke:published:visual
```

Make shortcuts:

```bash
make e2e-smoke
make e2e-login
make e2e-smoke-confidence
make e2e-login-confidence
```

What it does:

1. opens the published URL
2. captures the first visible state
3. logs in if the password gate is shown
4. captures the latest-only landing state
5. expands the dashboard by changing a filter
6. captures the first session card if cards are visible
7. writes a JSON summary to `tmp/e2e-smoke/run-*/summary.json`

Default behavior:

- uses the published URL from `.env`
- sends Playwright screenshots through `t2me` if available
- expands the dashboard after the latest-only state

Useful env flags:

- `NEXUS_E2E_SEND_T2ME=0` to skip Telegram file sends
- `NEXUS_E2E_EXPAND_DASHBOARD=0` to stop after the latest-only state
- `NEXUS_PLAYWRIGHT_TIMEOUT_MS=45000` to increase timeouts

Output:

- step-by-step terminal logs
- JPEG screenshots under `tmp/e2e-smoke/run-*`
- JSON summary with steps, API responses, failed requests, and screenshot metadata
