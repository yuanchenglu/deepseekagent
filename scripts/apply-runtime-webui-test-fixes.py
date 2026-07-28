#!/usr/bin/env python3
from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding='utf-8')
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{path}: expected exactly one match, found {count}: {old[:120]!r}')
    target.write_text(text.replace(old, new, 1), encoding='utf-8')


path = 'webui/packages/server/src/services/runtime-task-supervisor-client.ts'
replace_once(path, """export async function acquireRuntimeTaskLease(input: AcquireRuntimeTaskLeaseInput): Promise<RuntimeTaskLeaseHandle> {
  const config = supervisorConfig()
  if (!config) {
    return new NoopRuntimeTaskLeaseHandle(
      input.runtime,
      input.taskId,
      input.workspace,
      input.access,
      input.processPid,
    )
  }
  if (input.requireProcess && !input.processPid) {
""", """export async function acquireRuntimeTaskLease(input: AcquireRuntimeTaskLeaseInput): Promise<RuntimeTaskLeaseHandle> {
  const config = supervisorConfig()
  const workspace = String(input.workspace || '').trim()
  if (!config) {
    return new NoopRuntimeTaskLeaseHandle(
      input.runtime,
      input.taskId,
      workspace,
      input.access,
      input.processPid,
    )
  }
  if (!workspace) {
    throw new RuntimeTaskSupervisorError(
      `${input.runtime} task workspace is required`,
      'workspace-required',
      400,
    )
  }
  if (input.requireProcess && !input.processPid) {
""")
replace_once(path, """    workspace: input.workspace,
    access: input.access,
""", """    workspace,
    access: input.access,
""")
replace_once(path, """    input.taskId,
    input.workspace,
    input.access,
""", """    input.taskId,
    workspace,
    input.access,
""")

path = 'webui/packages/server/src/services/hermes/run-chat/handle-coding-agent-run.ts'
replace_once(path, """  const launchProvider = data.provider || (mode === 'scoped' ? storedSession?.provider || undefined : undefined)
  const launchModel = data.model || (mode === 'scoped' ? storedSession?.model || undefined : undefined)
""", """  const launchProvider = data.provider || (mode === 'scoped' ? storedSession?.provider || undefined : undefined)
  const launchModel = data.model || (mode === 'scoped' ? storedSession?.model || undefined : undefined)
  let taskWorkspace = String(storedSession?.workspace || data.workspace || '').trim()
""")
replace_once(path, """    }, state)
    runId = started.agentSessionId
  }
""", """    }, state)
    runId = started.agentSessionId
    taskWorkspace = String(started.workspaceDir || taskWorkspace).trim()
  }
""")
replace_once(path, """  let taskLease: RuntimeTaskLeaseHandle | undefined
  try {
    const taskWorkspace = String(getSession(sessionId)?.workspace || data.workspace || '').trim()
    if (!taskWorkspace) throw new Error('workspace is required for a DeepCode Runtime task')
    taskLease = await acquireRuntimeTaskLease({
""", """  let taskLease: RuntimeTaskLeaseHandle | undefined
  try {
    taskLease = await acquireRuntimeTaskLease({
""")
replace_once(path, """    await sendCodingAgentRunInput(sessionId, inputText, runPrompt, taskLease)
""", """    if (taskLease.enabled) {
      await sendCodingAgentRunInput(sessionId, inputText, runPrompt, taskLease)
    } else {
      await sendCodingAgentRunInput(sessionId, inputText, runPrompt)
    }
""")

path = 'webui/packages/server/src/services/hermes/run-chat/handle-bridge-run.ts'
replace_once(path, """  const resumeWorkspace = String(args.workspace || getSession(sessionId)?.workspace || '').trim()
  if (!resumeWorkspace) throw new Error('workspace is required to resume a DeepAgent Runtime task')
  await acquireBridgeTaskLease(state, sessionId, resumeWorkspace)
""", """  const resumeWorkspace = String(args.workspace || getSession(sessionId)?.workspace || '').trim()
  await acquireBridgeTaskLease(state, sessionId, resumeWorkspace)
""")

path = 'webui/tests/server/coding-agent-run-manager-windows.test.ts'
replace_once(path, """  it('emits a readable failed run when a hidden Claude Code process cannot start', () => {
""", """  it('emits a readable failed run when a hidden Claude Code process cannot start', async () => {
""")
replace_once(path, """    manager.send('chat-session-error-1', 'test')
    testState.spawnCalls[0].child.emit('error', Object.assign(new Error('spawn claude ENOENT'), { code: 'ENOENT' }))

    expect(emitted).toContainEqual(expect.objectContaining({
      event: 'run.failed',
      payload: expect.objectContaining({
        error: 'spawn claude ENOENT',
      }),
    }))
""", """    await manager.send('chat-session-error-1', 'test')
    testState.spawnCalls[0].child.emit('error', Object.assign(new Error('spawn claude ENOENT'), { code: 'ENOENT' }))

    await vi.waitFor(() => {
      expect(emitted).toContainEqual(expect.objectContaining({
        event: 'run.failed',
        payload: expect.objectContaining({
          error: 'spawn claude ENOENT',
        }),
      }))
    })
""")
replace_once(path, """  it('includes decoded stderr detail when a hidden Codex process exits non-zero', () => {
""", """  it('includes decoded stderr detail when a hidden Codex process exits non-zero', async () => {
""")
replace_once(path, """    manager.send('chat-session-codex-error-1', 'test')
    testState.spawnCalls[0].child.stderr.emit('data', Buffer.from([0xb2, 0xbb, 0xca, 0xc7]))
    testState.spawnCalls[0].child.emit('exit', 1)

    expect(emitted).toContainEqual(expect.objectContaining({
      event: 'run.failed',
      payload: expect.objectContaining({
        error: 'Codex exited with code 1: 不是',
      }),
    }))
""", """    await manager.send('chat-session-codex-error-1', 'test')
    testState.spawnCalls[0].child.stderr.emit('data', Buffer.from([0xb2, 0xbb, 0xca, 0xc7]))
    testState.spawnCalls[0].child.emit('exit', 1)

    await vi.waitFor(() => {
      expect(emitted).toContainEqual(expect.objectContaining({
        event: 'run.failed',
        payload: expect.objectContaining({
          error: 'Codex exited with code 1: 不是',
        }),
      }))
    })
""")

print('Runtime WebUI compatibility and async lifecycle tests updated')
