# Graduation Design Skills

Codex skills for planning a graduation design project and reviewing its formulas, code, and thesis in an isolated context.

这是一个面向本科和硕士毕业设计的 Codex 技能仓库。它把毕业设计拆成可验收的里程碑和证据关卡，并通过独立子智能体审查公式推导、代码实现和论文，避免作者在同一上下文中“检查自己”。

## Included Skills

| Skill | 用途 |
|---|---|
| [`graduation-design-coach`](skills/graduation-design-coach/SKILL.md) | 选题收敛、里程碑规划、文献与实验设计、论文证据链、答辩准备和提交核验 |
| [`graduation-independent-review`](skills/graduation-independent-review/SKILL.md) | 使用无父级历史的子智能体独立审查公式、代码和论文，输出问题表、结论和复审闭环 |

两个技能配合使用：

```text
graduation-design-coach
        |
        | 进入 F1 / C1 / P1 关卡
        v
graduation-independent-review
        |
        +-- formula：公式与推导
        +-- code：代码与实验实现
        +-- paper：整篇论文
```

- **F1**：核心公式冻结前。
- **C1**：正式批量实验前。
- **P1**：最终提交和答辩前。

## What You Get

`graduation-design-coach` 包含：

- 项目章程、选题范围契约和周度检查模板；
- 文献比较矩阵与实验计划；
- 论文声明—证据映射；
- 答辩问题库；
- 声明—证据映射检查脚本。

`graduation-independent-review` 包含：

- 公式、代码、论文三个审查模式；
- 审查材料包和独立审查报告模板；
- P0/P1/P2 问题跟踪；
- 子智能体启动提示词和隔离协议；
- 复审、争议仲裁与问题关闭检查脚本。

## Requirements

- 支持 Skills 的 Codex 环境。
- Python 3，仅用于运行附带的标准库脚本。
- 独立审查需要可用的子智能体工具。若无法启动隔离子智能体，技能会停止审查并明确报告，不会把同上下文自查伪装成独立审查。

## Installation

克隆仓库：

```bash
git clone https://github.com/zhuJarvi/graduation-design-skills.git
cd graduation-design-skills
```

把两个技能复制到 Codex 的技能目录：

```bash
SKILLS_DIR="${CODEX_HOME:-$HOME/.codex}/skills"
mkdir -p "$SKILLS_DIR"

cp -R skills/graduation-design-coach "$SKILLS_DIR/"
cp -R skills/graduation-independent-review "$SKILLS_DIR/"
```

如果本机已经安装过同名技能，建议先备份或移走原目录，再执行复制。

验证安装：

```bash
ls "$SKILLS_DIR/graduation-design-coach/SKILL.md"
ls "$SKILLS_DIR/graduation-independent-review/SKILL.md"
```

随后在新消息中显式调用：

```text
$graduation-design-coach 帮我根据专业、截止时间和现有材料制定毕业设计计划。

$graduation-independent-review formula 使用隔离子智能体审查这份公式推导。
$graduation-independent-review code 使用隔离子智能体审查当前代码快照。
$graduation-independent-review paper 使用隔离子智能体审查最终论文。
```

## Update

```bash
cd graduation-design-skills
git pull

SKILLS_DIR="${CODEX_HOME:-$HOME/.codex}/skills"
cp -R skills/graduation-design-coach "$SKILLS_DIR/"
cp -R skills/graduation-independent-review "$SKILLS_DIR/"
```

## Utility Scripts

检查论文声明与证据映射：

```bash
python3 "$SKILLS_DIR/graduation-design-coach/scripts/audit_evidence_map.py" \
  path/to/claim-evidence-map.csv
```

检查独立审查问题表：

```bash
python3 "$SKILLS_DIR/graduation-independent-review/scripts/audit_review_log.py" \
  path/to/review-issue-log.csv --fail-on p1
```

`--fail-on` 可选：

- `none`：只检查表格结构和关闭证据。
- `p0`：存在未关闭 P0 时失败，默认值。
- `p1`：存在未关闭 P0 或 P1 时失败。
- `any`：存在任何未关闭问题时失败。

## Repository Layout

```text
.
|-- README.md
`-- skills/
    |-- graduation-design-coach/
    |   |-- SKILL.md
    |   |-- agents/
    |   |-- assets/
    |   |-- references/
    |   `-- scripts/
    `-- graduation-independent-review/
        |-- SKILL.md
        |-- agents/
        |-- assets/
        |-- references/
        `-- scripts/
```

## Design Notes

- 结论必须由证据支持，不编造文献、实验或结果。
- 范围和控制优先于功能数量。
- 正式独立审查必须隔离上下文，并冻结被审查版本。
- 审查者先只记录问题，作者修复后再复审。
- 学校模板、导师要求和专业规范始终优先于通用建议。

这些技能用于辅助规划、检查和追踪，不替代导师指导、学校规定或作者对研究内容的最终责任。
