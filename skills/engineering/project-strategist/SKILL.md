---
name: project-strategist
description: Analyze a project's planning state from domain docs, local issues, backlog, git history, and lightweight source signals, then generate a Chinese project strategy HTML report. Use when the user asks for project-level planning, strategic roadmap, project diagnosis, long-term direction, project strategy, 项目规划, 发展建议, or 路线图.
---

# Project Strategist

Create an evidence-based project strategy report. The report is for project-level
planning: current state, planning gaps, risks, and a Now / Next / Later roadmap.

## Default output

- Write a complete, self-contained Chinese HTML file to `project-strategy.html`
  in the current repo root.
- Also respond with a short Chinese summary and the report path.
- After writing the HTML, open it in the system browser.
- The HTML must be a static single file with inline CSS only: no external
  fonts, CSS, JS, images, or CDNs.
- Use an engineering-review tone: direct, specific, and evidence-backed.

## Boundaries

- The only default write is `project-strategy.html`.
- Do not update `.scratch/`, PRDs, issues, ADRs, `CONTEXT.md`, or source files
  unless the user explicitly asks after reviewing the report.
- Do not invoke downstream skills automatically. You may recommend later use of
  skills such as `improve-codebase-architecture`, `to-prd`, `to-issues`,
  `to-issues2`, or `grill-with-docs`, but only as recommendations.
- If a recommendation conflicts with an ADR, mark the conflict clearly and say
  whether reopening the ADR is justified.

## Workflow

1. Confirm the working directory is the project to analyse.
2. Run the bundled collector script at
   [scripts/collect-project-signals.py](scripts/collect-project-signals.py),
   resolving the script path relative to this `SKILL.md`:

   ```bash
   python3 <skill-dir>/scripts/collect-project-signals.py --output /tmp/project-strategy-signals.json
   ```

3. Read `/tmp/project-strategy-signals.json`. If the collector reports warnings,
   reflect the important ones in the report.
4. Read additional local files only when needed to support a judgment. Prefer:
   `CONTEXT.md`, `CONTEXT-MAP.md`, `docs/adr/`, `.scratch/`, and recent commits.
5. Generate `project-strategy.html` in the repo root.
6. Open the generated report in the system browser:

   ```bash
   open "$(pwd)/project-strategy.html"
   ```

   Use `xdg-open` on Linux or `start` on Windows. If the open command fails
   because no browser/session is available, continue and mention the failure in
   the final response.
7. Final response: give a short Chinese summary and the absolute path to the
   HTML file, and say whether the browser was opened.

## Report structure

The HTML body should include:

- Title, generation time, repo path, branch, and HEAD commit.
- Executive summary: 3-6 direct paragraphs or bullets.
- Current state: what the project has actually completed, based on issues and
  git history.
- Strategic diagnosis: the main planning gaps, architectural risks, delivery
  risks, and stale assumptions.
- Now / Next / Later roadmap:
  - Now: 1-3 actions that protect the current delivery target.
  - Next: the next planning moves after the current bottleneck is addressed.
  - Later: long-range ideas with explicit prerequisites.
- Recommendations for follow-up workflows. Mention skills only as suggestions;
  do not execute them.
- Evidence appendix in a collapsed `<details>` section: issue status counts,
  backlog items, ADR list, recent commits, high-churn files, and lightweight
  source/test signals.

## Evidence rules

- Every major risk, priority change, and roadmap item must include a short
  "证据：" line naming the source paths, ADR numbers, issue ids, commits, or
  source signals behind it.
- Separate fact, inference, and recommendation. Do not present inferred strategy
  as settled project fact.
- Prefer project vocabulary from `CONTEXT.md`. Avoid synonyms explicitly rejected
  by the project glossary.
- If `CONTEXT.md`, ADRs, or `.scratch/` are missing, continue and state the gap.

## Collector behavior

The collector is deterministic and fact-only. It should fail when the current
directory is not inside a git repository. Missing `CONTEXT.md`, `docs/adr/`, or
`.scratch/` should be reported as warnings rather than fatal errors.
