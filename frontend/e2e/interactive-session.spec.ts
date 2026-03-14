import fs from 'node:fs';
import path from 'node:path';

import { expect, test, type Page } from '@playwright/test';

type AuthStatusPayload = {
  authenticated: boolean;
  auth_required?: boolean;
  password_required?: boolean;
};

const HARNESS = 'codex';
const FIXTURE_ARTIFACT_ID = 'rollout-interactive-fixture.jsonl';
const DETAIL_ROUTE = `/sessions/${HARNESS}/${FIXTURE_ARTIFACT_ID}`;
const INTERACTIVE_ROUTE = `${DETAIL_ROUTE}/interactive`;

function getRootEnvValue(name: string): string {
  const envPath = path.resolve(process.cwd(), '..', '.env');
  if (!fs.existsSync(envPath)) {
    return '';
  }

  for (const line of fs.readFileSync(envPath, 'utf8').split('\n')) {
    if (line.startsWith(`${name}=`)) {
      return line.slice(name.length + 1).trim();
    }
  }

  return '';
}

function getLoginPassword(): string {
  return process.env.NEXUS_E2E_PASSWORD
    || process.env.NEXUS_PASSWORD
    || getRootEnvValue('NEXUS_PASSWORD');
}

async function maybeAuthenticate(page: Page): Promise<void> {
  const authResponse = await page.context().request.get('/api/auth/status');
  expect(authResponse.ok()).toBeTruthy();
  const authStatus = await authResponse.json() as AuthStatusPayload;

  if (!authStatus.auth_required || authStatus.authenticated) {
    return;
  }

  const password = getLoginPassword();
  if (!password) {
    throw new Error('NEXUS_E2E_PASSWORD or NEXUS_PASSWORD is required when password auth is enabled');
  }

  const loginResponse = await page.context().request.post('/api/auth/login', {
    data: {
      password,
    },
  });
  expect(loginResponse.ok()).toBeTruthy();
}

async function gotoInteractiveRoute(page: Page): Promise<void> {
  await maybeAuthenticate(page);
  const response = await page.goto(INTERACTIVE_ROUTE, {
    waitUntil: 'domcontentloaded',
  });

  expect(response?.ok()).toBeTruthy();
  await expect(page.getByRole('heading', { name: 'Interactive session shell' })).toBeVisible();
}

test.describe('interactive session browser flow', () => {
  test('tail snapshot shows last messages', async ({ page }) => {
    await gotoInteractiveRoute(page);

    await expect(page).toHaveURL(new RegExp(`${INTERACTIVE_ROUTE.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}$`));
    await expect(page.getByTestId('interactive-live-attach')).toContainText('Live attach ready');
    await expect(page.getByTestId('interactive-timeline-entry-0')).toContainText(
      'Build deterministic fixture for interactive mode',
    );
    await expect(page.getByText('Replay is complete and the route may attach live')).toBeVisible();
  });

  test('detail CTA opens interactive route', async ({ page }) => {
    await maybeAuthenticate(page);
    const response = await page.goto(DETAIL_ROUTE, {
      waitUntil: 'domcontentloaded',
    });

    expect(response?.ok()).toBeTruthy();
    await expect(page.getByTestId('session-detail-page')).toBeVisible();
    await expect(page.getByTestId('session-detail-interactive-cta')).toBeVisible();

    await page.getByTestId('session-detail-interactive-cta').click();

    await expect(page).toHaveURL(new RegExp(`${INTERACTIVE_ROUTE.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}$`));
    await expect(page.getByRole('heading', { name: 'Interactive session shell' })).toBeVisible();
  });

  test('interactive prompt roundtrip', async ({ page }) => {
    await gotoInteractiveRoute(page);

    const promptText = 'Browser continuation prompt from Playwright';
    const promptTimelineEntry = page.locator('[data-testid^="interactive-timeline-entry-"]').filter({
      hasText: promptText,
    }).first();
    await page.getByTestId('interactive-composer-input').fill(promptText);
    await page.getByTestId('interactive-composer-submit').click();

    await expect(promptTimelineEntry).toBeVisible();
    await expect(page.getByText('Browser continuation acknowledged the prompt')).toBeVisible();

    await page.reload({
      waitUntil: 'domcontentloaded',
    });

    await expect(page.getByRole('heading', { name: 'Interactive session shell' })).toBeVisible();
    await expect(page.getByTestId('interactive-live-attach')).toContainText('Reconnecting to runtime');
    await expect(promptTimelineEntry).toBeVisible();
    await expect(page.getByTestId('interactive-live-attach')).toContainText('Live attach ready');
  });
});
