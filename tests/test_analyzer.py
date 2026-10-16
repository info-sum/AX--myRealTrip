import json
import unittest
from pathlib import Path

from trip_graph_rescue import analyze_trip


FIXTURE = Path(__file__).parents[1] / "fixtures" / "paris_flight_delay.json"


class TripGraphRescueTests(unittest.TestCase):
    def setUp(self):
        self.payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.brief = analyze_trip(self.payload)
        self.nodes = {node["id"]: node for node in self.brief["graph"]}

    def test_delay_propagates_to_transfer_checkin_and_first_day_tour(self):
        self.assertEqual(self.nodes["flight_icn_cdg"]["actual_end"], "2026-09-01T19:00:00+02:00")
        self.assertEqual(self.nodes["airport_to_hotel"]["actual_end"], "2026-09-01T20:00:00+02:00")
        self.assertEqual(self.nodes["hotel_checkin"]["actual_start"], "2026-09-01T20:00:00+02:00")
        self.assertEqual(self.nodes["first_day_tour"]["actual_start"], "2026-09-01T20:35:00+02:00")

    def test_first_day_tour_is_unavailable_with_explicit_time_evidence(self):
        tour = self.nodes["first_day_tour"]
        self.assertEqual(tour["status"], "unavailable")
        self.assertIn("arrival after tour meeting time", tour["calculation"])

    def test_late_checkin_missing_policy_requires_counselor_confirmation(self):
        self.assertEqual(self.nodes["hotel_checkin"]["approval"], "counselor_confirmation_required")

    def test_only_non_conflicting_alternatives_are_candidates(self):
        options = {option["id"]: option for option in self.brief["alternatives"]}
        self.assertEqual(options["alternative_a_next_day"]["status"], "candidate")
        self.assertEqual(options["alternative_b_night"]["status"], "candidate")
        self.assertEqual(options["alternative_c_keep_original"]["status"], "excluded")

    def test_output_has_no_execution_capability(self):
        self.assertEqual(self.brief["prohibited_actions"], ["refund", "rebook", "send_customer_message", "production_api_call"])

    def test_safety_event_always_adds_human_approval(self):
        self.payload["event"] = {"type": "safety_issue", "node_id": "flight_icn_cdg"}
        brief = analyze_trip(self.payload)
        self.assertIn("operations_lead_or_safety_approval_required", brief["approval_gates"])


if __name__ == "__main__":
    unittest.main()
