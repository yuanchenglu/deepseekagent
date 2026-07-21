# Evidence Classification System

> This classification system comes from the DeepSeek Agent research methodology (`research-method.md`). It provides a disciplined vocabulary for stating how certain we are about a claim about a system. Useful when writing paper entries that involve implementation claims about open-source systems.

## Level Definitions

```
A0：固定 commit 的真实运行路径与测试共同证明
A1：固定 commit 的实现源码证明，但尚未确认运行效果
A2：官方 README / docs / config 中的产品声明
B：基于事实的工程推论或设计方案
C：非官方逆向或社区线索
N：在公开证据中未找到实现
```

## When to Use in Paper Databases

| Context | Apply Level | Example |
|---------|-------------|---------|
| Paper claims about a system you've personally run | A0 | "We verified the SWE-agent loop on this commit" |
| Paper analysis based on reading source code | A1 | "The context manager logic is confirmed in code at commit abc123" |
| Citing a paper's own claims about its system | A2 | "The paper states it achieves X% on benchmark Y" |
| Your inference from the paper + other sources | B | "Based on the architecture figure and ablation study, we infer..." |
| Community claims without paper/src support | C | "Community reports suggest this framework also supports..." |
| Something that should exist but doesn't | N | "No evidence of sandbox isolation in the open-source release" |

## Recommended Language Mapping

| Don't say | Say |
|-----------|-----|
| "已证明最优" | "在当前源码/样本中表现出优势，仍需 benchmark" |
| "唯一实现" | "在本次固定版本调研中确认实现" |
| "必然 / 永远" | "在这些条件下预期 / 需要验证" |
| "源码验证完成" | "已定位关键实现；是否接入运行路径另行说明" |
| "生产级" | "已通过明确的生产指标与运行证据" |
