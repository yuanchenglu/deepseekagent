#!/usr/bin/env python3
from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one match, found {count}: {old[:100]!r}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


path = "webui/packages/server/src/services/hermes/run-chat/handle-coding-agent-run.ts"
replace_once(path, "import type { Server, Socket } from 'socket.io'\n", "import { randomUUID } from 'node:crypto'\nimport type { Server, Socket } from 'socket.io'\n")
replace_once(path, """import { getSystemPrompt } from '../../../lib/llm-prompt'
import { getSession } from '../../../db/hermes/session-store'
""", """import { getSystemPrompt } from '../../../lib/llm-prompt'
import { getSession } from '../../../db/hermes/session-store'
import { acquireRuntimeTaskLease, runtimeTaskId, type RuntimeTaskLeaseHandle } from '../../runtime-task-supervisor-client'
""")
replace_once(path, """  state.isWorking = true
  state.runId = runId

  try {
    const inputText = contentBlocksToString(data.input)
""", """  state.isWorking = true
  state.runId = runId

  let taskLease: RuntimeTaskLeaseHandle | undefined
  try {
    const taskWorkspace = String(getSession(sessionId)?.workspace || data.workspace || '').trim()
    if (!taskWorkspace) throw new Error('workspace is required for a DeepCode Runtime task')
    taskLease = await acquireRuntimeTaskLease({
      runtime: 'deepcode',
      taskId: runtimeTaskId('deepcode', `${sessionId}:${randomUUID()}`),
      workspace: taskWorkspace,
      access: 'write',
    })
    const inputText = contentBlocksToString(data.input)
""")
replace_once(path, """    await sendCodingAgentRunInput(sessionId, inputText, runPrompt)
  } catch (err) {
    if (!codingAgentRunManager.isSessionProcessing(sessionId)) {
""", """    await sendCodingAgentRunInput(sessionId, inputText, runPrompt, taskLease)
  } catch (err) {
    if (taskLease && !codingAgentRunManager.isSessionProcessing(sessionId)) {
      try { await taskLease.finish('failed') } catch { taskLease.abandon() }
    }
    if (!codingAgentRunManager.isSessionProcessing(sessionId)) {
""")

path = "webui/packages/server/src/services/coding-agents.ts"
replace_once(path, """import type { SessionState } from './hermes/run-chat/types'
import { normalizeWindowsCommandPath, windowsCmdShimExecution, windowsCommandNeedsShell, type WindowsCommandExecution } from './windows-command'
""", """import type { SessionState } from './hermes/run-chat/types'
import { normalizeWindowsCommandPath, windowsCmdShimExecution, windowsCommandNeedsShell, type WindowsCommandExecution } from './windows-command'
import { stripRuntimeTaskSupervisorEnvironment, type RuntimeTaskLeaseHandle } from './runtime-task-supervisor-client'
""")
replace_once(path, """function getCurrentNodeEnv(): NodeJS.ProcessEnv {
  return {
    ...process.env,
    PATH: [getNodeBinDir(), getNvmNodeBinPaths(), process.env.PATH].filter(Boolean).join(delimiter),
    npm_node_execpath: process.execPath,
  }
}
""", """function getCurrentNodeEnv(): NodeJS.ProcessEnv {
  return stripRuntimeTaskSupervisorEnvironment({
    ...process.env,
    PATH: [getNodeBinDir(), getNvmNodeBinPaths(), process.env.PATH].filter(Boolean).join(delimiter),
    npm_node_execpath: process.execPath,
  })
}
""")
replace_once(path, """export function sendCodingAgentRunInput(sessionId: string, input: string, systemPrompt?: string): { runId: string } {
  return codingAgentRunManager.send(sessionId, input, { systemPrompt })
}
""", """export function sendCodingAgentRunInput(
  sessionId: string,
  input: string,
  systemPrompt?: string,
  taskLease?: RuntimeTaskLeaseHandle,
): Promise<{ runId: string }> {
  return codingAgentRunManager.send(sessionId, input, { systemPrompt, taskLease })
}
""")

