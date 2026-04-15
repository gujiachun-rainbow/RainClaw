"""
DeepAgents 内置工具集 — 网页搜索与爬取。

提供 web_search / web_crawl 两个工具，通过调用 websearch 微服务（SearXNG + Crawl4AI）
替代原来的 Tavily internet_search。

特性：
  - 支持多输入：用 | 分隔多个 query 或 URL，一次调用完成多个任务
  - 异步并行：多个 query 使用 asyncio.gather 并发请求
"""
from __future__ import annotations

import asyncio
import logging
import os

import httpx
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

_WEBSEARCH_BASE_URL = os.environ.get("WEBSEARCH_BASE_URL", "http://websearch:8068")
_WEBSEARCH_API_KEY = os.environ.get("WEBSEARCH_API_KEY", "")
_REQUEST_TIMEOUT = 120


def _headers() -> dict:
    h: dict[str, str] = {"Content-Type": "application/json"}
    if _WEBSEARCH_API_KEY:
        h["apikey"] = _WEBSEARCH_API_KEY
    return h


async def _search_one_async(client: httpx.AsyncClient, query: str, limit: int = 10) -> dict:
    try:
        resp = await client.post(
            f"{_WEBSEARCH_BASE_URL}/web_search",
            json={"query": query, "limit": limit},
            headers=_headers(),
            timeout=_REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        return {
            "query": query,
            "results": [
                {"title": r.get("title", ""), "url": r.get("url", ""), "content": r.get("content", "")}
                for r in data.get("results", [])
            ],
        }
    except Exception as exc:
        logger.error(f"[web_search] query={query!r} failed: {exc}")
        return {"query": query, "results": [], "error": str(exc)}


async def _crawl_batch_async(url_list: list[str]) -> dict:
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{_WEBSEARCH_BASE_URL}/crawl_urls",
                json={"urls": url_list},
                headers=_headers(),
                timeout=_REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error(f"[web_crawl] crawl failed: {exc}")
        return {"results": {}, "failed_urls": url_list, "error": str(exc)}


def _run_async(coro):
    """Run async code from sync tool context (handles existing event loop)."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()


@tool
def web_search(queries: str) -> dict:
    """Search the internet for real-time information using one or more search queries.

    Returns titles, snippets and URLs from search engine results.
    To search for MULTIPLE topics at once, separate each query with a pipe '|'.
    All queries will be executed in parallel for faster results.

    Args:
        queries: One or more search queries separated by '|'.
                 Example single: "latest AI research papers"
                 Example multi:  "python async tutorial|rust vs go performance|climate change 2025"

    Returns:
        A dict containing a 'searches' list, where each element has 'query' and
        'results' (list of {title, url, content}).
    """
    query_list = [q.strip() for q in queries.split("|") if q.strip()]
    if not query_list:
        return {"searches": [], "error": "No valid queries provided"}

    logger.info(f"[web_search] Executing {len(query_list)} queries: {query_list}")

    async def _do_search():
        async with httpx.AsyncClient() as client:
            tasks = [_search_one_async(client, q) for q in query_list]
            return await asyncio.gather(*tasks)

    results = _run_async(_do_search())
    return {"searches": list(results)}


@tool
def propose_skill_save(skill_name: str) -> str:
    """After installing and testing a skill in the session workspace, call this tool to propose saving it permanently to the user's skill library. The frontend will show a confirmation prompt to the user.

    Args:
        skill_name: The name of the skill to save (e.g. "hello-world", "react-best-practices").

    Returns:
        A confirmation message.
    """
    return f"Proposed saving skill '{skill_name}' to user's permanent skill library. Waiting for user confirmation."


@tool
def propose_tool_save(tool_name: str, replaces: str = "") -> str:
    """After creating or upgrading a tool in the session workspace, call this tool to propose saving it permanently to the user's tool library. The tool file should already exist at {workspace_dir}/tools_staging/{tool_name}.py. The frontend will show a confirmation prompt to the user.

    Args:
        tool_name: The name of the tool to save (e.g. "check_weather", "person_physical_score"). This should match the .py filename (without extension).
        replaces: (Optional) If this tool is an upgraded version that REPLACES an existing tool with a DIFFERENT name, set this to the old tool's name. The old file will be deleted when saving. Leave empty if the name is unchanged (the common case — the new file simply overwrites the old one).

    Returns:
        A confirmation message.
    """
    msg = f"Proposed saving tool '{tool_name}' to user's permanent tool library."
    if replaces and replaces != tool_name:
        msg += f" This will replace the existing tool '{replaces}'."
    msg += " Waiting for user confirmation."
    return msg


@tool
def eval_skill(workspace_dir: str, skill_name: str, test_cases_json: str, iteration: int = 1) -> str:
    """Run evaluation test cases against a skill using independent agent sessions.

    Each test case is executed in an isolated agent that loads the skill but has no
    knowledge of the test design, simulating a real user. Results are saved to the
    workspace and a summary is returned.

    Args:
        workspace_dir: The caller's workspace directory (absolute path).
        skill_name: Name of the skill to evaluate (e.g. "hello-world").
        test_cases_json: JSON array of test cases. Each element: {"id": "t1", "prompt": "...", "description": "..."}.
        iteration: Iteration number for tracking improvements (default 1).

    Returns:
        A text summary of eval results with per-test status and file paths.
    """
    import json as _json
    try:
        test_cases = _json.loads(test_cases_json)
    except _json.JSONDecodeError as e:
        return f"Error: invalid test_cases_json — {e}"

    if not isinstance(test_cases, list) or not test_cases:
        return "Error: test_cases_json must be a non-empty JSON array"

    from backend.deepagent.runner import run_eval_task, EvalResult
    import shortuuid

    eval_base_dir = os.path.join(
        workspace_dir, f"{skill_name}-eval", f"iteration-{iteration}"
    )
    os.makedirs(eval_base_dir, exist_ok=True)

    skill_sources = ["/skills/", "/builtin-skills/"]

    results: list[dict] = []

    for tc in test_cases:
        tc_id = tc.get("id", shortuuid.uuid()[:6])
        prompt = tc.get("prompt", "")
        description = tc.get("description", prompt[:80])

        if not prompt:
            results.append({"id": tc_id, "status": "SKIPPED", "error": "empty prompt"})
            continue

        temp_session_id = f"eval-{shortuuid.uuid()}"

        logger.info(f"[eval_skill] Running test '{tc_id}' (session={temp_session_id})")

        eval_result: EvalResult = _run_async(run_eval_task(
            session_id=temp_session_id,
            query=prompt,
            skill_sources=skill_sources,
            timeout=180,
        ))

        tc_dir = os.path.join(eval_base_dir, tc_id)
        os.makedirs(tc_dir, exist_ok=True)

        with open(os.path.join(tc_dir, "prompt.txt"), "w") as f:
            f.write(prompt)

        with open(os.path.join(tc_dir, "response.md"), "w") as f:
            f.write(eval_result.response or "(no response)")

        with open(os.path.join(tc_dir, "tool_calls.json"), "w") as f:
            _json.dump(eval_result.tool_calls, f, ensure_ascii=False, indent=2)

        meta = {
            "id": tc_id,
            "description": description,
            "duration_ms": eval_result.duration_ms,
            "error": eval_result.error,
            "tool_call_count": len([
                t for t in eval_result.tool_calls if "result" not in t
            ]),
            "response_length": len(eval_result.response),
        }
        with open(os.path.join(tc_dir, "meta.json"), "w") as f:
            _json.dump(meta, f, ensure_ascii=False, indent=2)

        results.append({
            "id": tc_id,
            "description": description,
            "status": "ERROR" if eval_result.error else "COMPLETED",
            "duration_ms": eval_result.duration_ms,
            "error": eval_result.error,
            "response_preview": eval_result.response[:300] if eval_result.response else "(empty)",
            "output_dir": tc_dir,
        })

    # ── Load previous iteration for comparison ──
    prev_results_map: dict[str, dict] = {}
    prev_grading_map: dict[str, list[dict]] = {}
    if iteration > 1:
        prev_dir = os.path.join(
            workspace_dir, f"{skill_name}-eval", f"iteration-{iteration - 1}"
        )
        prev_summary_path = os.path.join(prev_dir, "summary.json")
        if os.path.isfile(prev_summary_path):
            try:
                with open(prev_summary_path, "r") as f:
                    prev_data = _json.load(f)
                for pr in prev_data.get("results", []):
                    prev_results_map[pr.get("id", "")] = pr
            except Exception:
                pass
        prev_grading_path = os.path.join(prev_dir, "grading.json")
        if os.path.isfile(prev_grading_path):
            try:
                with open(prev_grading_path, "r") as f:
                    prev_grading = _json.load(f)
                for pg in prev_grading:
                    tid = pg.get("test_id", "")
                    prev_grading_map.setdefault(tid, []).append(pg)
            except Exception:
                pass

    summary_path = os.path.join(eval_base_dir, "summary.json")
    with open(summary_path, "w") as f:
        _json.dump({"skill": skill_name, "iteration": iteration, "results": results},
                    f, ensure_ascii=False, indent=2)

    completed = sum(1 for r in results if r["status"] == "COMPLETED")
    total = len(results)
    lines = [
        f"## Eval Results — {skill_name} (iteration {iteration})",
        f"**{completed}/{total}** tests completed\n",
    ]

    if prev_results_map:
        prev_completed = sum(1 for p in prev_results_map.values() if p.get("status") == "COMPLETED")
        lines.append(f"Previous iteration: {prev_completed}/{len(prev_results_map)} completed")
        delta = completed - prev_completed
        if delta > 0:
            lines.append(f"Change: +{delta} tests now passing")
        elif delta < 0:
            lines.append(f"Change: {delta} tests regressed")
        else:
            lines.append("Change: no difference in pass count")
        lines.append("")

    for r in results:
        status_icon = "✓" if r["status"] == "COMPLETED" else "✗"
        lines.append(f"### {status_icon} {r['id']}: {r.get('description', '')}")
        lines.append(f"- Status: {r['status']}")
        lines.append(f"- Duration: {r['duration_ms']}ms")

        if r["id"] in prev_results_map:
            prev = prev_results_map[r["id"]]
            prev_status = prev.get("status", "?")
            prev_dur = prev.get("duration_ms", 0)
            if prev_status != r["status"]:
                lines.append(f"- vs prev: {prev_status} → {r['status']}")
            dur_diff = r["duration_ms"] - prev_dur
            if abs(dur_diff) > 1000:
                sign = "+" if dur_diff > 0 else ""
                lines.append(f"- Duration change: {sign}{dur_diff}ms")

        if r.get("error"):
            lines.append(f"- Error: {r['error']}")
        lines.append(f"- Response preview: {r.get('response_preview', '')[:200]}")
        lines.append(f"- Output dir: {r.get('output_dir', '')}")
        lines.append("")

    lines.append(f"\nFull results saved to: {eval_base_dir}")
    return "\n".join(lines)


@tool
def grade_eval(eval_dir: str, assertions_json: str) -> str:
    """Grade eval outputs against programmatic assertions and return a grading report.

    Reads the eval outputs from the specified directory and checks each assertion.
    Supported assertion types:
      - "file_exists": Check if a file was created in the eval output
      - "response_contains": Check if the response contains a substring
      - "response_not_contains": Check if the response does NOT contain a substring
      - "json_valid": Check if the response (or a specified file) is valid JSON
      - "regex_match": Check if the response matches a regex pattern
      - "min_tool_calls": Check minimum number of tool calls made
      - "tool_was_used": Check that a specific tool was called

    Args:
        eval_dir: Path to the eval iteration directory (e.g. "<workspace>/skill-eval/iteration-1").
        assertions_json: JSON array of assertions. Each element:
            {"test_id": "t1", "type": "response_contains", "value": "hello", "description": "Should greet user"}.

    Returns:
        A grading report with pass/fail for each assertion and a summary.
    """
    import json as _json
    import re as _re

    try:
        assertions = _json.loads(assertions_json)
    except _json.JSONDecodeError as e:
        return f"Error: invalid assertions_json — {e}"

    if not isinstance(assertions, list) or not assertions:
        return "Error: assertions_json must be a non-empty JSON array"

    if not os.path.isdir(eval_dir):
        return f"Error: eval directory not found — {eval_dir}"

    grading_results: list[dict] = []

    for assertion in assertions:
        test_id = assertion.get("test_id", "")
        a_type = assertion.get("type", "")
        a_value = assertion.get("value", "")
        a_desc = assertion.get("description", "")

        tc_dir = os.path.join(eval_dir, test_id)
        passed = False
        detail = ""

        if not os.path.isdir(tc_dir):
            grading_results.append({
                "test_id": test_id, "assertion": a_type, "description": a_desc,
                "passed": False, "detail": f"Test directory not found: {tc_dir}",
            })
            continue

        response_path = os.path.join(tc_dir, "response.md")
        response_text = ""
        if os.path.isfile(response_path):
            with open(response_path, "r") as f:
                response_text = f.read()

        tool_calls_path = os.path.join(tc_dir, "tool_calls.json")
        tool_calls: list = []
        if os.path.isfile(tool_calls_path):
            try:
                with open(tool_calls_path, "r") as f:
                    tool_calls = _json.load(f)
            except _json.JSONDecodeError:
                pass

        if a_type == "file_exists":
            target = os.path.join(tc_dir, a_value)
            passed = os.path.exists(target)
            detail = f"{'Found' if passed else 'Not found'}: {target}"

        elif a_type == "response_contains":
            passed = a_value.lower() in response_text.lower()
            detail = f"Looking for '{a_value}' in response ({len(response_text)} chars)"

        elif a_type == "response_not_contains":
            passed = a_value.lower() not in response_text.lower()
            detail = f"Checking absence of '{a_value}' in response"

        elif a_type == "json_valid":
            target_text = response_text
            if a_value:
                fpath = os.path.join(tc_dir, a_value)
                if os.path.isfile(fpath):
                    with open(fpath, "r") as f:
                        target_text = f.read()
            try:
                _json.loads(target_text)
                passed = True
                detail = "Valid JSON"
            except _json.JSONDecodeError as e:
                detail = f"Invalid JSON: {e}"

        elif a_type == "regex_match":
            match = _re.search(a_value, response_text, _re.DOTALL)
            passed = match is not None
            detail = f"Pattern: {a_value}"

        elif a_type == "min_tool_calls":
            actual_calls = len([t for t in tool_calls if "result" not in t])
            threshold = int(a_value)
            passed = actual_calls >= threshold
            detail = f"Tool calls: {actual_calls} (min: {threshold})"

        elif a_type == "tool_was_used":
            used_tools = {t.get("name", "") for t in tool_calls}
            passed = a_value in used_tools
            detail = f"Looking for '{a_value}' in {used_tools}"

        else:
            detail = f"Unknown assertion type: {a_type}"

        grading_results.append({
            "test_id": test_id, "assertion": a_type, "description": a_desc,
            "passed": passed, "detail": detail,
        })

    grading_path = os.path.join(eval_dir, "grading.json")
    with open(grading_path, "w") as f:
        _json.dump(grading_results, f, ensure_ascii=False, indent=2)

    total = len(grading_results)
    passed_count = sum(1 for g in grading_results if g["passed"])
    failed_count = total - passed_count

    lines = [
        f"## Grading Report",
        f"**{passed_count}/{total}** assertions passed ({failed_count} failed)\n",
    ]
    for g in grading_results:
        icon = "PASS" if g["passed"] else "FAIL"
        lines.append(f"- [{icon}] {g['test_id']} / {g['assertion']}: {g.get('description', '')}")
        lines.append(f"  {g.get('detail', '')}")

    lines.append(f"\nGrading saved to: {grading_path}")
    return "\n".join(lines)


@tool
def web_crawl(urls: str) -> dict:
    """Crawl one or more web pages to extract their full text content.

    Use this tool after web_search when you need the detailed content of specific
    web pages. Separate multiple URLs with a pipe '|'. All URLs are crawled in
    parallel by the backend service.

    Args:
        urls: One or more URLs separated by '|'.
              Example single: "https://example.com/article"
              Example multi:  "https://example.com/page1|https://example.com/page2|https://other.com/doc"

    Returns:
        A dict with 'results' (mapping URL -> page text content) and 'failed_urls'.
    """
    url_list = [u.strip() for u in urls.split("|") if u.strip()]
    if not url_list:
        return {"results": {}, "failed_urls": [], "error": "No valid URLs provided"}

    logger.info(f"[web_crawl] Crawling {len(url_list)} URLs")
    return _run_async(_crawl_batch_async(url_list))
