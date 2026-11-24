import os
import unittest
from pathlib import Path

os.environ.setdefault("FLASK_SECRET_KEY", "test-only-secret")
os.environ["DEMO_MODE"] = "1"

from app import app
from simulation import apply_effects, calculate_total_score, make_comment, run_round_choice


class SimulationScoreTests(unittest.TestCase):
    def test_lowest_score(self):
        metrics = {
            "budget_remaining": 75,
            "problem_improvement": 75,
            "satisfaction": 75,
            "fairness": 75,
        }
        plan = {
            "budget_remaining": -20,
            "problem_improvement": 0,
            "satisfaction": -10,
            "fairness": -10,
        }
        metrics = apply_effects(metrics, plan)
        action = {
            "budget_remaining": -10,
            "problem_improvement": -5,
            "satisfaction": -5,
            "fairness": -5,
        }
        metrics = run_round_choice(metrics, action)
        metrics = run_round_choice(metrics, action)
        self.assertEqual(metrics, {
            "budget_remaining": 35,
            "problem_improvement": 65,
            "satisfaction": 55,
            "fairness": 55,
        })
        self.assertEqual(calculate_total_score(metrics), 53)

    def test_highest_score_and_comment(self):
        metrics = {
            "budget_remaining": 75,
            "problem_improvement": 75,
            "satisfaction": 75,
            "fairness": 75,
        }
        plan = {
            "budget_remaining": 0,
            "problem_improvement": 20,
            "satisfaction": 10,
            "fairness": 10,
        }
        metrics = apply_effects(metrics, plan)
        action = {
            "budget_remaining": 0,
            "problem_improvement": 5,
            "satisfaction": 5,
            "fairness": 5,
        }
        metrics = run_round_choice(metrics, action)
        metrics = run_round_choice(metrics, action)
        self.assertEqual(metrics, {
            "budget_remaining": 75,
            "problem_improvement": 100,
            "satisfaction": 95,
            "fairness": 95,
        })
        score = calculate_total_score(metrics)
        self.assertEqual(score, 91)
        self.assertIn("整體", make_comment(score))
        self.assertTrue(score >= 80)


class OfflineDemoTests(unittest.TestCase):
    def setUp(self):
        self.records_file = Path(__file__).resolve().parent / "data" / "records.json"
        self.original_records = self.records_file.read_bytes()
        app.config["TESTING"] = True
        self.client = app.test_client()
        with self.client.session_transaction() as session:
            session.clear()

    def tearDown(self):
        self.records_file.write_bytes(self.original_records)

    def test_offline_demo_completes_without_gemini_requests(self):
        response = self.client.post(
            "/interview/start",
            data={"proposal": "校園圖書館座位不足，學生常找不到安靜的閱讀空間。"},
            follow_redirects=True,
        )
        self.assertIn("離線示範模式".encode("utf-8"), response.data)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            "/interview/answer",
            data={"answer": "\u6539\u5584\u4f7f\u7528\u6d41\u7a0b"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.post(
            "/interview/answer",
            data={"answer": "\u516c\u5e73\u6027"},
            follow_redirects=True,
        )
        self.assertIn("校園服務改善示範".encode("utf-8"), response.data)

        response = self.client.post(
            "/simulation/start",
            data={"plan_id": "plan_1"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            "/simulation/choose",
            data={"action_id": "r1_a1"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.post(
            "/simulation/choose",
            data={"action_id": "r2_a1"},
            follow_redirects=True,
        )
        self.assertIn("模擬結果".encode("utf-8"), response.data)

        with self.client.session_transaction() as session:
            self.assertLess(len(self.client.get_cookie("session").value.encode("utf-8")), 4096)


if __name__ == "__main__":
    unittest.main()
