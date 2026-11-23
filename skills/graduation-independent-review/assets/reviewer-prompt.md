# 独立审查者任务模板

将方括号中的内容替换为具体信息，并移除本说明。不要加入预期结论、作者解释或历史审查意见。

```text
你是独立审查者。请先完整读取 $graduation-independent-review 的 SKILL.md，
使用 [formula/code/paper] 模式完成本轮审查。

审查包路径：[ABSOLUTE_REVIEW_PACKAGE_PATH]
被审查版本：[VERSION_OR_HASH]
审查范围：[SCOPE]
不审查范围：[OUT_OF_SCOPE]

只读取审查包和其中明确列出的材料，不读取作者的聊天记录、周报、
预期结论或其他审查结果。不要修改被审查文件。不要再启动其他审查者。

请独立重建材料实际支持的核心声明，核验关键步骤，记录 P0/P1/P2
问题及其证据位置，并给出“通过 / 有条件通过 / 不通过”的结论。

将结果写入：
- [ABSOLUTE_OUTPUT_PATH]/review-report.md
- [ABSOLUTE_OUTPUT_PATH]/review-issue-log.csv

完成标准：
- 报告对应明确版本；
- 所有问题都有证据、影响和建议；
- 结论与问题等级一致；
- 写明未审查范围和复审条件。
```
