#!/usr/bin/env python3
from pathlib import Path

test_path = Path('webui/tests/server/global-agent-server.test.ts')
test_source = test_path.read_text(encoding='utf-8')
old_helper = '''async function waitForMockCalls(mock: { mock: { calls: unknown[] } }, count: number): Promise<void> {
  const startedAt = Date.now()
  while (mock.mock.calls.length < count && Date.now() - startedAt < 1000) {
    await new Promise(resolve => setTimeout(resolve, 5))
  }
}
'''
new_helper = old_helper + '''
async function waitForMockCall(
  mock: { mock: { calls: unknown[][] } },
  predicate: (call: unknown[]) => boolean,
): Promise<void> {
  const startedAt = Date.now()
  while (!mock.mock.calls.some(predicate) && Date.now() - startedAt < 1000) {
    await new Promise(resolve => setTimeout(resolve, 5))
  }
  if (!mock.mock.calls.some(predicate)) throw new Error('expected mock call did not arrive before timeout')
}
'''
old_assertion = '''    await waitForMockCalls(fetchImpl, 2)
    expect(JSON.parse(String(fetchImpl.mock.calls[1][1]?.body))).toMatchObject({
      text: '结果如下： | 名称 | 值 | | --- | --- | | foo | 1 | 请确认。',
    })
    expect(agentSocket.emit).toHaveBeenCalledWith('audio.enqueue', expect.objectContaining({
'''
new_assertion = '''    await waitForMockCalls(fetchImpl, 2)
    expect(JSON.parse(String(fetchImpl.mock.calls[1][1]?.body))).toMatchObject({
      text: '结果如下： | 名称 | 值 | | --- | --- | | foo | 1 | 请确认。',
    })
    await waitForMockCall(agentSocket.emit, call => (
      call[0] === 'audio.enqueue' && (call[1] as any)?.segmentId === 'voice-1-tts-2'
    ))
    expect(agentSocket.emit).toHaveBeenCalledWith('audio.enqueue', expect.objectContaining({
'''
if test_source.count(old_helper) != 1:
    raise SystemExit('waitForMockCalls contract changed; refusing patch')
if test_source.count(old_assertion) != 1:
    raise SystemExit('MCU assertion contract changed; refusing patch')
test_path.write_text(test_source.replace(old_helper, new_helper).replace(old_assertion, new_assertion), encoding='utf-8')

workflow_path = Path('.github/workflows/release-electron-preview.yml')
workflow = workflow_path.read_text(encoding='utf-8')
old_paths = '''      - "webui/package-lock.json"
      - "webui/packages/desktop/**"
'''
new_paths = '''      - "webui/package-lock.json"
      - "webui/tests/**"
      - "webui/packages/desktop/**"
'''
if workflow.count(old_paths) != 1:
    raise SystemExit('Electron Preview path contract changed; refusing patch')
workflow_path.write_text(workflow.replace(old_paths, new_paths), encoding='utf-8')
print('patched deterministic MCU wait and Electron test path gate')
