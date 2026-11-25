import json
import os
import requests
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

os.environ.setdefault("FLASK_SECRET_KEY", "test-only-secret")
os.environ["DEMO_MODE"] = "1"

from ai_service import METRIC_RANGES, PLAN_RESPONSE_SCHEMA, _validate_effects, recommend_plans, send_request
from app import GAMES, app
from campus_simulation import advance_campaign, new_campaign
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


class GeminiRequestTests(unittest.TestCase):
    def test_timeout_is_bounded_and_not_retried_automatically(self):
        with patch(
            "ai_service.requests.post",
            side_effect=requests.exceptions.ReadTimeout,
        ) as post:
            with self.assertRaisesRegex(TimeoutError, "回應上限 30 秒"):
                send_request("https://example.test/generate", {}, {})

        post.assert_called_once_with(
            "https://example.test/generate",
            headers={},
            json={},
            timeout=(5, 30),
        )

    def test_service_unavailable_retries_twice_then_succeeds(self):
        unavailable = Mock(status_code=503)
        still_unavailable = Mock(status_code=503)
        success = Mock(status_code=200)
        with (
            patch(
                "ai_service.requests.post",
                side_effect=[unavailable, still_unavailable, success],
            ) as post,
            patch("ai_service.time.sleep") as sleep,
        ):
            response = send_request("https://example.test/generate", {}, {})

        self.assertIs(response, success)
        self.assertEqual(post.call_count, 3)
        self.assertEqual(
            [call.args[0] for call in sleep.call_args_list],
            [2, 4],
        )

    def test_repeated_service_unavailable_reports_retry_failure(self):
        unavailable = Mock(status_code=503)
        with (
            patch(
                "ai_service.requests.post",
                side_effect=[unavailable, unavailable, unavailable],
            ) as post,
            patch("ai_service.time.sleep") as sleep,
        ):
            with self.assertRaisesRegex(RuntimeError, "已自動重試兩次仍失敗"):
                send_request("https://example.test/generate", {}, {})

        self.assertEqual(post.call_count, 3)
        self.assertEqual(
            [call.args[0] for call in sleep.call_args_list],
            [2, 4],
        )


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
        self.assertIn('id="campus-map"'.encode("utf-8"), response.data)
        self.assertIn('data-map-metric="fairness"'.encode("utf-8"), response.data)
        for label in ("剩餘預算", "問題改善", "學生滿意度", "公平性"):
            self.assertIn(label.encode("utf-8"), response.data)
        for location in ("圖書館</text>", "行政樓</text>", "學生中心</text>", "共融步道</text>"):
            self.assertNotIn(location.encode("utf-8"), response.data)

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
            headers={"X-Game-Update": "1"},
        )
        self.assertIn('data-game-update'.encode("utf-8"), response.data)
        self.assertIn('data-round-number="3"'.encode("utf-8"), response.data)
        self.assertNotIn('id="campus-map"'.encode("utf-8"), response.data)
        response = self.client.post(
            "/simulation/choose",
            data={"action_id": "r3_a1"},
            follow_redirects=True,
            headers={"X-Game-Update": "1"},
        )
        self.assertIn("模擬結果".encode("utf-8"), response.data)
        self.assertEqual(response.request.path, "/result")

        with self.client.session_transaction() as session:
            self.assertLess(len(self.client.get_cookie("session").value.encode("utf-8")), 4096)

    def test_interview_start_timeout_keeps_retryable_session(self):
        question = {"question": "先改善哪個面向？", "options": ["改善流程", "增加資源"]}
        with patch(
            "app.ask_interview_question",
            side_effect=[TimeoutError("Gemini timeout"), question],
        ) as ask_question:
            response = self.client.post(
                "/interview/start",
                data={"proposal": "改善校園服務"},
            )
            self.assertEqual(response.status_code, 503)
            self.assertIn("重試".encode("utf-8"), response.data)

            response = self.client.post("/interview/retry", follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("問題 1 / 3".encode("utf-8"), response.data)
        self.assertEqual(ask_question.call_count, 2)

    def test_plan_generation_503_can_retry_without_losing_answers(self):
        response = self.client.post(
            "/interview/start",
            data={"proposal": "改善校園服務"},
            follow_redirects=True,
        )
        self.assertIn("問題 1 / 3".encode("utf-8"), response.data)
        for answer in ("改善使用流程", "公平性"):
            response = self.client.post(
                "/interview/answer",
                data={"answer": answer},
                follow_redirects=True,
            )
        self.assertIn("問題 3 / 3".encode("utf-8"), response.data)

        plan_data = {
            "supported": True,
            "scenario_title": "校園資源改善",
            "recommendations": [{
                "plan_id": "plan_1",
                "title": "循序改善方案",
                "strategy": "分階段調整",
                "description": "先整理需求，再分階段調整服務。",
                "reason": "可逐步驗證改善方向。",
                "effects": {
                    "budget_remaining": -2,
                    "problem_improvement": 2,
                    "satisfaction": 1,
                    "fairness": 1,
                },
            }],
            "rounds": [],
        }
        with patch(
            "app.recommend_plans",
            side_effect=[RuntimeError("Gemini HTTP 503"), plan_data],
        ) as recommend:
            response = self.client.post(
                "/interview/answer",
                data={"answer": "持續收集使用者意見"},
            )
            self.assertEqual(response.status_code, 503)

            response = self.client.post("/interview/retry", follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("方案探索".encode("utf-8"), response.data)
        self.assertIn("循序改善方案".encode("utf-8"), response.data)
        self.assertEqual(recommend.call_count, 2)


class CampusCampaignTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()
        with self.client.session_transaction() as session:
            session.clear()

    def test_ten_year_campaign_runs_forty_turns_and_saves_decade_report(self):
        with patch("app.save_record") as save_record:
            response = self.client.post(
                "/campus/start",
                data={"concern": "圖書館尖峰時段座位不足"},
                follow_redirects=True,
            )
            self.assertEqual(response.status_code, 200)
            self.assertIn("圖書館尖峰時段座位不足".encode("utf-8"), response.data)
            self.assertIn("第 1 年第 1 季".encode("utf-8"), response.data)
            with self.client.session_transaction() as session:
                flow_id = session["flow_id"]

            for _ in range(40):
                response = self.client.post(
                    "/campus/choose",
                    data={"action_id": "listen", "development_id": "audit"},
                    follow_redirects=True,
                )
                self.assertEqual(response.status_code, 200)

        self.assertIn("十年校務總結".encode("utf-8"), response.data)
        self.assertIn("40 個連鎖事件".encode("utf-8"), response.data)
        self.assertIn("第 10 年".encode("utf-8"), response.data)
        self.assertEqual(save_record.call_count, 1)
        campaign = GAMES[flow_id]["campaign"]
        self.assertTrue(campaign["finished"])
        self.assertEqual(len(campaign["history"]), 40)
        self.assertEqual(len(campaign["yearly"]), 10)

    def test_invalid_development_does_not_consume_a_turn(self):
        campaign = new_campaign("校園空間不足", seed=7)
        with self.assertRaisesRegex(ValueError, "可負擔"):
            advance_campaign(campaign, "listen", "not-a-development")
        self.assertEqual(campaign["turn"], 0)
        self.assertEqual(len(campaign["history"]), 0)

    def test_decision_cannot_spend_more_than_available_funds(self):
        campaign = new_campaign("校園空間不足", seed=7)
        campaign["treasury"] = 0
        with self.assertRaisesRegex(ValueError, "校務基金不足"):
            advance_campaign(campaign, "act", "austerity")
        self.assertEqual(campaign["turn"], 0)

    def test_development_choice_branches_the_next_campus_issue(self):
        next_events = set()
        for development in ("library", "scholarships", "conservation", "audit"):
            campaign = new_campaign("校園空間不足", seed=14)
            outcome = advance_campaign(campaign, "listen", development)
            next_events.add(outcome["next_event"])
        self.assertGreater(len(next_events), 1)


if __name__ == "__main__":
    unittest.main()
