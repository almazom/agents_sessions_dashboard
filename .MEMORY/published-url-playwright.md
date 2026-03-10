# Memory Card: Published URL And Playwright

Use this card when:

- a task changes visible UI
- a task changes auth, routing, hydration, or API payloads
- a task changes `public/` assets or branding
- you are about to ask the user to test the published app

Goal:
- verify the real published deployment, not just local HTML

Published URL:
- use the published URL from `.env`
- for this project that means `http://${NEXUS_PUBLIC_HOST}:${NEXUS_PUBLIC_PORT}`

Major-change rule:
- local build is not enough
- restart the published stack after major changes
- run Playwright yourself before asking the user to test

Minimal sequence:

1. run local verification
2. run `./start_published.sh`
3. verify backend/frontend health endpoints
4. open the published URL in Playwright
5. verify auth flow, hydration, and critical API calls
6. collect screenshots when visual review matters
7. send screenshots through `t2me` unless the user explicitly opted out

Visual smoke shortcut:

```bash
cd frontend
npm run smoke:published:visual
```

The visual smoke pipeline sends step screenshots through `t2me` by default.

Green check conditions:
- page status is `200`
- loading spinner count becomes `0`
- critical API calls return `200`
- failed requests array is empty
- visible page state matches the intended mode

Important browser rules:
- open the real published URL, not just localhost
- wait for hydration, not only the first HTML response
- record API responses and failed requests
- do not close the task while the published page is stale or stuck on loading

Minimal Playwright pattern:

```js
const apiRequests = [];
const failedRequests = [];

page.on('response', (res) => {
  if (res.url().includes('/api/')) apiRequests.push(`${res.status()} ${res.url()}`);
});

page.on('requestfailed', (req) => {
  failedRequests.push(`${req.method()} ${req.url()} :: ${req.failure()?.errorText}`);
});

const response = await page.goto(publicUrl, { waitUntil: 'domcontentloaded' });
await page.waitForTimeout(4000);

expect(response?.status()).toBe(200);
expect(await page.getByText('⏳ Загрузка...').count()).toBe(0);
expect(failedRequests).toEqual([]);
expect(apiRequests.some((item) => item.startsWith('200 '))).toBe(true);
```

Project-specific tip:
- if the page is in expanded dashboard mode, check that section headers like `Активные`, `Ошибки`, `Завершённые` are present after load
- if the page is in latest-only mode, check that the single latest card is visible and dashboard sections stay hidden until filters change
