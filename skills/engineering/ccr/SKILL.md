---
name: ccr
description: Run local Claude code review for current changes; invoke as /ccr.
disable-model-invocation: true
allowed-tools: Bash
---

Run a local Claude code review for the current repo changes, wait for the result, then relay the review and give your own assessment in this chat in Chinese.

## Levels

Default to `high` when no level is given.

| Level | Model | Effort |
| --- | --- | --- |
| `fast` | `sonnet` | `high` |
| `high` | `opus` | `high` |
| `max` | `opus` | `max` |

## Steps

1. Parse the invocation as `/ccr [fast|high|max]`. If the level is missing or unknown, use `high`. Completion criterion: exactly one model and effort pair has been selected from the table.
2. Run this command from the current repo root, replacing the model and effort from the selected level. Code review may take several minutes. Wait patiently and do not stop the command early; set the tool timeout to 10 minutes (`600000` ms). If it is still running after 10 minutes, stop and report the timeout instead of inventing findings.

```bash
claude -p '用中文审查此仓库当前未提交的代码变更。使用 git status 和 git diff 检查工作区。重点关注正确性 bug、回归、缺失测试、安全/数据丢失风险和行为不匹配。也要从代码仓库长期发展的远期视角评估可维护性、演进成本和架构风险。按严重程度排序列出发现，并尽量包含文件/行号引用。保持简洁。如果没有问题，请明确说明，并提到剩余测试风险。' --model <model> --effort <effort> --dangerously-skip-permissions
```

Completion criterion: the Claude command exits and its stdout/stderr have been captured.
3. Restate Claude's review result to the user in Chinese in the current chat. Preserve the finding order and severity. If the command failed, report the command failure in Chinese instead of inventing review findings.
4. Immediately evaluate Claude's review in Chinese: state which findings you agree with, disagree with, or are neutral on, with brief reasons. Base this on the local diff and code context; do not invent extra findings unless they are needed to explain your assessment. Completion criterion: the user can read both Claude's review and your assessment without asking a follow-up.
