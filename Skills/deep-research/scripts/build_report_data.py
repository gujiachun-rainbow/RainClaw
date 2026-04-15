#!/usr/bin/env python3
"""
Deep Research — 报告数据组装脚本

从 research_plan.json、sections/*.txt、research_data/ 中读取调研结果，
组装为 report_data.json，供 pdf/docx generate_report 模板使用。

用法：
    python3 build_report_data.py [--output report_data.json]

前置条件：
    - research_plan.json 已包含 report_structure 和 subtopics
    - sections/ 目录下已有各章节文件
    - research_data/all_references.json 已合并完成
"""

import json
import os
import sys
import glob
from datetime import date


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def build_report_data(output_path="report_data.json"):
    plan = load_json("research_plan.json")
    structure = plan.get("report_structure", {})
    subtopics = plan.get("subtopics", [])
    scope = plan.get("scope", {})

    data = {
        "title": structure.get("title", plan.get("original_question", "深度调研报告")),
        "subtitle": structure.get("subtitle", ""),
        "short_title": structure.get("title", "调研报告")[:30],
        "report_type": "深度调研报告",
        "toc": True,
        "cover_meta": [
            ["报告类型", "深度调研报告"],
            ["生成日期", str(date.today())],
            ["调研领域", scope.get("domain", "")],
            ["问题类型", plan.get("question_type", "")],
        ],
        "disclaimer": "本报告由 AI 辅助调研生成，数据来源均已标注。请结合实际情况参考使用。",
        "sections": []
    }

    sec_num = 1

    # --- 执行摘要 ---
    summary_path = "sections/executive_summary.txt"
    if os.path.isfile(summary_path):
        data["sections"].append({
            "type": "heading", "level": 1,
            "number": f"{sec_num}.", "text": "执行摘要"
        })
        data["sections"].append({
            "type": "text", "body": load_text(summary_path)
        })
        sec_num += 1

    # --- 各子课题章节 ---
    section_map = {s["subtopic_id"]: s for s in structure.get("sections", [])}

    for st in subtopics:
        sid = st["id"]
        sec_file = f"sections/sec_{sid}.txt"
        if not os.path.isfile(sec_file):
            print(f"WARNING: {sec_file} not found, skipping subtopic {sid}")
            continue

        sec_info = section_map.get(sid, {})
        heading_number = sec_info.get("heading_number", f"{sec_num}.")
        heading_text = sec_info.get("heading_text", st.get("title", f"章节 {sid}"))

        data["sections"].append({
            "type": "heading", "level": 1,
            "number": heading_number, "text": heading_text
        })

        content = load_text(sec_file)
        data["sections"].append({"type": "text", "body": content})

        # 检查是否有该子课题的表格数据文件
        table_file = f"sections/table_{sid}.json"
        if os.path.isfile(table_file):
            table_data = load_json(table_file)
            data["sections"].append({
                "type": "table",
                "headers": table_data.get("headers", []),
                "rows": table_data.get("rows", []),
                "caption": table_data.get("caption", "")
            })

        sec_num += 1

    # --- 结论与展望 ---
    conclusion_path = "sections/conclusion.txt"
    if os.path.isfile(conclusion_path):
        data["sections"].append({
            "type": "heading", "level": 1,
            "number": f"{sec_num}.", "text": "结论与展望"
        })
        data["sections"].append({
            "type": "text", "body": load_text(conclusion_path)
        })
        sec_num += 1

    # --- 参考文献 ---
    refs_path = "research_data/all_references.json"
    if os.path.isfile(refs_path):
        all_refs = load_json(refs_path)
        data["sections"].append({
            "type": "heading", "level": 1,
            "number": f"{sec_num}.", "text": "参考文献"
        })
        data["sections"].append({
            "type": "references", "items": all_refs
        })

    # --- 写入 ---
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # --- 统计 ---
    total_chars = sum(len(s.get("body", "")) for s in data["sections"])
    section_count = sum(1 for s in data["sections"] if s["type"] == "heading")
    ref_count = 0
    for s in data["sections"]:
        if s["type"] == "references":
            ref_count = len(s.get("items", []))

    print(f"Report data generated: {output_path}")
    print(f"  Title    : {data['title']}")
    print(f"  Sections : {section_count}")
    print(f"  Chars    : {total_chars}")
    print(f"  Est pages: {total_chars // 500}")
    print(f"  References: {ref_count}")

    if total_chars < 3000:
        print(f"  WARNING: Total chars ({total_chars}) seems low. Consider expanding sections.")


if __name__ == "__main__":
    output = "report_data.json"
    if "--output" in sys.argv:
        idx = sys.argv.index("--output")
        if idx + 1 < len(sys.argv):
            output = sys.argv[idx + 1]
    build_report_data(output)
