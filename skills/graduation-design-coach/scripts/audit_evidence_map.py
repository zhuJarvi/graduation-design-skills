#!/usr/bin/env python3
"""Audit a claim-evidence map used for thesis and defense preparation."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path


REQUIRED_COLUMNS = [
    "claim_id",
    "claim",
    "location",
    "claim_type",
    "evidence",
    "evidence_location",
    "status",
    "gap_action",
]
VALID_STATUSES = {"supported", "partial", "unsupported"}
CLAIM_TYPE_ALIASES = {
    "fact": "fact",
    "design": "design",
    "effect": "effect",
    "explanation": "explanation",
    "generalization": "generalization",
    "事实": "fact",
    "设计": "design",
    "效果": "effect",
    "解释": "explanation",
    "推广": "generalization",
}


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def audit(path: Path, strict: bool) -> tuple[dict[str, object], int]:
    errors: list[str] = []
    warnings: list[str] = []

    if not path.is_file():
        errors.append(f"找不到证据映射文件：{path}")
        return {
            "path": str(path),
            "errors": errors,
            "warnings": warnings,
            "counts": {},
            "claims": 0,
        }, 1

    try:
        handle = path.open("r", encoding="utf-8-sig", newline="")
    except OSError as exc:
        errors.append(f"无法读取文件：{exc}")
        return {
            "path": str(path),
            "errors": errors,
            "warnings": warnings,
            "counts": {},
            "claims": 0,
        }, 1

    with handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            errors.append("CSV 没有表头。")
            return {
                "path": str(path),
                "errors": errors,
                "warnings": warnings,
                "counts": {},
                "claims": 0,
            }, 1

        reader.fieldnames = [clean(name) for name in reader.fieldnames]
        missing = [name for name in REQUIRED_COLUMNS if name not in reader.fieldnames]
        if missing:
            errors.append("缺少必需列：" + ", ".join(missing))
            return {
                "path": str(path),
                "errors": errors,
                "warnings": warnings,
                "counts": {},
                "claims": 0,
            }, 1

        seen_ids: dict[str, int] = {}
        counts: Counter[str] = Counter()
        claim_count = 0

        for line_number, raw_row in enumerate(reader, start=2):
            row = {key: clean(value) for key, value in raw_row.items() if key is not None}
            if not any(row.values()):
                continue

            claim_count += 1
            if clean(raw_row.get(None, "")):
                errors.append(
                    f"第 {line_number} 行：字段数量超过表头，请检查多余逗号或未加引号的文本。"
                )

            claim_id = row["claim_id"]
            status = row["status"].lower()

            if not claim_id:
                errors.append(f"第 {line_number} 行：claim_id 为空。")
            elif claim_id in seen_ids:
                errors.append(
                    f"第 {line_number} 行：claim_id '{claim_id}' 与第 {seen_ids[claim_id]} 行重复。"
                )
            else:
                seen_ids[claim_id] = line_number

            if not row["claim"]:
                errors.append(f"第 {line_number} 行：claim 为空。")
            if not row["location"]:
                errors.append(f"第 {line_number} 行：location 为空。")
            if not row["claim_type"]:
                errors.append(f"第 {line_number} 行：claim_type 为空。")
            if not status:
                errors.append(f"第 {line_number} 行：status 为空。")

            if status and status not in VALID_STATUSES:
                errors.append(
                    f"第 {line_number} 行：status '{row['status']}' 无效，"
                    "应为 supported、partial 或 unsupported。"
                )
            else:
                counts[status] += 1

            if status == "supported":
                if not row["evidence"] or not row["evidence_location"]:
                    errors.append(
                        f"第 {line_number} 行：supported 声明必须填写 evidence 和 evidence_location。"
                    )
            elif status in {"partial", "unsupported"} and not row["gap_action"]:
                errors.append(
                    f"第 {line_number} 行：{status} 声明必须填写 gap_action。"
                )

            claim_type = CLAIM_TYPE_ALIASES.get(
                row["claim_type"].strip().lower(), row["claim_type"].strip().lower()
            )
            if claim_type in {"effect", "explanation", "generalization"} and status != "supported":
                warnings.append(
                    f"第 {line_number} 行：{claim_type} 声明当前为 {status or '空状态'}，"
                    "需要缩小表述、补证或移入局限。"
                )

    if claim_count == 0:
        warnings.append("映射表没有声明记录，尚未完成任何证据审查。")

    result = {
        "path": str(path),
        "claims": claim_count,
        "counts": {
            "supported": counts.get("supported", 0),
            "partial": counts.get("partial", 0),
            "unsupported": counts.get("unsupported", 0),
        },
        "errors": errors,
        "warnings": warnings,
    }
    blocked = counts.get("partial", 0) + counts.get("unsupported", 0)
    exit_code = 1 if errors or (strict and blocked) else 0
    return result, exit_code


def print_text(result: dict[str, object]) -> None:
    print(f"证据映射：{result['path']}")
    print(f"声明总数：{result.get('claims', 0)}")
    counts = result.get("counts", {})
    if isinstance(counts, dict) and counts:
        print(
            "状态统计："
            f"supported={counts.get('supported', 0)}, "
            f"partial={counts.get('partial', 0)}, "
            f"unsupported={counts.get('unsupported', 0)}"
        )

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
    if not errors and not warnings:
        print("结构检查通过，没有发现未处理的证据缺口。")
    elif not errors:
        print("结构检查通过；仍需人工处理上述证据缺口。")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="检查论文声明—证据映射表的结构、状态和缺口动作。"
    )
    parser.add_argument("csv_file", type=Path, help="claim-evidence map CSV 文件")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="当存在 partial 或 unsupported 声明时也返回非零状态。",
    )
    parser.add_argument("--json", action="store_true", help="以 JSON 输出结果。")
    args = parser.parse_args()

    result, exit_code = audit(args.csv_file, args.strict)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_text(result)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
