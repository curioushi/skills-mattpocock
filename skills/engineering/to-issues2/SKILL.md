---
name: to-issues2
description: 用 tracer-bullet（曳光弹）垂直切片把一份计划、规格或 PRD 拆成项目 issue tracker 上「独立可领取」的 issue。在原版基础上加了两点让改动更易 review：每个 issue 的非机械 diff 控制在 400 行内、实现完成后随 PR 附一份审查指南。当用户想把计划拆成 issue、创建实现工单、分解工作，或想控制单次改动规模、降低审查成本时使用。
---

# To Issues（审查友好版）

用垂直切片（tracer bullet，曳光弹）把一份计划拆成「独立可领取」的 issue。

## 流程

### 1. 收集上下文

从当前对话已有的内容出发。如果用户传入了 issue 编号或 URL 作为参数，用 `gh issue view <编号>` 把它（连同评论）取出来。

issue tracker 与 triage 标签的约定应当已经提供给你——若没有，先运行 `/setup-matt-pocock-skills`。

### 1.1 输出语言规则

与用户交互时沿用用户使用的语言；但凡需要**落盘为 Markdown 文件**的内容，必须用中文撰写，关键术语保留英文。这里的落盘 Markdown 包括 local markdown issue tracker 下的 `.md` issue、PRD 拆解文件、实现说明、审查指南，以及任何为了本次拆 issue 工作写入仓库的 Markdown 记录。

关键术语包括但不限于：issue、PRD、tracer bullet、vertical slice、HITL、AFK、diff、schema、API、UI、test、agent、PR、review、triage label、issue tracker、acceptance criteria。标题、正文、验收标准和审查指南都应使用中文句子，但这些术语按英文保留。

### 2. 探查 codebase（可选）

如果还没探查过 codebase，就探查一下，以了解代码的当前状态。

### 3. 起草垂直切片

把计划拆成 **tracer bullet（曳光弹）** issue。每个 issue 是一个**纵贯所有集成层、端到端**的薄垂直切片，而不是某一层的横切。

切片可以是 ‘HITL’ 或 ‘AFK’。HITL 切片需要人介入，比如一次架构决策或一次设计评审。AFK 切片可以在无人介入下实现并合并。尽可能优先选 AFK 而非 HITL。

<vertical-slice-rules>
- 每个切片提供一条贯穿每一层（schema、API、UI、测试）的窄而**完整**的路径
- 一个完成的切片本身可演示或可验证
- 宁可多个薄切片，不要少数厚切片
- **diff 预算**：每个 issue 的非机械 diff 建议 ≤ 400 行。机械改动（重命名、移动、格式化、生成代码）易审，不计入。
- **预算优先于垂直纯度**：若收窄后非机械 diff 仍超 400 行，允许该 issue 退化为单模块「增厚」（横切）而非真正的垂直切片——小而可审的 diff 比保持垂直更重要。
</vertical-slice-rules>

### 4. 向用户提问

把拟定的拆解以编号列表呈现。每个切片展示：

- **标题**：简短描述性名称
- **类型**：HITL / AFK
- **预期非机械 diff**：约 N 行（核对 400 行预算）
- **被谁阻塞**：哪些其他切片（如有）必须先完成
- **覆盖的用户故事**：这个切片对应哪些用户故事（如果源材料里有）

向用户提问：

- 颗粒度合适吗？（太粗 / 太细）
- 有没有切片超出 400 行非机械 diff？该拆分还是退化为单模块增厚？
- 依赖关系对吗？
- 有没有切片需要合并或进一步拆分？
- HITL 和 AFK 是否标对了？

反复迭代，直到用户批准这份拆解。

### 5. 创建 issue

对每个被批准的切片，发布一个新 issue 到 issue tracker。GitHub issue tracker 用 `gh issue create`；local markdown issue tracker 按 `docs/agents/issue-tracker.md` 约定写入 `.md` 文件。使用下面的 issue 正文模板。

如果 issue tracker 是 local markdown，所有落盘的 `.md` 文件都必须遵守「输出语言规则」：中文正文，关键术语保留英文。不要把模板字段翻译回英文，也不要混用英文段落来描述实现任务。

这些 issue 被视为已可交给 AFK agent，因此发布时打上正确的 triage 标签（除非另有指示）。

按依赖顺序发布（被依赖者在前），这样「被谁阻塞」字段里就能引用到真实的 issue 编号。

模板末尾的「审查指南」由实现者在完成后随 PR 填写，别省略。审查指南必须尽量短：开发思路用一句话概括，高效审查路径用文件阅读顺序表达。

<issue-template>
## 父级

#<父 issue 编号>（若来源是某个 issue；否则省略本节）

## 要构建什么

简要描述这个垂直切片。描述端到端的行为，而不是逐层的实现。

## 验收标准

- [ ] 标准 1
- [ ] 标准 2
- [ ] 标准 3

## 被谁阻塞

- 被 #<issue 编号> 阻塞（如有）

或「无 —— 可立即开始」。

## 审查指南（实现完成后由实现者随 PR 补充）

- **开发思路**：一句话概括怎么实现的、关键决策与取舍。
- **高效审查路径**：`file1.py -> file2.py -> file3.cpp`（按建议阅读顺序列文件路径）。
- **心智地图更新**：本次新增或改变了哪些概念、抽象、模块或依赖。

</issue-template>

不要关闭或修改任何父 issue。
