import type { IpcMainInvokeEvent } from 'electron'
import { WorkspaceLockManager, type WorkspaceAccess } from './workspace-lock'

export const WORKSPACE_LOCK_CHANNELS = {
  acquire: 'deepagent:workspace-lock:acquire',
  release: 'deepagent:workspace-lock:release',
  releaseTask: 'deepagent:workspace-lock:release-task',
} as const

export interface WorkspaceLockSender {
  id: number
  once(event: 'destroyed', listener: () => void): unknown
}

export interface WorkspaceLockIpcEvent {
  sender: WorkspaceLockSender
}

export interface WorkspaceLockIpcMain {
  handle(
    channel: string,
    listener: (event: WorkspaceLockIpcEvent, ...args: unknown[]) => unknown,
  ): void
}

function ownerIdForSender(sender: WorkspaceLockSender): string | null {
  return Number.isSafeInteger(sender.id) && sender.id >= 0
    ? `renderer:${sender.id}`
    : null
}

function validWorkspaceArgument(value: unknown): value is string {
  return typeof value === 'string' && value.trim().length > 0
}

function validTaskArgument(value: unknown): value is string {
  return typeof value === 'string'
}

export function registerWorkspaceLockIpc(
  ipcMain: WorkspaceLockIpcMain,
  locks = new WorkspaceLockManager(),
): WorkspaceLockManager {
  const cleanupRegistered = new Set<number>()

  function bindOwnerLifecycle(sender: WorkspaceLockSender, ownerId: string): void {
    if (cleanupRegistered.has(sender.id)) return
    cleanupRegistered.add(sender.id)
    sender.once('destroyed', () => {
      locks.releaseOwner(ownerId)
      cleanupRegistered.delete(sender.id)
    })
  }

  ipcMain.handle(
    WORKSPACE_LOCK_CHANNELS.acquire,
    (event, workspace, taskId, access) => {
      const ownerId = ownerIdForSender(event.sender)
      if (
        !ownerId
        || !validWorkspaceArgument(workspace)
        || !validTaskArgument(taskId)
        || (access !== 'read' && access !== 'write')
      ) {
        return false
      }

      bindOwnerLifecycle(event.sender, ownerId)
      return locks.acquire(workspace, taskId, access as WorkspaceAccess, ownerId)
    },
  )

  ipcMain.handle(
    WORKSPACE_LOCK_CHANNELS.release,
    (event, workspace, taskId) => {
      const ownerId = ownerIdForSender(event.sender)
      if (!ownerId || !validWorkspaceArgument(workspace) || !validTaskArgument(taskId)) return
      locks.release(workspace, taskId, ownerId)
    },
  )

  ipcMain.handle(
    WORKSPACE_LOCK_CHANNELS.releaseTask,
    (event, taskId) => {
      const ownerId = ownerIdForSender(event.sender)
      if (!ownerId || !validTaskArgument(taskId)) return
      locks.releaseTask(taskId, ownerId)
    },
  )

  return locks
}

export type ElectronWorkspaceLockEvent = Pick<IpcMainInvokeEvent, 'sender'>
