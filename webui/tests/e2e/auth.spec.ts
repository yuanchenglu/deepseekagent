import { expect, test } from '@playwright/test'
import { mockHermesApi } from './fixtures'

test('redirects protected routes to the login screen without a token', async ({ page }) => {
  const api = await mockHermesApi(page)

  await page.goto('/#/hermes/jobs')

  await expect(page).toHaveURL(/#\/$/)
  await expect(page.getByRole('heading', { name: 'DeepAgent Web UI' })).toBeVisible()
  await expect(page.getByPlaceholder('Username')).toBeVisible()
  await expect(page.getByPlaceholder('Password')).toBeVisible()
  expect(api.unexpectedRequests).toEqual([])
})

test('rejects invalid credentials without persisting a token', async ({ page }) => {
  const api = await mockHermesApi(page, { tokenValidationStatus: 401 })

  await page.goto('/')
  await page.getByPlaceholder('Username').fill('playwright')
  await page.getByPlaceholder('Password').fill('bad-password')
  await page.getByRole('button', { name: 'Login' }).click()

  await expect(page.getByText('Invalid username or password')).toBeVisible()
  await expect(page).toHaveURL(/#\/$/)
  await expect(page.evaluate(() => window.localStorage.getItem('hermes_api_key'))).resolves.toBeNull()
  expect(api.unexpectedRequests).toEqual([])
})

test('logs in with password through the BFF before entering the app', async ({ page }) => {
  const api = await mockHermesApi(page)

  await page.goto('/')
  await page.getByPlaceholder('Username').fill('playwright')
  await page.getByPlaceholder('Password').fill('correct-password')
  await page.getByRole('button', { name: 'Login' }).click()

  await expect(page).toHaveURL(/#\/hermes\/chat$/)
  await expect(page.evaluate(() => window.localStorage.getItem('hermes_api_key'))).resolves.toBeNull()
  await expect(page.evaluate(() => window.sessionStorage.getItem('deepagent_cookie_session'))).resolves.not.toBeNull()
  await expect.poll(() => api.requests.some((request) => request.pathname === '/health')).toBe(true)

  const loginRequest = api.requests.find((request) => request.pathname === '/api/auth/login')
  expect(loginRequest?.method).toBe('POST')
  expect(loginRequest?.postData).toBe(JSON.stringify({ username: 'playwright', password: 'correct-password' }))
  expect(api.unexpectedRequests).toEqual([])
})

test('exchanges a one-time ticket without persisting the ticket or JWT', async ({ page }) => {
  const api = await mockHermesApi(page)
  const ticket = 'T'.repeat(43)

  await page.goto(`/#/?ticket=${ticket}`)

  await expect(page).toHaveURL(/#\/hermes\/chat$/)
  await expect(page.evaluate(() => window.localStorage.getItem('hermes_api_key'))).resolves.toBeNull()
  await expect(page.evaluate(() => window.location.href)).resolves.not.toContain(ticket)
  const request = api.requests.find((item) => item.pathname === '/api/auth/ticket')
  expect(request?.postData).toBe(JSON.stringify({ ticket }))
  expect(api.unexpectedRequests).toEqual([])
})