path = "webui/packages/server/src/services/agent-runner/coding-agent-run-manager.ts"
replace_once(path, """import { mapCodingAgentResponseEvent } from './coding-agent-event-mapper'
import { normalizeWindowsCommandPath, windowsCmdShimExecution, windowsCommandNeedsShell } from '../windows-command'
""", """import { mapCodingAgentResponseEvent } from './coding-agent-event-mapper'
import { normalizeWindowsCommandPath, windowsCmdShimExecution, windowsCommandNeedsShell } from '../windows-command'
import { stripRuntimeTaskSupervisorEnvironment, type RuntimeTaskLeaseHandle, type RuntimeTaskOutcome } from '../runtime-task-supervisor-client'
""")
replace_once(path, """  currentChild?: ChildProcess
  currentChildKillTimer?: ReturnType<typeof setTimeout>
""", """  currentChild?: ChildProcess
  currentTaskLease?: RuntimeTaskLeaseHandle
  currentChildKillTimer?: ReturnType<typeof setTimeout>
""")
replace_once(path, """interface CodingAgentRunSendOptions {
  systemPrompt?: string
}
""", """interface CodingAgentRunSendOptions {
  systemPrompt?: string
  taskLease?: RuntimeTaskLeaseHandle
}
""")
replace_once(path, """}): ChildProcess {
  const normalizedCommand = process.platform === 'win32' ? normalizeWindowsCommandPath(command) : command
""", """}): ChildProcess {
  const childEnvironment = stripRuntimeTaskSupervisorEnvironment(options.env)
  const normalizedCommand = process.platform === 'win32' ? normalizeWindowsCommandPath(command) : command
""")
replace_once(path, "      env: options.env,\n", "      env: childEnvironment,\n")
replace_once(path, "    env: options.env,\n", "    env: childEnvironment,\n")
replace_once(path, """  send(sessionId: string, input: string, options: CodingAgentRunSendOptions = {}): { runId: string } {
""", """  async send(sessionId: string, input: string, options: CodingAgentRunSendOptions = {}): Promise<{ runId: string }> {
""")
replace_once(path, """    if (run.launch.agentId === 'claude-code') {
      this.startClaudePrintTurn(run, text, systemPrompt)
      return { runId: run.id }
    }
    if (run.launch.agentId === 'codex') {
      this.startCodexExecTurn(run, text, systemPrompt)
""", """    if (run.launch.agentId === 'claude-code') {
      await this.startClaudePrintTurn(run, text, systemPrompt, options.taskLease)
      return { runId: run.id }
    }
    if (run.launch.agentId === 'codex') {
      await this.startCodexExecTurn(run, text, systemPrompt, options.taskLease)
""")
replace_once(path, """  private startClaudePrintTurn(run: ManagedCodingAgentRun, input: string, systemPrompt = '') {
""", """  private async finishTaskLease(run: ManagedCodingAgentRun, outcome: RuntimeTaskOutcome): Promise<void> {
    const lease = run.currentTaskLease
    run.currentTaskLease = undefined
    if (!lease) return
    try {
      await lease.finish(outcome)
    } catch (err) {
      lease.abandon()
      logger.warn({ err, runId: run.id, sessionId: run.launch.sessionId, outcome }, '[coding-agent-run] failed to finish DeepCode Runtime task lease')
    }
  }

  private async processTaskLeaseExit(run: ManagedCodingAgentRun, code: number | null, signal: NodeJS.Signals | null): Promise<void> {
    const lease = run.currentTaskLease
    run.currentTaskLease = undefined
    if (!lease) return
    try {
      await lease.processExit(code, signal)
    } catch (err) {
      lease.abandon()
      logger.warn({ err, runId: run.id, sessionId: run.launch.sessionId, code, signal }, '[coding-agent-run] failed to record DeepCode process exit')
    }
  }

  private async bindTaskLease(run: ManagedCodingAgentRun, child: ChildProcess, lease?: RuntimeTaskLeaseHandle): Promise<void> {
    if (!lease) return
    run.currentTaskLease = lease
    if (!child.pid) throw new Error('Coding agent child did not publish a PID')
    try {
      await lease.bindProcess(child.pid)
    } catch (err) {
      terminateChildProcess(child)
      await this.finishTaskLease(run, 'failed')
      throw err
    }
  }

  private async startClaudePrintTurn(run: ManagedCodingAgentRun, input: string, systemPrompt = '', taskLease?: RuntimeTaskLeaseHandle): Promise<void> {
""")
replace_once(path, """    })
    run.currentChild = child

    let stdoutBuffer = ''
""", """    })
    run.currentChild = child
    run.currentTaskLease = taskLease

    let stdoutBuffer = ''
""")
replace_once(path, """    child.on('error', (err) => {
      if (run.currentChildKillTimer) clearTimeout(run.currentChildKillTimer)
      run.currentChildKillTimer = undefined
      run.currentChild = undefined
      logger.warn({ err, runId: run.id, sessionId: run.launch.sessionId }, '[coding-agent-run] claude print failed to start')
      this.handleClaudePrintResponseEvent(run, {
        type: 'response.failed',
        data: {
          type: 'response.failed',
          response: {
            id: run.printResponseId,
            object: 'response',
            status: 'failed',
            model: run.launch.model,
            error: { message: childProcessErrorMessage(err) },
            output: [],
          },
        },
      })
    })

    child.on('exit', (code) => {
      if (stdoutBuffer.trim()) this.handleClaudePrintLine(run, stdoutBuffer)
      if (run.currentChildKillTimer) clearTimeout(run.currentChildKillTimer)
      run.currentChildKillTimer = undefined
      run.currentChild = undefined
      logger.info({ runId: run.id, sessionId: run.launch.sessionId, code }, '[coding-agent-run] claude print exited')
      if (run.stoppedByUser) return
      if (run.pendingChatCompletionEvent) {
        this.emitAndMarkPrintChatRunCompleted(run, run.pendingChatCompletionEvent, run.pendingChatCompletionPayload)
        return
      }
      if (code === 0) {
        this.completeClaudePrintTurn(run)
        return
      }
      this.handleClaudePrintResponseEvent(run, {
        type: 'response.failed',
        data: {
          type: 'response.failed',
          response: {
            id: run.printResponseId,
            object: 'response',
            status: 'failed',
            model: run.launch.model,
            error: { message: exitErrorMessage('Claude Code', code, run.currentChildStderr) },
            output: [],
          },
        },
      })
    })
  }
""", """    child.on('error', (err) => {
      void this.finishTaskLease(run, 'failed').finally(() => {
        if (run.currentChildKillTimer) clearTimeout(run.currentChildKillTimer)
        run.currentChildKillTimer = undefined
        run.currentChild = undefined
        logger.warn({ err, runId: run.id, sessionId: run.launch.sessionId }, '[coding-agent-run] claude print failed to start')
        this.handleClaudePrintResponseEvent(run, {
          type: 'response.failed',
          data: {
            type: 'response.failed',
            response: {
              id: run.printResponseId,
              object: 'response',
              status: 'failed',
              model: run.launch.model,
              error: { message: childProcessErrorMessage(err) },
              output: [],
            },
          },
        })
      })
    })

    child.on('exit', (code, signal) => {
      void this.processTaskLeaseExit(run, code, signal).finally(() => {
        if (stdoutBuffer.trim()) this.handleClaudePrintLine(run, stdoutBuffer)
        if (run.currentChildKillTimer) clearTimeout(run.currentChildKillTimer)
        run.currentChildKillTimer = undefined
        run.currentChild = undefined
        logger.info({ runId: run.id, sessionId: run.launch.sessionId, code, signal }, '[coding-agent-run] claude print exited')
        if (run.stoppedByUser) return
        if (run.pendingChatCompletionEvent) {
          this.emitAndMarkPrintChatRunCompleted(run, run.pendingChatCompletionEvent, run.pendingChatCompletionPayload)
          return
        }
        if (code === 0) {
          this.completeClaudePrintTurn(run)
          return
        }
        this.handleClaudePrintResponseEvent(run, {
          type: 'response.failed',
          data: {
            type: 'response.failed',
            response: {
              id: run.printResponseId,
              object: 'response',
              status: 'failed',
              model: run.launch.model,
              error: { message: exitErrorMessage('Claude Code', code, run.currentChildStderr) },
              output: [],
            },
          },
        })
      })
    })
    await this.bindTaskLease(run, child, taskLease)
  }
""")
replace_once(path, """  private startCodexExecTurn(run: ManagedCodingAgentRun, input: string, systemPrompt = '') {
""", """  private async startCodexExecTurn(run: ManagedCodingAgentRun, input: string, systemPrompt = '', taskLease?: RuntimeTaskLeaseHandle): Promise<void> {
""")
replace_once(path, """    })
    run.currentChild = child

    let stdoutBuffer = ''
""", """    })
    run.currentChild = child
    run.currentTaskLease = taskLease

    let stdoutBuffer = ''
""")
replace_once(path, """    child.on('error', (err) => {
      if (run.currentChildKillTimer) clearTimeout(run.currentChildKillTimer)
      run.currentChildKillTimer = undefined
      run.currentChild = undefined
      logger.warn({ err, runId: run.id, sessionId: run.launch.sessionId }, '[coding-agent-run] codex exec failed to start')
      this.handleClaudePrintResponseEvent(run, {
        type: 'response.failed',
        data: {
          type: 'response.failed',
          response: {
            id: run.printResponseId,
            object: 'response',
            status: 'failed',
            model: run.launch.model,
            error: { message: childProcessErrorMessage(err) },
            output: [],
          },
        },
      })
    })

    child.on('exit', (code) => {
      if (stdoutBuffer.trim()) this.handleCodexExecLine(run, stdoutBuffer)
      if (run.currentChildKillTimer) clearTimeout(run.currentChildKillTimer)
      run.currentChildKillTimer = undefined
      run.currentChild = undefined
      logger.info({ runId: run.id, sessionId: run.launch.sessionId, code }, '[coding-agent-run] codex exec exited')
      if (run.stoppedByUser) return
      if (run.pendingChatCompletionEvent) {
        this.emitAndMarkPrintChatRunCompleted(run, run.pendingChatCompletionEvent, run.pendingChatCompletionPayload)
        return
      }
      if (code === 0) {
        this.completeCodexExecTurn(run, run.codexPendingUsage)
        return
      }
      this.handleClaudePrintResponseEvent(run, {
        type: 'response.failed',
        data: {
          type: 'response.failed',
          response: {
            id: run.printResponseId,
            object: 'response',
            status: 'failed',
            model: run.launch.model,
            error: { message: exitErrorMessage('Codex', code, run.currentChildStderr) },
            output: [],
          },
        },
      })
    })
  }
""", """    child.on('error', (err) => {
      void this.finishTaskLease(run, 'failed').finally(() => {
        if (run.currentChildKillTimer) clearTimeout(run.currentChildKillTimer)
        run.currentChildKillTimer = undefined
        run.currentChild = undefined
        logger.warn({ err, runId: run.id, sessionId: run.launch.sessionId }, '[coding-agent-run] codex exec failed to start')
        this.handleClaudePrintResponseEvent(run, {
          type: 'response.failed',
          data: {
            type: 'response.failed',
            response: {
              id: run.printResponseId,
              object: 'response',
              status: 'failed',
              model: run.launch.model,
              error: { message: childProcessErrorMessage(err) },
              output: [],
            },
          },
        })
      })
    })

    child.on('exit', (code, signal) => {
      void this.processTaskLeaseExit(run, code, signal).finally(() => {
        if (stdoutBuffer.trim()) this.handleCodexExecLine(run, stdoutBuffer)
        if (run.currentChildKillTimer) clearTimeout(run.currentChildKillTimer)
        run.currentChildKillTimer = undefined
        run.currentChild = undefined
        logger.info({ runId: run.id, sessionId: run.launch.sessionId, code, signal }, '[coding-agent-run] codex exec exited')
        if (run.stoppedByUser) return
        if (run.pendingChatCompletionEvent) {
          this.emitAndMarkPrintChatRunCompleted(run, run.pendingChatCompletionEvent, run.pendingChatCompletionPayload)
          return
        }
        if (code === 0) {
          this.completeCodexExecTurn(run, run.codexPendingUsage)
          return
        }
        this.handleClaudePrintResponseEvent(run, {
          type: 'response.failed',
          data: {
            type: 'response.failed',
            response: {
              id: run.printResponseId,
              object: 'response',
              status: 'failed',
              model: run.launch.model,
              error: { message: exitErrorMessage('Codex', code, run.currentChildStderr) },
              output: [],
            },
          },
        })
      })
    })
    await this.bindTaskLease(run, child, taskLease)
  }
""")

print("DeepCode child task lifecycle transformed")
