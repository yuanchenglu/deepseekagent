#!/usr/bin/env python3
from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one match, found {count}: {old[:100]!r}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


path = "webui/packages/server/src/services/hermes/agent-bridge/manager.ts"
replace_once(path, """import { detectHermesHome, getHermesBin } from '../hermes-path'
import { AgentBridgeClient, DEFAULT_AGENT_BRIDGE_ENDPOINT } from './client'
""", """import { detectHermesHome, getHermesBin } from '../hermes-path'
import { AgentBridgeClient, DEFAULT_AGENT_BRIDGE_ENDPOINT } from './client'
import { stripRuntimeTaskSupervisorEnvironment } from '../../runtime-task-supervisor-client'
""")
replace_once(path, """  const env: NodeJS.ProcessEnv = {
    ...process.env,
    HERMES_AGENT_BRIDGE_ENDPOINT: endpoint,
""", """  const env: NodeJS.ProcessEnv = stripRuntimeTaskSupervisorEnvironment({
    ...process.env,
    HERMES_AGENT_BRIDGE_ENDPOINT: endpoint,
""")
replace_once(path, """    ...(agentRoot ? { HERMES_AGENT_ROOT: agentRoot } : {}),
  }
  delete env.ANTHROPIC_AUTH_TOKEN
""", """    ...(agentRoot ? { HERMES_AGENT_ROOT: agentRoot } : {}),
  })
  delete env.ANTHROPIC_AUTH_TOKEN
""")
replace_once(path, """function classifyEndpointKind(endpoint: string): AgentBridgeEndpointKind {
  if (endpoint.startsWith('ipc://')) return 'ipc'
  if (endpoint.startsWith('tcp://')) return 'tcp'
  return 'unknown'
}

""", """function classifyEndpointKind(endpoint: string): AgentBridgeEndpointKind {
  if (endpoint.startsWith('ipc://')) return 'ipc'
  if (endpoint.startsWith('tcp://')) return 'tcp'
  return 'unknown'
}

function endpointProcessPid(endpoint: string): number | null {
  if (process.platform === 'win32') return null
  let output = ''
  try {
    if (endpoint.startsWith('ipc://')) {
      output = execFileSync('lsof', ['-t', '-U', '--', endpoint.slice('ipc://'.length)], {
        encoding: 'utf8',
        timeout: 5_000,
        stdio: ['ignore', 'pipe', 'ignore'],
      })
    } else if (endpoint.startsWith('tcp://')) {
      const port = Number(new URL(endpoint).port)
      if (!Number.isSafeInteger(port) || port <= 0) return null
      output = execFileSync('lsof', [`-tiTCP:${port}`, '-sTCP:LISTEN'], {
        encoding: 'utf8',
        timeout: 5_000,
        stdio: ['ignore', 'pipe', 'ignore'],
      })
    } else {
      return null
    }
  } catch {
    return null
  }
  for (const line of output.split(/\\r?\\n/)) {
    const pid = Number(line.trim())
    if (!Number.isSafeInteger(pid) || pid <= 0) continue
    try {
      const command = execFileSync('ps', ['-p', String(pid), '-o', 'command='], {
        encoding: 'utf8',
        timeout: 5_000,
        stdio: ['ignore', 'pipe', 'ignore'],
      }).trim()
      if (command.includes('hermes_bridge.py') && command.includes(endpoint)) return pid
    } catch {}
  }
  return null
}

""")
replace_once(path, """  getRuntimeState(): AgentBridgeManagerRuntimeState {
    return {
      endpoint: this.endpoint,
      running: this.running,
      ready: this.ready,
      attached: this.attached,
      pid: this.child?.pid,
      starting: !!this.starting,
      stopping: this.stopping,
      restartScheduled: !!this.restartTimer,
      restartAttempts: this.restartAttempts,
    }
  }

""", """  getRuntimeState(): AgentBridgeManagerRuntimeState {
    return {
      endpoint: this.endpoint,
      running: this.running,
      ready: this.ready,
      attached: this.attached,
      pid: this.child?.pid,
      starting: !!this.starting,
      stopping: this.stopping,
      restartScheduled: !!this.restartTimer,
      restartAttempts: this.restartAttempts,
    }
  }

  getTaskProcessPid(): number | null {
    const childPid = this.child?.pid
    if (childPid && this.child?.exitCode == null && this.child?.signalCode == null) return childPid
    if (!this.ready && !this.attached) return null
    return endpointProcessPid(this.endpoint)
  }

""")

