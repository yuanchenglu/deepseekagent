#!/usr/bin/env python3
from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding='utf-8')
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{path}: expected exactly one match, found {count}: {old[:120]!r}')
    target.write_text(text.replace(old, new, 1), encoding='utf-8')


replace_once(
    'webui/packages/desktop/src/main/runtime-task-supervisor.ts',
    """  response.setHeader('content-type', 'application/json; charset=utf-8')
  response.setHeader('content-length', String(payload.length))
  response.end(payload)
""",
    """  response.setHeader('content-type', 'application/json; charset=utf-8')
  response.setHeader('content-length', String(payload.length))
  response.setHeader('connection', 'close')
  response.end(payload)
""",
)

replace_once(
    'webui/packages/server/src/services/runtime-task-supervisor-client.ts',
    """    path,
    method: 'POST',
    headers: {
""",
    """    path,
    method: 'POST',
    agent: false,
    headers: {
""",
)

for test_path in [
    'webui/packages/desktop/src/main/runtime-task-supervisor.test.ts',
    'webui/packages/desktop/src/main/runtime-task-supervisor-generation.test.ts',
    'webui/packages/desktop/src/main/runtime-task-supervisor-runtime-crash.test.ts',
]:
    replace_once(
        test_path,
        """      path,
      method: 'POST',
      headers: {
""",
        """      path,
      method: 'POST',
      agent: false,
      headers: {
""",
    )

print('Runtime supervisor restart connection fix applied')
