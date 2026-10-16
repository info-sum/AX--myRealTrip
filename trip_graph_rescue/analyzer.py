"""Pure, deterministic impact propagation for de-identified travel fixtures."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

HIGH_RISK_EVENTS = {"weather_local_issue", "safety_issue", "dispute"}


def _time(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _iso(value: datetime) -> str:
    return value.isoformat()


def analyze_trip(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a brief only and never perform external or irreversible actions."""
    nodes = {node["id"]: node for node in payload["nodes"]}
    event = payload["event"]
    resolved: dict[str, dict[str, Any]] = {}

    def resolve(node_id: str) -> dict[str, Any]:
        if node_id in resolved:
            return resolved[node_id]

        node = nodes[node_id]
        scheduled_start = _time(node["scheduled_start"])
        scheduled_end = _time(node["scheduled_end"])
        required_ends = [_time(resolve(required)["actual_end"]) for required in node.get("requires", [])]
        ready_at = max(required_ends, default=scheduled_start)
        actual_start = max(scheduled_start, ready_at + timedelta(minutes=node.get("buffer_after_requirements_minutes", 0)))

        if node_id == event["node_id"] and event["type"] == "flight_delayed":
            actual_end = scheduled_end + timedelta(minutes=event["delay_minutes"])
            actual_start = scheduled_start
        elif node.get("duration_minutes", 0):
            actual_end = actual_start + timedelta(minutes=node["duration_minutes"])
        else:
            actual_end = actual_start

        status = "on_time" if actual_start <= scheduled_start and actual_end <= scheduled_end else "impacted"
        result = {
            "id": node_id,
            "kind": node["kind"],
            "status": status,
            "scheduled_start": _iso(scheduled_start),
            "actual_start": _iso(actual_start),
            "actual_end": _iso(actual_end),
            "approval": node["approval"],
            "calculation": [],
        }
        if node_id == event["node_id"] and event["type"] == "flight_delayed":
            result["calculation"].append(
                f"scheduled arrival {_iso(scheduled_end)} + {event['delay_minutes']} minutes = {_iso(actual_end)}"
            )
        if required_ends:
            result["calculation"].append(f"latest required completion = {_iso(ready_at)}")
        if node.get("buffer_after_requirements_minutes", 0):
            result["calculation"].append(
                f"required completion + {node['buffer_after_requirements_minutes']} minute buffer = {_iso(actual_start)}"
            )
        if node.get("late_checkin_policy") == "confirmation_required" and actual_start > scheduled_start:
            result["approval"] = "counselor_confirmation_required"
            result["calculation"].append("late check-in policy is unconfirmed")
        if actual_start > scheduled_start and node["kind"] == "tour":
            result["status"] = "unavailable"
            result["calculation"].append("arrival after tour meeting time")
        resolved[node_id] = result
        return result

    graph = [resolve(node["id"]) for node in payload["nodes"]]
    first_tour = resolved.get("first_day_tour")
    availability_threshold = _time(first_tour["actual_start"]) if first_tour else None
    alternatives = []
    for option in payload.get("alternatives", []):
        start = _time(option["start"])
        permitted = availability_threshold is None or start >= availability_threshold
        alternatives.append(
            {
                **option,
                "status": "candidate" if permitted else "excluded",
                "reason": "meets calculated arrival constraint" if permitted else "starts before traveler can reach the meeting point",
                "approval": "counselor_approval_required" if option["policy"] != "not_applicable" else "not_applicable",
            }
        )

    approvals = sorted({item["approval"] for item in graph if item["approval"] != "auto_information_allowed"})
    if event["type"] in HIGH_RISK_EVENTS:
        approvals.append("operations_lead_or_safety_approval_required")

    return {
        "synthetic": payload.get("synthetic") is True,
        "trip_id": payload["trip_id"],
        "event": event,
        "graph": graph,
        "alternatives": alternatives,
        "approval_gates": sorted(set(approvals)),
        "prohibited_actions": ["refund", "rebook", "send_customer_message", "production_api_call"],
        "customer_message_draft": {
            "confirmed_facts": ["The arrival delay affects the first-day tour meeting time"],
            "options": ["A counselor will confirm eligible replacement options"],
            "follow_up": ["A counselor will confirm hotel late check-in policy before any commitment"],
        },
    }
