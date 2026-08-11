from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.cli import configure_utf8_stdio

REQUIRED_ALERT_FIELDS = ("name", "severity", "condition", "type", "owner", "runbook")
VALID_SEVERITIES = {"critical", "warning", "info"}

# Anh xa SLI trong config/slo.yaml sang aggregation/threshold tuong ung
# trong config/dashboard.yaml, de bat loi lech so giua hai file.
SLO_TO_DASHBOARD_PANEL = {
    "latency_p95_ms": "latency",
    "error_rate_pct": "errors",
    "daily_cost_usd": "cost",
    "quality_score_avg": "quality",
}

RUNBOOK_HEADING_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)


class AlertsConfigError(ValueError):
    pass


def _slugify(heading: str) -> str:
    slug = heading.strip().lower()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug).strip("-")
    return slug


def load_yaml(path: Path, label: str) -> dict:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise AlertsConfigError(f"Khong tim thay {label}: {path}") from exc
    except yaml.YAMLError as exc:
        raise AlertsConfigError(f"{label} khong phai YAML hop le: {exc}") from exc
    if not isinstance(payload, dict):
        raise AlertsConfigError(f"{label} phai la mot YAML object")
    return payload


def validate_alert_rules(alerts_path: Path, runbook_path: Path) -> list[str]:
    errors: list[str] = []

    payload = load_yaml(alerts_path, "alert_rules.yaml")
    alerts = payload.get("alerts")
    if not isinstance(alerts, list) or len(alerts) < 3:
        raise AlertsConfigError("'alerts' phai la danh sach co it nhat 3 alert")

    runbook_text = runbook_path.read_text(encoding="utf-8") if runbook_path.exists() else ""
    runbook_slugs = {_slugify(h) for h in RUNBOOK_HEADING_RE.findall(runbook_text)}

    for index, alert in enumerate(alerts):
        label = f"alerts[{index}]"
        if not isinstance(alert, dict):
            errors.append(f"{label} phai la mot YAML object")
            continue

        for field in REQUIRED_ALERT_FIELDS:
            value = alert.get(field)
            if value is None or (isinstance(value, str) and not value.strip()):
                errors.append(f"{label}.{field} bi thieu hoac rong")
            elif isinstance(value, str) and "TODO" in value.upper():
                errors.append(f"{label}.{field} van con gia tri TODO")

        severity = alert.get("severity")
        if isinstance(severity, str) and severity.lower() not in VALID_SEVERITIES:
            errors.append(
                f"{label}.severity='{severity}' khong hop le (chi nhan {sorted(VALID_SEVERITIES)})"
            )

        name = alert.get("name")
        condition = alert.get("condition")
        if isinstance(name, str) and isinstance(condition, str):
            implementation_names = {"rag_slow", "tool_fail", "cost_spike"}
            lowered = f"{name} {condition}".lower()
            hit = {n for n in implementation_names if n in lowered}
            if hit:
                errors.append(
                    f"{label} du a tren ten incident noi bo {sorted(hit)}; "
                    "alert phai symptom-based (dua tren SLI/SLO), khong dua vao ten scenario"
                )

        runbook_ref = alert.get("runbook")
        if isinstance(runbook_ref, str) and "#" in runbook_ref:
            _, anchor = runbook_ref.split("#", 1)
            if anchor not in runbook_slugs:
                errors.append(
                    f"{label}.runbook trỏ toi anchor '#{anchor}' nhung khong tim thay heading "
                    f"tuong ung trong {runbook_path}"
                )

    return errors


def validate_slo_vs_dashboard(slo_path: Path, dashboard_path: Path) -> list[str]:
    errors: list[str] = []

    slo_payload = load_yaml(slo_path, "slo.yaml")
    slis = slo_payload.get("slis")
    if not isinstance(slis, dict):
        raise AlertsConfigError("'slis' phai la mot YAML object trong slo.yaml")

    dashboard_payload = load_yaml(dashboard_path, "dashboard.yaml")
    panels = dashboard_payload.get("dashboard", {}).get("panels", [])
    panel_thresholds = {
        panel["id"]: panel["threshold"]
        for panel in panels
        if isinstance(panel, dict) and "id" in panel and "threshold" in panel
    }

    for sli_name, panel_id in SLO_TO_DASHBOARD_PANEL.items():
        sli = slis.get(sli_name)
        if not isinstance(sli, dict) or "objective" not in sli:
            errors.append(f"slis.{sli_name}.objective bi thieu trong slo.yaml")
            continue

        threshold = panel_thresholds.get(panel_id)
        if threshold is None:
            errors.append(
                f"Khong tim thay panel '{panel_id}' trong dashboard.yaml de doi chieu voi slis.{sli_name}"
            )
            continue

        objective = sli["objective"]
        value = threshold.get("value")
        if objective != value:
            errors.append(
                f"Lech so: slis.{sli_name}.objective={objective} nhung "
                f"dashboard panel '{panel_id}'.threshold.value={value}"
            )

    return errors


def main() -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description="Kiem tra alert rules, runbook va doi chieu SLO/dashboard")
    parser.add_argument("--alerts", type=Path, default=REPO_ROOT / "config" / "alert_rules.yaml")
    parser.add_argument("--runbook", type=Path, default=REPO_ROOT / "docs" / "alerts.md")
    parser.add_argument("--slo", type=Path, default=REPO_ROOT / "config" / "slo.yaml")
    parser.add_argument("--dashboard", type=Path, default=REPO_ROOT / "config" / "dashboard.yaml")
    args = parser.parse_args()

    all_errors: list[str] = []
    try:
        all_errors.extend(validate_alert_rules(args.alerts, args.runbook))
        all_errors.extend(validate_slo_vs_dashboard(args.slo, args.dashboard))
    except AlertsConfigError as exc:
        print(f"KHONG HOP LE: {exc}")
        return 1

    if all_errors:
        print("KHONG HOP LE:")
        for err in all_errors:
            print(f"  - {err}")
        return 1

    print("HOP LE: alert rules, runbook va SLO/dashboard threshold khop nhau.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
