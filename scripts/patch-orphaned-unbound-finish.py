#!/usr/bin/env python3
from pathlib import Path

supervisor_path = Path('webui/packages/desktop/src/main/runtime-task-supervisor.ts')
source = supervisor_path.read_text(encoding='utf-8')
old_finish = '''    const record = this.records.get(key)
    if (!record) return { status: 200, body: { ok: true, code: 'already-terminal' } }
    if (record.state === 'orphaned') return { status: 409, body: { ok: false, code: 'resume-required', task: cloneTask(record) } }
    const result = request.outcome === 'cancelled'
'''
new_finish = '''    const record = this.records.get(key)
    if (!record) return { status: 200, body: { ok: true, code: 'already-terminal' } }
    if (record.state === 'orphaned') {
      // A task restored without process evidence must remain fail-closed: it may
      // not bind or resume an arbitrary PID. The original Runtime can still
      // explicitly confirm that the unbound attempt is terminal, which closes
      // the orphaned coordinator lease through the existing process-exit path.
      if (record.process) return { status: 409, body: { ok: false, code: 'resume-required', task: cloneTask(record) } }
      const terminal = this.coordinator.dispatch({
        type: 'process-exit', eventId: request.eventId, observedAt: this.now(), runtime: record.runtime,
        taskId: record.internalTaskId, leaseId: record.leaseId, exitCode: null, signal: null,
      })
      if (!terminal.ok) return { status: 409, body: { ok: false, code: terminal.code, message: terminal.message } }
      this.records.delete(key)
      this.persist()
      return { status: 200, body: { ok: true, code: request.outcome } }
    }
    const result = request.outcome === 'cancelled'
'''
if source.count(old_finish) != 1:
    raise SystemExit('finishTask contract changed; refusing patch')
supervisor_path.write_text(source.replace(old_finish, new_finish), encoding='utf-8')

test_path = Path('webui/tests/server/runtime-task-dual-runtime-e2e.test.ts')
test_source = test_path.read_text(encoding='utf-8')
anchor = '''  it('allows the same Runtime client to resume after heartbeat orphaning while unverifiable Main-restart tasks remain locked', async () => {
'''
addition = '''  it('releases an orphaned acquire-before-bind task only after explicit Runtime terminal confirmation', async () => {
    const value = await fixture()
    value.probe.set(8051, 'deepagent-after-unbound-cleanup')
    const taskId = runtimeTaskId('deepcode', 'main-restart-before-bind')
    const workspace = join(value.stateDir, 'main-restart-before-bind')
    const unbound = await deepcode(taskId, workspace)
    unbound.abandon()
    await value.supervisor.stop()

    await value.activate(newSupervisor(value))
    expect(value.supervisor.listTasks()).toMatchObject([
      { runtime: 'deepcode', taskId, workspace, state: 'orphaned', process: undefined },
    ])
    await expect(deepagent(runtimeTaskId('deepagent', 'blocked-by-unbound-orphan'), workspace, 8051))
      .rejects.toMatchObject({ code: 'conflict', status: 409 })

    await unbound.finish('failed')
    expect(value.supervisor.listTasks()).toEqual([])
    const afterConfirmation = await deepagent(runtimeTaskId('deepagent', 'after-unbound-cleanup'), workspace, 8051)
    await afterConfirmation.finish('completed')
    record('unbound-orphan-explicit-terminal-cleanup', value)
  })

'''
if test_source.count(anchor) != 1:
    raise SystemExit('dual Runtime E2E insertion anchor changed; refusing patch')
test_path.write_text(test_source.replace(anchor, addition + anchor), encoding='utf-8')
print('patched orphaned unbound terminal cleanup and E2E coverage')