path = "webui/packages/server/src/services/hermes/run-chat/types.ts"
replace_once(path, "import type { ChatMessage } from '../../../lib/context-compressor'\n", "import type { ChatMessage } from '../../../lib/context-compressor'\nimport type { RuntimeTaskLeaseHandle } from '../../runtime-task-supervisor-client'\n")
replace_once(path, """  abortController?: AbortController
  runId?: string
""", """  abortController?: AbortController
  runtimeTaskLease?: RuntimeTaskLeaseHandle
  runId?: string
""")

path = "webui/packages/server/src/services/hermes/run-chat/handle-bridge-run.ts"
replace_once(path, """import { AgentBridgeClient, type AgentBridgeContextEstimate, type AgentBridgeMessage, type AgentBridgeOutput } from '../agent-bridge'
""", """import { AgentBridgeClient, type AgentBridgeContextEstimate, type AgentBridgeMessage, type AgentBridgeOutput } from '../agent-bridge'
import { getAgentBridgeManager } from '../agent-bridge/manager'
""")
replace_once(path, """import { ensureHermesRunWorkspace } from './workspace'
import { observeRunChatPetEvent } from '../pet-state-socket'
""", """import { ensureHermesRunWorkspace } from './workspace'
import { observeRunChatPetEvent } from '../pet-state-socket'
import { acquireRuntimeTaskLease, runtimeTaskId, type RuntimeTaskOutcome } from '../../runtime-task-supervisor-client'
""")
replace_once(path, """const BRIDGE_GOAL_EVALUATE_TIMEOUT_MS = 120_000

""", """const BRIDGE_GOAL_EVALUATE_TIMEOUT_MS = 120_000

async function acquireBridgeTaskLease(state: SessionState, sessionId: string, workspace: string): Promise<void> {
  if (state.runtimeTaskLease) return
  const processPid = getAgentBridgeManager().getTaskProcessPid()
  state.runtimeTaskLease = await acquireRuntimeTaskLease({
    runtime: 'deepagent',
    taskId: runtimeTaskId('deepagent', sessionId),
    workspace,
    access: 'write',
    processPid: processPid || undefined,
    requireProcess: true,
  })
}

async function finishBridgeTaskLease(state: SessionState, outcome: RuntimeTaskOutcome): Promise<void> {
  const lease = state.runtimeTaskLease
  state.runtimeTaskLease = undefined
  if (!lease) return
  try {
    await lease.finish(outcome)
  } catch (err) {
    lease.abandon()
    bridgeLogger.warn({
      err: err instanceof Error ? { message: err.message, name: err.name } : err,
      runtime: lease.runtime,
      taskId: lease.taskId,
      outcome,
    }, '[chat-run-socket] failed to finish DeepAgent Runtime task lease')
  }
}

function bridgeTaskOutcome(chunk: AgentBridgeOutput): RuntimeTaskOutcome {
  if (chunk.status === 'interrupted') return 'cancelled'
  return bridgeTerminalError(chunk) ? 'failed' : 'completed'
}

""")
replace_once(path, """  try {
    const bridgeInput = isContentBlockArray(input)
""", """  try {
    await acquireBridgeTaskLease(state, session_id, workspace)
    const bridgeInput = isContentBlockArray(input)
""")
replace_once(path, """      if (chunk.done) {
        sawTerminalChunk = true
        void pollBridgeGeneratedTitleAfterRun(bridge, session_id, profile, emit)
""", """      if (chunk.done) {
        sawTerminalChunk = true
        await finishBridgeTaskLease(state, bridgeTaskOutcome(chunk))
        void pollBridgeGeneratedTitleAfterRun(bridge, session_id, profile, emit)
""")
replace_once(path, """        data.model_groups,
      )
    }
  } catch (err: any) {
""", """        data.model_groups,
      )
      await finishBridgeTaskLease(state, bridgeTaskOutcome(terminalChunk))
    }
  } catch (err: any) {
    await finishBridgeTaskLease(state, 'failed')
""")
replace_once(path, """  state.bridgePendingTools = state.bridgePendingTools || []
  state.bridgeToolCounter = state.bridgeToolCounter || 0

  const emit = (event: string, payload: any) => {
""", """  state.bridgePendingTools = state.bridgePendingTools || []
  state.bridgeToolCounter = state.bridgeToolCounter || 0

  const resumeWorkspace = String(args.workspace || getSession(sessionId)?.workspace || '').trim()
  if (!resumeWorkspace) throw new Error('workspace is required to resume a DeepAgent Runtime task')
  await acquireBridgeTaskLease(state, sessionId, resumeWorkspace)

  const emit = (event: string, payload: any) => {
""")
replace_once(path, """      if (chunk.done) return
      await delay(100)
    }
  } catch (err) {
""", """      if (chunk.done) {
        await finishBridgeTaskLease(state, bridgeTaskOutcome(chunk))
        return
      }
      await delay(100)
    }
  } catch (err) {
    await finishBridgeTaskLease(state, 'failed')
""")

