#!/usr/bin/env python3
"""Audit an isolated-review issue log for structure and blocking issues."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path


REQUIRED_COLUMNS = [
    "issue_id",
    "area",
    "severity",
    "issue",
    "evidence",
    "recommendation",
    "owner",
    "status",
    "resolution",
    "verified_by",
    "verification",
]
VALID_AREAS = {"formula", "code", "paper", "cross"}
VALID_SEVERITIES = {"p0", "p1", "p2"}
VALID_STATUSES = {"open", "in_progress", "resolved", "closed", "accepted_risk"}
FAIL_ON_CHOICES = ("none", "p0", "p1", "any")
UNRESOLVED_STATUSES = {"open", "in_progress", "resolved"}


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def empty_result(path: Path, errors: list[str], warnings: list[str]) -> dict[str, object]:
    return {
        "path": str(path),
        "issues": 0,
        "severity_counts": {},
        "status_counts": {},
        "unresolved_by_severity": {},
        "errors": errors,
        "warnings": warnings,
    }


def audit(path: Path, fail_on: str) -> tuple[dict[str, object], int]:
    errors: list[str] = []
    warnings: list[str] = []
    severity_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    unresolved_by_severity: Counter[str] = Counter()
    issue_count = 0

    if not path.is_file():
        errors.append(f"找不到审查问题表：{path}")
        return empty_result(path, errors, warnings), 1

    try:
        handle = path.open("r", encoding="utf-8-sig", newline="")
    except OSError as exc:
        errors.append(f"无法读取文件：{exc}")
        return empty_result(path, errors, warnings), 1

    with handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            errors.append("CSV 没有表头。")
            return empty_result(path, errors, warnings), 1

        reader.fieldnames = [clean(name) for name in reader.fieldnames]
        missing = [name for name in REQUIRED_COLUMNS if name not in reader.fieldnames]
        if missing:
            errors.append("缺少必需列：" + ", ".join(missing))
            return empty_result(path, errors, warnings), 1

        seen_ids: dict[str, int] = {}
        for line_number, raw_row in enumerate(reader, start=2):
            row = {key: clean(value) for key, value in raw_row.items() if key is not None}
            if not any(row.values()):
                continue

            issue_count += 1
            if clean(raw_row.get(None, "")):
                errors.append(
                    f"第 {line_number} 行：字段数量超过表头，请检查多余逗号或未加引号的文本。"
                )

            issue_id = row["issue_id"]
            area = row["area"].lower()
            severity = row["severity"].lower()
            status = row["status"].lower()

            if not issue_id:
                errors.append(f"第 {line_number} 行：issue_id 为空。")
            elif issue_id in seen_ids:
                errors.append(
                    f"第 {line_number} 行：issue_id '{issue_id}' 与第 {seen_ids[issue_id]} 行重复。"
                )
            else:
                seen_ids[issue_id] = line_number

            for field in ("issue", "evidence", "recommendation", "owner"):
                if not row[field]:
                    errors.append(f"第 {line_number} 行：{field} 为空。")

            if area not in VALID_AREAS:
                errors.append(
                    f"第 {line_number} 行：area '{row['area']}' 无效，"
                    "应为 formula、code、paper 或 cross。"
                )

            if severity not in VALID_SEVERITIES:
                errors.append(
                    f"第 {line_number} 行：severity '{row['severity']}' 无效，"
                    "应为 P0、P1 或 P2。"
                )
            else:
                severity_counts[severity.upper()] += 1

            if status not in VALID_STATUSES:
                errors.append(
                    f"第 {line_number} 行：status '{row['status']}' 无效，"
                    "应为 open、in_progress、resolved、closed 或 accepted_risk。"
                )
            else:
                status_counts[status] += 1
                if status in UNRESOLVED_STATUSES:
                    unresolved_by_severity[severity.upper()] += 1

            if status == "closed":
                for field in ("resolution", "verified_by", "verification"):
                    if not row[field]:
                        errors.append(
                            f"第 {line_number} 行：closed 问题必须填写 {field}。"
                        )

            if status == "accepted_risk":
                if severity == "p0":
                    errors.append(
                        f"第 {line_number} 行：P0 阻断问题不能用 accepted_risk 代替关闭。"
                    )
                for field in ("resolution", "verified_by", "verification"):
                    if not row[field]:
                        errors.append(
                            f"第 {line_number} 行：accepted_risk 必须填写 {field}。"
                        )

            if status == "resolved":
                warnings.append(
                    f"第 {line_number} 行：问题已修复但尚未复审关闭。"
                )

    if issue_count == 0:
        warnings.append("审查问题表没有记录，尚未完成任何审查闭环。")

    fail_levels = {
        "none": set(),
        "p0": {"P0"},
        "p1": {"P0", "P1"},
        "any": {"P0", "P1", "P2"},
    }[fail_on]
    threshold_failed = any(
        unresolved_by_severity.get(level, 0) > 0 for level in fail_levels
    )

    result = {
        "path": str(path),
        "issues": issue_count,
        "severity_counts": dict(sorted(severity_counts.items())),
        "status_counts": dict(sorted(status_counts.items())),
        "unresolved_by_severity": dict(sorted(unresolved_by_severity.items())),
        "fail_on": fail_on,
        "threshold_failed": threshold_failed,
        "errors": errors,
        "warnings": warnings,
    }

    exit_code = 1 if errors or threshold_failed else 0
    return result, exit_code


def print_text(result: dict[str, object]) -> None:
    print(f"审查问题表：{result['path']}")
    print(f"问题总数：{result.get('issues', 0)}")
    for label, key in (
        ("级别统计", "severity_counts"),
        ("状态统计", "status_counts"),
        ("未关闭统计", "unresolved_by_severity"),
    ):
        counts = result.get(key, {})
        if isinstance(counts, dict) and counts:
            print(label + "：" + ", ".join(f"{name}={count}" for name, count in counts.items()))

    errors = result.get("errors", [])
    warnings = result.get("warnings", [])
    if errors:
        print("\n错误：")
        for item in errors:
            print(f"- {item}")
    if warnings:
        print("\n警示：")
        for item in warnings:
            print(f"- {item}")
    if not errors and not warnings and result.get("issues", 0):
        if result.get("threshold_failed"):
            print("问题表结构有效，但未满足当前失败阈值。")
        else:
            print("问题表结构有效，并已满足当前失败阈值。")
    elif not errors:
        print("问题表结构有效；仍需处理上述未关闭或未复审问题。")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="检查独立审查问题表的结构、关闭证据和阻断问题。"
    )
    parser.add_argument("csv_file", type=Path, help="review issue log CSV 文件")
    parser.add_argument(
        "--fail-on",
        choices=FAIL_ON_CHOICES,
        default="p0",
        help="在何种未关闭严重度上返回非零状态，默认 p0。",
    )
    parser.add_argument("--json", action="store_true", help="以 JSON 输出结果。")
    args = parser.parse_args()

    result, exit_code = audit(args.csv_file, args.fail_on)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_text(result)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
