#!/usr/bin/env python3
"""Generate an HTML report from DeepEval JSON result files.

Usage:
    python scripts/generate_eval_report.py [results_dir] [output_file]

Defaults:
    results_dir  ./deepeval-results
    output_file  ./deepeval-results/report.html
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

# ── helpers ───────────────────────────────────────────────────────────────────

METRIC_TAG_CLASS: dict[str, str] = {
    "Answer Relevancy": "tag-relevancy",
    "Faithfulness": "tag-faithfulness",
    "Helpfulness [GEval]": "tag-helpfulness",
    "Tool Correctness": "tag-tool",
    "AppropriateUncertainty [GEval]": "tag-uncertainty",
    "Latency": "tag-latency",
    "Cost": "tag-cost",
    "Response Length": "tag-length",
}

METRIC_DISPLAY_COLOR: dict[str, str] = {
    "Answer Relevancy": "#60a5fa",
    "Faithfulness": "#a78bfa",
    "Helpfulness [GEval]": "#22d3ee",
    "Tool Correctness": "#86efac",
    "AppropriateUncertainty [GEval]": "#eab308",
    "Latency": "#fb923c",
    "Cost": "#f472b6",
    "Response Length": "#67e8f9",
}

METRIC_BG_COLOR: dict[str, str] = {
    "Answer Relevancy": "#1e3a5f",
    "Faithfulness": "#2a1e5f",
    "Helpfulness [GEval]": "#1a2e40",
    "Tool Correctness": "#1f2e1a",
    "AppropriateUncertainty [GEval]": "#2e2a1a",
    "Latency": "#2e1e1a",
    "Cost": "#2a1f2e",
    "Response Length": "#1a2a2e",
}


def score_color(score: float, threshold: float) -> str:
    ratio = score / threshold if threshold > 0 else 1.0
    if ratio >= 1.0:
        return "high"
    if ratio >= 0.8:
        return "mid"
    return "low"


def bar_class(score: float, threshold: float) -> str:
    ratio = score / threshold if threshold > 0 else 1.0
    if ratio >= 1.0:
        return "bar-high"
    if ratio >= 0.8:
        return "bar-mid"
    return "bar-low"


def bar_width(score: float) -> int:
    return min(100, int(score * 100))


def esc(text: str) -> str:
    return (
        text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    )


# ── data loading ──────────────────────────────────────────────────────────────


def load_result_files(results_dir: Path) -> list[dict]:
    """Load all DeepEval JSON result files from a directory."""
    runs: list[dict] = []
    if not results_dir.exists():
        print(f"[warn] results directory not found: {results_dir}", file=sys.stderr)
        return runs
    for path in sorted(results_dir.iterdir()):
        if not path.is_file() or path.suffix == ".html":
            continue
        try:
            with open(path) as f:
                data = json.load(f)
            if "testCases" in data:
                data["_source_file"] = path.name
                runs.append(data)
        except json.JSONDecodeError, UnicodeDecodeError:
            pass
    return runs


# ── HTML generation ───────────────────────────────────────────────────────────

CSS = """
  :root {
    --bg:#0f1117;--surface:#1a1d27;--surface2:#22263a;--border:#2e3248;
    --text:#e2e4f0;--muted:#7c82a0;
    --green:#22c55e;--green-bg:#0d2e1a;
    --red:#ef4444;--red-bg:#2e0d0d;
    --yellow:#eab308;--blue:#60a5fa;--purple:#a78bfa;
    --cyan:#22d3ee;--orange:#fb923c;--pink:#f472b6;
  }
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
       background:var(--bg);color:var(--text);min-height:100vh;padding:2rem 1.5rem}
  .container{max-width:1100px;margin:0 auto}
  /* header */
  .header{display:flex;align-items:flex-start;justify-content:space-between;
          gap:1rem;margin-bottom:2rem;flex-wrap:wrap}
  .header-left h1{font-size:1.75rem;font-weight:700;letter-spacing:-.02em}
  .header-left .subtitle{color:var(--muted);margin-top:.25rem;font-size:.875rem}
  .badge-pass{background:var(--green-bg);color:var(--green);
              border:1px solid #15803d44;border-radius:999px;
              padding:.35rem 1rem;font-size:.875rem;font-weight:600;white-space:nowrap}
  .badge-fail{background:var(--red-bg);color:var(--red);
              border:1px solid #ef444433;border-radius:999px;
              padding:.35rem 1rem;font-size:.875rem;font-weight:600;white-space:nowrap}
  /* summary cards */
  .summary{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));
           gap:1rem;margin-bottom:2rem}
  .stat{background:var(--surface);border:1px solid var(--border);border-radius:12px;
        padding:1.25rem 1.5rem}
  .stat-label{font-size:.75rem;color:var(--muted);text-transform:uppercase;
              letter-spacing:.08em;margin-bottom:.5rem}
  .stat-value{font-size:1.75rem;font-weight:700;line-height:1}
  .stat-value.green{color:var(--green)}.stat-value.blue{color:var(--blue)}
  .stat-value.purple{color:var(--purple)}.stat-value.cyan{color:var(--cyan)}
  .stat-sub{font-size:.75rem;color:var(--muted);margin-top:.35rem}
  /* section */
  .section{margin-bottom:2rem}
  .section-header{display:flex;align-items:center;gap:.75rem;margin-bottom:.75rem}
  .section-title{font-size:1rem;font-weight:600}
  .section-tag{font-size:.7rem;padding:.2rem .6rem;border-radius:999px;
               font-weight:600;text-transform:uppercase;letter-spacing:.06em}
  .section-count{font-size:.75rem;color:var(--muted);margin-left:auto}
  /* table */
  .table-wrap{background:var(--surface);border:1px solid var(--border);
              border-radius:12px;overflow:hidden}
  table{width:100%;border-collapse:collapse;font-size:.875rem}
  thead th{background:var(--surface2);color:var(--muted);font-size:.7rem;
           text-transform:uppercase;letter-spacing:.08em;padding:.75rem 1rem;
           text-align:left;font-weight:600;border-bottom:1px solid var(--border)}
  tbody tr{border-bottom:1px solid var(--border);transition:background .1s}
  tbody tr:last-child{border-bottom:none}
  tbody tr:hover{background:var(--surface2)}
  td{padding:.9rem 1rem;vertical-align:top}
  .test-name{font-family:'SF Mono','Menlo',monospace;font-size:.78rem;
             color:var(--text);word-break:break-word}
  .test-input{color:var(--muted);font-size:.8rem;margin-top:.3rem;
              line-height:1.4;max-width:320px}
  /* score */
  .score-cell{white-space:nowrap;min-width:120px}
  .score-top{display:flex;align-items:baseline;gap:.4rem;margin-bottom:.35rem}
  .score-num{font-weight:700;font-size:1rem}
  .score-threshold{font-size:.7rem;color:var(--muted)}
  .bar-track{height:5px;background:var(--border);border-radius:999px;
             overflow:hidden;width:80px}
  .bar-fill{height:100%;border-radius:999px}
  .high{color:var(--green)}.mid{color:var(--yellow)}.low{color:var(--red)}
  .bar-high{background:var(--green)}.bar-mid{background:var(--yellow)}
  .bar-low{background:var(--red)}
  /* pill */
  .pill{display:inline-flex;align-items:center;gap:.3rem;padding:.2rem .6rem;
        border-radius:999px;font-size:.72rem;font-weight:600}
  .pill-pass{background:var(--green-bg);color:var(--green);
             border:1px solid #22c55e33}
  .pill-fail{background:var(--red-bg);color:var(--red);border:1px solid #ef444433}
  .dot{width:6px;height:6px;border-radius:50%;background:currentColor}
  .reason{font-size:.78rem;color:var(--muted);line-height:1.5;max-width:360px}
  /* metric tag colors */
  .tag-relevancy{background:#1e3a5f;color:#60a5fa}
  .tag-faithfulness{background:#2a1e5f;color:#a78bfa}
  .tag-helpfulness{background:#1a2e40;color:#22d3ee}
  .tag-tool{background:#1f2e1a;color:#86efac}
  .tag-uncertainty{background:#2e2a1a;color:#eab308}
  .tag-latency{background:#2e1e1a;color:#fb923c}
  .tag-cost{background:#2a1f2e;color:#f472b6}
  .tag-length{background:#1a2a2e;color:#67e8f9}
  /* run tabs */
  .run-label{font-size:.7rem;color:var(--muted);background:var(--surface2);
             border:1px solid var(--border);border-radius:6px;
             padding:.15rem .5rem;font-family:monospace}
  /* footer */
  .footer{text-align:center;color:var(--muted);font-size:.75rem;
          margin-top:3rem;padding-top:1.5rem;border-top:1px solid var(--border)}
"""


def metric_pill(name: str) -> str:
    bg = METRIC_BG_COLOR.get(name, "#222")
    fg = METRIC_DISPLAY_COLOR.get(name, "#aaa")
    return (
        f'<span class="pill" style="background:{bg};color:{fg};'
        f'border:1px solid {fg}33;font-size:.68rem">{esc(name)}</span>'
    )


def render_test_row(tc: dict, show_metric_pill: bool = False) -> str:
    name = esc(tc.get("name", ""))
    inp = esc((tc.get("input") or "")[:120])
    overall_pass = tc.get("success", False)
    status_pill = (
        '<span class="pill pill-pass"><span class="dot"></span>Pass</span>'
        if overall_pass
        else '<span class="pill pill-fail"><span class="dot"></span>Fail</span>'
    )
    metrics_html = ""
    for m in tc.get("metricsData", []):
        mname = m.get("name", "")
        score = float(m.get("score") or 0)
        threshold = float(m.get("threshold") or 1)
        reason = esc((m.get("reason") or "")[:300])
        sc = score_color(score, threshold)
        bc = bar_class(score, threshold)
        bw = bar_width(score)
        pill_html = metric_pill(mname) + "<br>" if show_metric_pill else ""
        metrics_html += f"""
        <tr>
          <td><div class="test-name">{name}</div>
              <div class="test-input">{inp}</div></td>
          <td>{pill_html if show_metric_pill else ""}</td>
          <td class="score-cell">
            <div class="score-top">
              <span class="score-num {sc}">{score:.2f}</span>
              <span class="score-threshold">/ {threshold}</span>
            </div>
            <div class="bar-track"><div class="bar-fill {bc}" style="width:{bw}%"></div></div>
          </td>
          <td>{status_pill}</td>
          <td><div class="reason">{reason}</div></td>
        </tr>"""
    return metrics_html


def group_by_metric(test_cases: list[dict]) -> dict[str, list[tuple[dict, dict]]]:
    """Return {metric_name: [(test_case, metric_data), ...]}."""
    groups: dict[str, list[tuple[dict, dict]]] = {}
    for tc in test_cases:
        for m in tc.get("metricsData", []):
            mname = m.get("name", "Unknown")
            groups.setdefault(mname, []).append((tc, m))
    return groups


def render_metric_section(metric_name: str, entries: list[tuple[dict, dict]]) -> str:
    tag_cls = METRIC_TAG_CLASS.get(metric_name, "tag-relevancy")
    total = len(entries)
    threshold = entries[0][1].get("threshold", 1) if entries else 1

    rows = ""
    for tc, m in entries:
        name = esc(tc.get("name", ""))
        inp = esc((tc.get("input") or "")[:120])
        score = float(m.get("score") or 0)
        thr = float(m.get("threshold") or 1)
        reason = esc((m.get("reason") or "")[:300])
        sc = score_color(score, thr)
        bc = bar_class(score, thr)
        bw = bar_width(score)
        status = (
            '<span class="pill pill-pass"><span class="dot"></span>Pass</span>'
            if m.get("success", False)
            else '<span class="pill pill-fail"><span class="dot"></span>Fail</span>'
        )
        rows += f"""
        <tr>
          <td><div class="test-name">{name}</div>
              <div class="test-input">{inp}</div></td>
          <td class="score-cell">
            <div class="score-top">
              <span class="score-num {sc}">{score:.2f}</span>
              <span class="score-threshold">/ {thr}</span>
            </div>
            <div class="bar-track">
              <div class="bar-fill {bc}" style="width:{bw}%"></div>
            </div>
          </td>
          <td>{status}</td>
          <td><div class="reason">{reason}</div></td>
        </tr>"""

    return f"""
  <div class="section">
    <div class="section-header">
      <span class="section-tag {tag_cls}">{esc(metric_name)}</span>
      <span class="section-count">{total} test{"s" if total != 1 else ""} &nbsp;·&nbsp; threshold {threshold}</span>
    </div>
    <div class="table-wrap">
      <table>
        <thead><tr>
          <th>Test</th><th>Score</th><th>Status</th><th>Reason</th>
        </tr></thead>
        <tbody>{rows}
        </tbody>
      </table>
    </div>
  </div>"""


def render_run(run: dict, run_index: int, total_runs: int) -> str:
    test_cases = run.get("testCases", [])
    test_file = run.get("testFile", "evals/")
    source = run.get("_source_file", "")
    passed = sum(1 for tc in test_cases if tc.get("success", False))
    total = len(test_cases)
    total_cost = sum(
        float(m.get("evaluationCost") or 0) for tc in test_cases for m in tc.get("metricsData", [])
    )
    eval_models = {
        m.get("evaluationModel", "")
        for tc in test_cases
        for m in tc.get("metricsData", [])
        if m.get("evaluationModel")
    }
    eval_model = next(iter(eval_models), "—")
    metric_types = {m.get("name", "") for tc in test_cases for m in tc.get("metricsData", [])}

    all_pass = passed == total
    badge = (
        f'<div class="badge-pass">✓ {passed} / {total} passed</div>'
        if all_pass
        else f'<div class="badge-fail">✗ {passed} / {total} passed</div>'
    )

    run_label = f'<span class="run-label">{esc(source)}</span>' if total_runs > 1 else ""

    summary = f"""
  <div class="summary">
    <div class="stat">
      <div class="stat-label">Tests Passed</div>
      <div class="stat-value {"green" if all_pass else "red"}">{passed} / {total}</div>
      <div class="stat-sub">{int(passed / total * 100) if total else 0}% pass rate</div>
    </div>
    <div class="stat">
      <div class="stat-label">Eval Cost</div>
      <div class="stat-value blue">${total_cost:.4f}</div>
      <div class="stat-sub">LLM-as-a-judge calls</div>
    </div>
    <div class="stat">
      <div class="stat-label">Judge Model</div>
      <div class="stat-value purple" style="font-size:1rem;padding-top:.3rem">
        {esc(eval_model.split(" ")[0].split("-")[-1] if eval_model else "—")}
      </div>
      <div class="stat-sub">{esc(eval_model)}</div>
    </div>
    <div class="stat">
      <div class="stat-label">Metric Types</div>
      <div class="stat-value cyan">{len(metric_types)}</div>
      <div class="stat-sub">{esc(" · ".join(sorted(metric_types)[:3]) + (" · +" + str(len(metric_types) - 3) if len(metric_types) > 3 else ""))}</div>
    </div>
  </div>"""

    if total_runs > 1:
        header = f"""
  <div class="header">
    <div class="header-left">
      <h1>Run {run_index + 1} {run_label}</h1>
      <div class="subtitle">{esc(test_file)}</div>
    </div>
    {badge}
  </div>"""
    else:
        header = ""

    groups = group_by_metric(test_cases)
    sections = "".join(render_metric_section(mname, entries) for mname, entries in groups.items())

    return header + summary + sections


def generate_report(runs: list[dict], generated_at: str) -> str:
    total_tests = sum(len(r.get("testCases", [])) for r in runs)
    total_passed = sum(
        sum(1 for tc in r.get("testCases", []) if tc.get("success", False)) for r in runs
    )
    all_pass = total_passed == total_tests

    main_badge = (
        f'<div class="badge-pass">✓ {total_passed} / {total_tests} passed</div>'
        if all_pass
        else f'<div class="badge-fail">✗ {total_passed} / {total_tests} passed</div>'
    )

    bodies = "".join(render_run(r, i, len(runs)) for i, r in enumerate(runs))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>DeepEval Report — PDF Agent</title>
<style>{CSS}</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div class="header-left">
      <h1>DeepEval Report</h1>
      <div class="subtitle">PDF Agent &nbsp;·&nbsp; {esc(generated_at)}</div>
    </div>
    {main_badge}
  </div>
{bodies}
  <div class="footer">
    Generated by <code>scripts/generate_eval_report.py</code>
    &nbsp;·&nbsp; PDF Agent &nbsp;·&nbsp; {esc(generated_at)}
  </div>
</div>
</body>
</html>"""


# ── main ──────────────────────────────────────────────────────────────────────


def main() -> int:
    results_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("deepeval-results")
    output_file = Path(sys.argv[2]) if len(sys.argv) > 2 else results_dir / "report.html"

    runs = load_result_files(results_dir)
    if not runs:
        print(f"[error] no DeepEval result files found in {results_dir}", file=sys.stderr)
        return 1

    generated_at = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    html = generate_report(runs, generated_at)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(html, encoding="utf-8")
    print(f"Report written to {output_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