path = "webui/packages/server/src/services/hermes/run-chat/abort.ts"
replace_once(path, """  if (isBridgeRunSource(activeState.source)) {
    let interruptResult: any = null
    try {
      interruptResult = await bridge.interrupt(sessionId, 'Aborted by user', activeState.profile)
    } catch (err) {
      logger.warn(err, '[chat-run-socket][abort] failed to interrupt CLI bridge for session %s', sessionId)
    }
    try {
      await bridge.goalPause?.(sessionId, 'user-interrupted', activeState.profile)
      activeState.queue = activeState.queue.filter(item => !item.goalContinuation)
    } catch (err) {
      logger.debug(err, '[chat-run-socket][abort] goal pause-on-interrupt skipped for session %s', sessionId)
    }
    if (interruptResult?.synced === false) {
      replaceState(sessionMap, sessionId, 'abort.timeout', {
        event: 'abort.timeout',
        run_id: runId,
        synced: false,
        message: ABORT_BRIDGE_SYNC_TIMEOUT_MESSAGE,
      })
      emitToSession(nsp, socket, sessionId, 'abort.timeout', {
        event: 'abort.timeout',
        run_id: runId,
        synced: false,
        message: ABORT_BRIDGE_SYNC_TIMEOUT_MESSAGE,
      })
      logger.warn({ sessionId, runId }, '[chat-run-socket][abort] CLI bridge interrupt did not sync before timeout')
      try {
        await bridge.destroy?.(sessionId, activeState.profile)
      } catch (err) {
        logger.warn(err, '[chat-run-socket][abort] failed to destroy timed-out CLI bridge session %s', sessionId)
      }
      await markAbortCompleted(nsp, socket, sessionId, runId || 'bridge_abort_timeout', sessionMap, runQueuedItem, false)
      return
    }
  } else if (activeState.source === 'coding_agent') {
""", """  if (isBridgeRunSource(activeState.source)) {
    let cancellationConfirmed = false
    let interruptResult: any = null
    try {
      interruptResult = await bridge.interrupt(sessionId, 'Aborted by user', activeState.profile)
      cancellationConfirmed = interruptResult?.synced !== false
    } catch (err) {
      logger.warn(err, '[chat-run-socket][abort] failed to interrupt CLI bridge for session %s', sessionId)
    }
    try {
      await bridge.goalPause?.(sessionId, 'user-interrupted', activeState.profile)
      activeState.queue = activeState.queue.filter(item => !item.goalContinuation)
    } catch (err) {
      logger.debug(err, '[chat-run-socket][abort] goal pause-on-interrupt skipped for session %s', sessionId)
    }
    if (interruptResult?.synced === false) {
      replaceState(sessionMap, sessionId, 'abort.timeout', {
        event: 'abort.timeout',
        run_id: runId,
        synced: false,
        message: ABORT_BRIDGE_SYNC_TIMEOUT_MESSAGE,
      })
      emitToSession(nsp, socket, sessionId, 'abort.timeout', {
        event: 'abort.timeout',
        run_id: runId,
        synced: false,
        message: ABORT_BRIDGE_SYNC_TIMEOUT_MESSAGE,
      })
      logger.warn({ sessionId, runId }, '[chat-run-socket][abort] CLI bridge interrupt did not sync before timeout')
      try {
        await bridge.destroy?.(sessionId, activeState.profile)
        cancellationConfirmed = true
      } catch (err) {
        logger.warn(err, '[chat-run-socket][abort] failed to destroy timed-out CLI bridge session %s', sessionId)
      }
      const lease = activeState.runtimeTaskLease
      activeState.runtimeTaskLease = undefined
      if (lease) {
        if (cancellationConfirmed) {
          try { await lease.finish('cancelled') } catch (err) {
            lease.abandon()
            logger.warn(err, '[chat-run-socket][abort] failed to finish cancelled DeepAgent Runtime task lease')
          }
        } else {
          lease.abandon()
        }
      }
      await markAbortCompleted(nsp, socket, sessionId, runId || 'bridge_abort_timeout', sessionMap, runQueuedItem, false)
      return
    }
    const lease = activeState.runtimeTaskLease
    activeState.runtimeTaskLease = undefined
    if (lease) {
      if (cancellationConfirmed) {
        try { await lease.finish('cancelled') } catch (err) {
          lease.abandon()
          logger.warn(err, '[chat-run-socket][abort] failed to finish cancelled DeepAgent Runtime task lease')
        }
      } else {
        lease.abandon()
      }
    }
  } else if (activeState.source === 'coding_agent') {
""")

print("DeepAgent bridge task lifecycle transformed")
