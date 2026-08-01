import { expect, test } from '@playwright/test'

const source = '#include <iostream>\nint main(){int a,b;std::cin>>a>>b;std::cout<<a+b;}'

test('student can register, submit, see a result and appear on the leaderboard', async ({ page }) => {
  const suffix = Date.now()
  await page.goto('/register')
  await page.locator('#reg-name').fill('E2E 学生')
  await page.locator('#reg-username').fill(`e2e_${suffix}`)
  await page.locator('#reg-email').fill(`e2e_${suffix}@example.test`)
  await page.locator('#reg-password').fill('correct-horse-battery')
  await page.getByRole('button', { name: '创建账号' }).click()
  await expect(page.getByRole('heading', { name: /你好，E2E 学生/ })).toBeVisible()
  const seededProblem = await page.request.get('/api/problems/1')
  await expect(seededProblem).toBeOK()
  await page.goto('/problems/1')
  await expect(page.locator('.cm-content')).toBeVisible()
  await page.locator('.cm-content').fill(source)
  await page.getByRole('button', { name: '提交评测' }).click()
  await expect(page.getByRole('heading', { name: '答案正确' })).toBeVisible({ timeout: 25_000 })
  await page.goto('/leaderboard')
  await expect(page.getByText(`@e2e_${suffix}`)).toBeVisible()
})

test('student is denied sensitive API access and public data remains redacted', async ({ page }) => {
  await page.goto('/login')
  await page.locator('#login-username').fill('demo_student')
  await page.locator('#login-password').fill('ojcampus-demo')
  await page.getByRole('button', { name: '登录' }).click()
  await expect(page).toHaveURL(/\/dashboard$/)
  await page.goto('/admin')
  await expect(page).toHaveURL(/\/dashboard$/)
  const protectedResults = await page.evaluate(async () => Promise.all([
    fetch('/api/admin/dashboard', { credentials: 'include' }),
    fetch('/api/admin/problems', { credentials: 'include' }),
  ]).then(async ([dashboard, problems]) => ({ dashboard: dashboard.status, problems: problems.status })))
  expect(protectedResults).toEqual({ dashboard: 403, problems: 403 })
  const [me, publicBody] = await page.evaluate(() => Promise.all([
    fetch('/api/auth/me', { credentials: 'include' }).then((response) => response.json()),
    fetch('/api/submissions/public', { credentials: 'include' }).then((response) => response.json()),
  ])) as [{ id: number }, { items: Array<Record<string, unknown>> }]
  const otherSubmission = publicBody.items.find((item) => item.user_id !== me.id)
  expect(otherSubmission).toBeTruthy()
  expect(otherSubmission).not.toHaveProperty('source')
  expect(otherSubmission).not.toHaveProperty('details')
  const otherDetail = await page.evaluate((id) => fetch(`/api/submissions/${id}`, { credentials: 'include' }).then(async (response) => ({ status: response.status, body: await response.json() })), otherSubmission?.id)
  expect(otherDetail.status).toBe(403)
  expect(otherDetail.body).not.toHaveProperty('source')
})

test('admin creates a published hidden-case problem that a student can solve', async ({ page }) => {
  const title = `E2E 隐藏用例题 ${Date.now()}`
  await page.goto('/login')
  await page.locator('#login-username').fill('demo_admin')
  await page.locator('#login-password').fill('ojcampus-demo')
  await page.getByRole('button', { name: '登录' }).click()
  await expect(page).toHaveURL(/\/admin$/)
  await page.goto('/admin/problems/new')
  await page.locator('#problem-title').fill(title)
  await page.locator('#statement').fill('输出输入的整数。')
  await page.locator('#case-in-0').fill('1\n')
  await page.locator('#case-out-0').fill('1\n')
  await page.getByRole('button', { name: '添加测试点' }).click()
  await page.locator('#case-in-1').fill('7\n')
  await page.locator('#case-out-1').fill('7\n')
  await page.getByLabel('保存后立即发布').check()
  await page.getByRole('button', { name: '保存题目' }).click()
  await expect(page.getByText(title)).toBeVisible()
  const response = await page.request.get('/api/admin/problems')
  const problems = await response.json() as Array<{ id: number; title: string; published: boolean; test_cases: Array<{ is_sample: boolean }> }>
  const created = problems.find((problem) => problem.title === title)
  expect(created?.published).toBe(true)
  expect(created?.test_cases).toEqual([
    { is_sample: true, input: '1\n', output: '1\n', position: 1 },
    { is_sample: false, input: '7\n', output: '7\n', position: 2 },
  ])
  const problemId = created?.id
  expect(problemId).toBeTruthy()
  await page.getByRole('button', { name: '退出登录' }).click()
  await expect(page).toHaveURL(/\/login$/)
  await page.locator('#login-username').fill('demo_student')
  await page.locator('#login-password').fill('ojcampus-demo')
  await page.getByRole('button', { name: '登录' }).click()
  await expect(page).toHaveURL(/\/dashboard$/)
  const publicProblem = await page.evaluate((id) => fetch(`/api/problems/${id}`, { credentials: 'include' }).then((result) => result.json()), problemId)
  expect(publicProblem.test_cases).toEqual([{ input: '1\n', output: '1\n', is_sample: true, position: 1 }])
  await page.goto(`/problems/${problemId}`)
  await page.locator('.cm-content').fill('#include <iostream>\nint main(){int n;std::cin>>n;std::cout<<n;}')
  await page.getByRole('button', { name: '提交评测' }).click()
  await expect(page.getByRole('heading', { name: '答案正确' })).toBeVisible({ timeout: 25_000 })
})
