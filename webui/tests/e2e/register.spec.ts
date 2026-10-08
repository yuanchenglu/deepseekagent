import { expect, test } from '@playwright/test'
import { mockHermesApi } from './fixtures'

test('shows the create account link on the login screen when registration is enabled', async ({ page }) => {
  await mockHermesApi(page)

  await page.goto('/')

  await expect(page.getByRole('link', { name: 'Create account' })).toBeVisible()
})

test('registers an account and enters the app', async ({ page }) => {
  const api = await mockHermesApi(page)

  await page.goto('/')
  await page.getByRole('link', { name: 'Create account' }).click()

  await expect(page).toHaveURL(/#\/register$/)
  await expect(page.getByPlaceholder('Username')).toBeVisible()

  await page.getByPlaceholder('Username').fill('alice')
  await page.getByPlaceholder('Password', { exact: true }).fill('secret123')
  await page.getByPlaceholder('Confirm Password').fill('secret123')
  await page.getByRole('button', { name: 'Create Account' }).click()

  await expect(page).toHaveURL(/#\/hermes\/chat$/)
  await expect(page.evaluate(() => window.sessionStorage.getItem('deepagent_cookie_session'))).resolves.not.toBeNull()

  const registerRequest = api.requests.find((request) => request.pathname === '/api/auth/register')
  expect(registerRequest?.method).toBe('POST')
  expect(registerRequest?.postData).toBe(JSON.stringify({ username: 'alice', password: 'secret123' }))
  expect(api.unexpectedRequests).toEqual([])
})

test('rejects a username that is already registered', async ({ page }) => {
  await mockHermesApi(page)

  await page.goto('/#/register')
  await page.getByPlaceholder('Username').fill('playwright')
  await page.getByPlaceholder('Password', { exact: true }).fill('secret123')
  await page.getByPlaceholder('Confirm Password').fill('secret123')
  await page.getByRole('button', { name: 'Create Account' }).click()

  await expect(page.getByText('Username already exists')).toBeVisible()
  await expect(page).toHaveURL(/#\/register$/)
})
