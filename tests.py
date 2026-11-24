import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("FLASK_SECRET_KEY", "test-only-secret")
os.environ["DEMO_MODE"] = "1"

from ai_service import METRIC_RANGES, PLAN_RESPONSE_SCHEMA, _validate_effects, recommend_plans
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


class GeminiStructuredOutputTests(unittest.TestCase):
    def test_plan_request_enforces_json_object_response(self):
        response_data = {
            "supported": True,
            "scenario_title": "校園服務改善",
            "recommendations": [
                {
                    "title": "方案甲",
                    "strategy": "分時處理",
                    "description": "依需求安排資源。",
                    "reason": "可以兼顧使用需求。",
                    "effects": {
                        "budget_remaining": -2,
                        "problem_improvement": 2,
                        "satisfaction": 1,
                        "fairness": 1,
                    },
                },
                {
                    "title": "方案乙",
                    "strategy": "集中處理",
                    "description": "集中資源改善問題。",
                    "reason": "可以快速處理主要問題。",
                    "effects": {
                        "budget_remaining": -3,
                        "problem_improvement": 3,
                        "satisfaction": 0,
                        "fairness": -1,
                    },
                },
            ],
            "rounds": [
                {
                    "event": "發現部分學生尚未了解安排。",
                    "actions": [
                        {
                            "text": "增加說明",
                            "effects": {
                                "budget_remaining": -1,
                                "problem_improvement": 1,
                                "satisfaction": 1,
                                "fairness": 0,
                            },
                        },
                        {
                            "text": "先觀察需求",
                            "effects": {
                                "budget_remaining": 0,
                                "problem_improvement": 0,
                                "satisfaction": 0,
                                "fairness": 1,
                            },
                        },
                    ],
                },
                {
                    "event": "試行後需要決定是否擴大範圍。",
                    "actions": [
                        {
                            "text": "擴大試行",
                            "effects": {
                                "budget_remaining": -1,
                                "problem_improvement": 2,
                                "satisfaction": 1,
                                "fairness": 0,
                            },
                        },
                        {
                            "text": "維持小規模",
                            "effects": {
                                "budget_remaining": 0,
                                "problem_improvement": 1,
                                "satisfaction": 0,
                                "fairness": 1,
                            },
                        },
                    ],
                },
                {
                    "event": "蒐集到更多使用情況，需要決定如何持續調整。",
                    "actions": [
                        {
                            "text": "依據意見微調安排",
                            "effects": {
                                "budget_remaining": -1,
                                "problem_improvement": 1,
                                "satisfaction": 1,
                                "fairness": 1,
                            },
                        },
                        {
                            "text": "維持現況並定期檢視",
                            "effects": {
                                "budget_remaining": 0,
                                "problem_improvement": 1,
                                "satisfaction": 0,
                                "fairness": 1,
                            },
                        },
                    ],
                },
            ],
        }
        mock_response = unittest.mock.Mock()
        mock_response.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{"text": json.dumps(response_data, ensure_ascii=False)}]
                }
            }]
        }
        game_config = {
            "metric_labels": {
                "budget_remaining": "剩餘預算",
                "problem_improvement": "問題改善",
                "satisfaction": "學生滿意度",
                "fairness": "公平性",
            },
            "initial_metrics": {
                "budget_remaining": 75,
                "problem_improvement": 75,
                "satisfaction": 75,
                "fairness": 75,
            },
        }

        with patch.dict(os.environ, {
            "DEMO_MODE": "0",
            "GEMINI_API_KEY": "test-key",
            "GEMINI_MODEL": "test-model",
        }):
            with patch("ai_service.send_request", return_value=mock_response) as send:
                result = recommend_plans("改善校園服務", [], game_config)

        request_data = send.call_args[0][2]
        self.assertEqual(
            request_data["generationConfig"]["responseSchema"]["type"],
            "OBJECT",
        )
        plan_effect_schema = PLAN_RESPONSE_SCHEMA["properties"]["recommendations"]["items"]["properties"]["effects"]
        action_effect_schema = PLAN_RESPONSE_SCHEMA["properties"]["rounds"]["items"]["properties"]["actions"]["items"]["properties"]["effects"]
        self.assertIn(
            "-20 到 0",
            plan_effect_schema["properties"]["budget_remaining"]["description"],
        )
        self.assertIn(
            "-10 到 0",
            action_effect_schema["properties"]["budget_remaining"]["description"],
        )
        self.assertIn('"effect_ranges"', request_data["contents"][0]["parts"][0]["text"])
        self.assertTrue(result["supported"])
        self.assertEqual(len(result["recommendations"]), 2)
        self.assertEqual(len(result["rounds"]), 3)

    def test_out_of_range_effect_error_names_field_and_bounds(self):
        effects = {
            "budget_remaining": 1,
            "problem_improvement": 0,
            "satisfaction": 0,
            "fairness": 0,
        }
        with self.assertRaisesRegex(ValueError, "budget_remaining=1.*-20～0"):
            _validate_effects(effects, METRIC_RANGES["plan"], "方案效果格式錯誤：")


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
        self.assertIn("1 / 3".encode("utf-8"), response.data)

        response = self.client.post(
            "/interview/answer",
            data={"answer": "\u6539\u5584\u4f7f\u7528\u6d41\u7a0b"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("2 / 3".encode("utf-8"), response.data)
        response = self.client.post(
            "/interview/answer",
            data={"answer": "\u516c\u5e73\u6027"},
            follow_redirects=True,
        )
        self.assertIn("3 / 3".encode("utf-8"), response.data)
        self.assertIn(
            "你認為要如何確認這項改善真的有效？".encode("utf-8"),
            response.data,
        )
        response = self.client.post(
            "/interview/answer",
            data={"answer": "持續收集使用者意見"},
            follow_redirects=True,
        )
        self.assertIn("校園服務改善示範".encode("utf-8"), response.data)

        response = self.client.post(
            "/simulation/start",
            data={"plan_id": "plan_1"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("回合 1 / 3".encode("utf-8"), response.data)
        self.assertIn("目前策略".encode("utf-8"), response.data)

        response = self.client.post(
            "/simulation/choose",
            data={"action_id": "r1_a1"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("回合 2 / 3".encode("utf-8"), response.data)
        self.assertIn("1 / 3 已完成".encode("utf-8"), response.data)
        self.assertRegex(response.get_data(as_text=True), r"[+-]\d+ 本回合")
        response = self.client.post(
            "/simulation/choose",
            data={"action_id": "r2_a1"},
            follow_redirects=True,
        )
        self.assertIn("回合 3 / 3".encode("utf-8"), response.data)
        response = self.client.post(
            "/simulation/choose",
            data={"action_id": "r3_a1"},
            follow_redirects=True,
        )
        self.assertIn("模擬結果".encode("utf-8"), response.data)

        with self.client.session_transaction() as session:
            self.assertLess(len(self.client.get_cookie("session").value.encode("utf-8")), 4096)


if __name__ == "__main__":
    unittest.main()
