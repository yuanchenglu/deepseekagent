#!/usr/bin/env python3
from pathlib import Path

path = Path('scripts/apply-runtime-deepcode.py')
text = path.read_text(encoding='utf-8')

function = '''def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one match, found {count}: {old[:100]!r}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")
'''
helper = function + '''

def replace_exact(path: str, old: str, new: str, expected: int) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != expected:
        raise RuntimeError(f"{path}: expected {expected} matches, found {count}: {old[:100]!r}")
    target.write_text(text.replace(old, new), encoding="utf-8")
'''
if text.count(function) != 1:
    raise RuntimeError('DeepCode transformer replace_once definition drifted')
text = text.replace(function, helper, 1)

block = '''replace_once(path, """    })
    run.currentChild = child

    let stdoutBuffer = ''
""", """    })
    run.currentChild = child
    run.currentTaskLease = taskLease

    let stdoutBuffer = ''
""")
'''
if text.count(block) != 2:
    raise RuntimeError(f'expected exactly two identical spawn transform blocks, found {text.count(block)}')
first = block.replace('replace_once(', 'replace_exact(', 1)
first = first.removesuffix('""")\n') + '""", 2)\n'
text = text.replace(block, first, 1)
text = text.replace(block, '', 1)
path.write_text(text, encoding='utf-8')
print('DeepCode transformer prepared for two intentional spawn markers')
