import json
import os
import requests
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

os.environ.setdefault("FLASK_SECRET_KEY", "test-only-secret")
os.environ["DEMO_MODE"] = "1"

from ai_service import (
    CAMPAIGN_EVENT_BATCH_SIZE,
    METRIC_RANGES,
    PLAN_RESPONSE_SCHEMA,
    _validate_effects,
    generate_campaign_events,
    recommend_campaign_plans,
    recommend_plans,
    send_request,
)
from app import GAMES, app
from campus_simulation import (
    TOTAL_TURNS,
    YEARS,
    advance_campaign,
    new_campaign,
    resident_profiles,
)
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


class CampaignAiGenerationTests(unittest.TestCase):
    def _event_payload(self, count=CAMPAIGN_EVENT_BATCH_SIZE):
        events = []
        for event_index in range(count):
            events.append({
                "event": f"由玩家決策衍生的校園議題 {event_index + 1}",
                "category": "policy",
                "group": "students",
                "resident_id": "lin_muqing",
                "resident_quote": "我希望學校也能理解我的日常和長期目標。",
                "resident_concern": "資源分配與服務可及性",
                "actions": [
                    {
                        "text": f"方案選項 {action_index + 1}",
                        "cost": 10 + action_index,
                        "effects": {
                            "problem_improvement": action_index,
                            "satisfaction": 1,
                            "fairness": 2 - action_index,
                        },
                        "resident_effects": {
                            "trust": action_index,
                            "stress": -action_index,
                        },
                    }
                    for action_index in range(3)
                ],
            })
        return {"events": events}

    def test_event_generation_sends_proposal_state_and_previous_decision_to_gemini(self):
        history = [{"event": "圖書館空間不足", "response": "擴大開放時段"}]
        next_decision = {
            "current_issue": "晚間延長開放後人力吃緊",
            "response": "調整輪班",
            "management_measure": "培訓支援人力",
        }
        state = {
            "year": 2,
            "semester": 1,
            "treasury": 540,
            "resources": {"staffing": 42},
            "characters": resident_profiles(),
        }
        with (
            patch.dict(os.environ, {"DEMO_MODE": "0"}),
            patch("ai_service._request_gemini", return_value=self._event_payload()) as request,
        ):
            events = generate_campaign_events(
                "圖書館座位不足",
                history,
                state,
                next_decision=next_decision,
            )

        self.assertEqual(len(events), CAMPAIGN_EVENT_BATCH_SIZE)
        self.assertEqual(len(events[0]["actions"]), 3)
        self.assertEqual(events[0]["source"], "gemini")
        user_prompt = json.loads(request.call_args.args[1])
        self.assertEqual(user_prompt["proposal"], "圖書館座位不足")
        self.assertEqual(user_prompt["recent_history"], history)
        self.assertEqual(user_prompt["campus_state"], state)
        self.assertEqual(user_prompt["next_decision"], next_decision)
        self.assertEqual(request.call_args.kwargs["temperature"], 0.9)

    def test_invalid_ai_event_effects_are_rejected(self):
        payload = self._event_payload()
        payload["events"][0]["actions"][0]["effects"]["problem_improvement"] = 11
        with (
            patch.dict(os.environ, {"DEMO_MODE": "0"}),
            patch("ai_service._request_gemini", return_value=payload),
        ):
            with self.assertRaisesRegex(ValueError, "problem_improvement=11"):
                generate_campaign_events(
                    "改善校園服務",
                    [],
                    {"characters": resident_profiles()},
                    opening=True,
                )

    def test_event_rejects_unknown_or_mismatched_character(self):
        for field, value in (("resident_id", "not_a_character"), ("group", "faculty")):
            with self.subTest(field=field):
                payload = self._event_payload()
                payload["events"][0][field] = value
                with (
                    patch.dict(os.environ, {"DEMO_MODE": "0"}),
                    patch("ai_service._request_gemini", return_value=payload),
                ):
                    with self.assertRaisesRegex(ValueError, "指定的教職員生不存在"):
                        generate_campaign_events(
                            "改善校園服務",
                            [],
                            {"characters": resident_profiles()},
                            opening=True,
                        )

    def test_invalid_ai_personal_effects_are_rejected(self):
        payload = self._event_payload()
        payload["events"][0]["actions"][0]["resident_effects"]["trust"] = 6
        with (
            patch.dict(os.environ, {"DEMO_MODE": "0"}),
            patch("ai_service._request_gemini", return_value=payload),
        ):
            with self.assertRaisesRegex(ValueError, "trust=6"):
                generate_campaign_events(
                    "改善校園服務",
                    [],
                    {"characters": resident_profiles()},
                    opening=True,
                )

    def test_campaign_plans_use_problem_specific_api_output(self):
        response_data = {
            "supported": True,
            "scenario_title": "圖書館空間改善",
            "recommendations": [
                {
                    "title": "延長開放方案",
                    "strategy": "分時段改善",
                    "description": "先調整尖峰開放時段並觀察座位使用需求。",
                    "reason": "可迅速紓解尖峰壓力並逐步驗證成效。",
                    "effects": {
                        "budget_remaining": -5,
                        "problem_improvement": 8,
                        "satisfaction": 4,
                        "fairness": 3,
                    },
                },
                {
                    "title": "空間增建方案",
                    "strategy": "擴建閱讀空間",
                    "description": "投入建設預算增加長期座位與自習空間。",
                    "reason": "能擴大容量，但短期財政負擔較高。",
                    "effects": {
                        "budget_remaining": -15,
                        "problem_improvement": 15,
                        "satisfaction": 3,
                        "fairness": 1,
                    },
                },
            ],
        }
        game_config = {
            "metric_labels": {
                "budget_remaining": "剩餘預算",
                "problem_improvement": "問題改善",
                "satisfaction": "教職員生滿意度",
                "fairness": "公平性",
            },
            "initial_metrics": {
                "budget_remaining": 75,
                "problem_improvement": 75,
                "satisfaction": 75,
                "fairness": 75,
            },
        }
        with (
            patch.dict(os.environ, {"DEMO_MODE": "0"}),
            patch("ai_service._request_gemini", return_value=response_data) as request,
        ):
            result = recommend_campaign_plans("圖書館尖峰座位不足", game_config)

        self.assertTrue(result["supported"])
        self.assertEqual(len(result["recommendations"]), 2)
        self.assertEqual(result["recommendations"][0]["plan_id"], "plan_1")
        self.assertIn("圖書館尖峰座位不足", json.loads(request.call_args.args[1])["proposal"])
        self.assertEqual(request.call_args.args[2]["required"], [
            "supported", "scenario_title", "recommendations",
        ])


class CampusCampaignTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()
        with self.client.session_transaction() as session:
            session.clear()

    def _new_test_campaign(self, seed=7):
        game_config = {
            "metric_labels": {
                "budget_remaining": "剩餘預算",
                "problem_improvement": "問題改善",
                "satisfaction": "教職員生滿意度",
                "fairness": "公平性",
            },
            "initial_metrics": {
                "budget_remaining": 75,
                "problem_improvement": 75,
                "satisfaction": 75,
                "fairness": 75,
            },
        }
        proposal = "校園空間不足"
        plans = recommend_campaign_plans(proposal, game_config)
        event_deck = generate_campaign_events(
            proposal,
            [],
            {
                "year": 1,
                "semester": 1,
                "characters": resident_profiles(),
            },
            opening=True,
        )
        return new_campaign(
            proposal,
            event_deck,
            plans["recommendations"][0],
            plans["scenario_title"],
            seed=seed,
        )

    def test_homepage_has_one_problem_input(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_data(as_text=True).count("<textarea"), 1)

    def test_five_year_campaign_runs_ten_turns_and_saves_report(self):
        with patch("app.save_record") as save_record:
            response = self.client.post(
                "/campus/start",
                data={"proposal": "圖書館尖峰時段座位不足"},
                follow_redirects=True,
            )
            self.assertEqual(response.status_code, 200)
            self.assertIn("圖書館尖峰時段座位不足".encode("utf-8"), response.data)
            self.assertIn("示範方案".encode("utf-8"), response.data)
            response = self.client.post(
                "/campus/plan",
                data={"plan_id": "plan_1"},
                follow_redirects=True,
            )
            self.assertEqual(response.status_code, 200)
            self.assertIn("第 1 年第 1 學期".encode("utf-8"), response.data)
            self.assertIn('class="event-portrait"'.encode("utf-8"), response.data)
            self.assertIn("個人目標".encode("utf-8"), response.data)
            with self.client.session_transaction() as session:
                flow_id = session["flow_id"]

            for turn in range(TOTAL_TURNS):
                campaign = GAMES[flow_id]["campaign"]
                response = self.client.post(
                    "/campus/choose",
                    data={
                        "action_id": campaign["current_event"]["actions"][0]["action_id"],
                        "development_id": "audit",
                    },
                    follow_redirects=True,
                )
                self.assertEqual(response.status_code, 200)
                if turn == 0:
                    self.assertIn("第 1 年第 2 學期".encode("utf-8"), response.data)
                elif turn == 1:
                    self.assertIn("第 2 年第 1 學期".encode("utf-8"), response.data)

        self.assertIn("5 年校務總結".encode("utf-8"), response.data)
        self.assertIn("10 個連鎖事件".encode("utf-8"), response.data)
        self.assertIn("第 5 年".encode("utf-8"), response.data)
        self.assertEqual(save_record.call_count, 1)
        campaign = GAMES[flow_id]["campaign"]
        self.assertTrue(campaign["finished"])
        self.assertEqual(len(campaign["history"]), TOTAL_TURNS)
        self.assertEqual(len(campaign["yearly"]), YEARS)

    def test_each_play_gets_five_unique_annual_challenges(self):
        first = self._new_test_campaign()
        second = self._new_test_campaign(seed=8)
        first_challenges = [item["id"] for item in first["challenges"]]
        second_challenges = [item["id"] for item in second["challenges"]]

        self.assertEqual(len(first_challenges), YEARS)
        self.assertEqual(len(set(first_challenges)), YEARS)
        self.assertNotEqual(first_challenges, second_challenges)
        self.assertEqual(first["challenges"][0]["reward"], 30)

    def test_completing_annual_challenge_grants_reward_and_titles(self):
        campaign = self._new_test_campaign()
        campaign["turn"] = 1
        campaign["treasury"] = 1500
        campaign["metrics"]["fairness"] = 95
        campaign["metrics"]["problem_improvement"] = 95
        campaign["resources"] = {"energy": 90, "water": 90, "staffing": 90}
        campaign["buildings"]["library"] = 1
        for resident in campaign["residents"]:
            resident["satisfaction"] = 90
            resident["trust"] = 90
            resident["stress"] = 10
        action = campaign["current_event"]["actions"][0]

        advance_campaign(campaign, action["action_id"], "audit")

        year_one = campaign["yearly"][0]
        self.assertTrue(year_one["challenge_completed"])
        self.assertEqual(year_one["challenge_reward"], 30)
        self.assertGreaterEqual(year_one["treasury"], 1500)
        self.assertIn("equity_champion", {title["id"] for title in campaign["titles"]})

    def test_title_collection_and_five_year_leaderboard_routes(self):
        records = [
            {
                "scenario_id": "campus_decade",
                "years": YEARS,
                "total_score": 91,
                "plan_title": "永續校園方案",
                "created_at": "2026-11-25T10:00:00+00:00",
                "titles": [{"id": "equity_champion", "name": "公平推手", "description": "公平性達到 75。"}],
            },
            {
                "scenario_id": "campus_decade",
                "years": 10,
                "total_score": 99,
                "plan_title": "舊制長期方案",
                "created_at": "2025-01-01T10:00:00+00:00",
            },
        ]
        with patch("app.load_records", return_value=records):
            collection = self.client.get("/titles")
            leaderboard = self.client.get("/leaderboard")

        self.assertEqual(collection.status_code, 200)
        self.assertIn("公平推手".encode("utf-8"), collection.data)
        self.assertIn("神秘稱號".encode("utf-8"), collection.data)
        self.assertEqual(leaderboard.status_code, 200)
        self.assertIn("永續校園方案".encode("utf-8"), leaderboard.data)
        self.assertNotIn("舊制長期方案".encode("utf-8"), leaderboard.data)

    def test_each_character_has_a_unique_portrait_and_personal_profile(self):
        campaign = self._new_test_campaign()
        residents = campaign["residents"]
        portraits = [resident["portrait"] for resident in residents]
        self.assertEqual(len(residents), 8)
        self.assertEqual(len(set(portraits)), len(residents))
        for resident in residents:
            self.assertTrue(resident["personality"])
            self.assertTrue(resident["goal"])
            self.assertTrue(
                (Path(__file__).parent / "static" / resident["portrait"]).is_file()
            )

    def test_choice_changes_only_the_focused_character_relationship(self):
        campaign = self._new_test_campaign()
        event = campaign["current_event"]
        focused = event["resident"]
        action = event["actions"][0]
        other_trust = {
            resident["id"]: resident["trust"]
            for resident in campaign["residents"]
            if resident["id"] != focused["id"]
        }
        expected_trust = max(
            0, min(100, focused["trust"] + action["resident_effects"]["trust"])
        )
        expected_stress = max(
            0, min(100, focused["stress"] + action["resident_effects"]["stress"])
        )

        advance_campaign(campaign, action["action_id"], "audit")

        self.assertEqual(focused["trust"], expected_trust)
        self.assertEqual(focused["stress"], expected_stress)
        self.assertEqual(
            {resident["id"]: resident["trust"] for resident in campaign["residents"] if resident["id"] != focused["id"]},
            other_trust,
        )

    def test_failed_event_batch_keeps_the_decision_retryable(self):
        response = self.client.post(
            "/campus/start",
            data={"proposal": "圖書館尖峰座位不足"},
            follow_redirects=True,
        )
        self.assertIn("示範方案".encode("utf-8"), response.data)
        response = self.client.post(
            "/campus/plan",
            data={"plan_id": "plan_1"},
            follow_redirects=True,
        )
        with self.client.session_transaction() as session:
            flow_id = session["flow_id"]
        campaign = GAMES[flow_id]["campaign"]
        campaign["event_queue"] = []
        action_id = campaign["current_event"]["actions"][0]["action_id"]
        generated_batch = generate_campaign_events(
            campaign["concern"],
            campaign["history"],
            {
                "year": 1,
                "semester": 1,
                "characters": resident_profiles(campaign["residents"]),
            },
        )
        with patch(
            "app.generate_campaign_events",
            side_effect=[RuntimeError("Gemini unavailable"), generated_batch],
        ) as generate_events:
            response = self.client.post(
                "/campus/choose",
                data={"action_id": action_id, "development_id": "audit"},
            )
            self.assertEqual(response.status_code, 503)
            self.assertIn(b"/campus/retry-choice", response.data)
            self.assertEqual(campaign["turn"], 0)

            response = self.client.post("/campus/retry-choice", follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(campaign["turn"], 1)
        self.assertNotIn("pending_decision", GAMES[flow_id])
        self.assertEqual(generate_events.call_count, 2)

    def test_invalid_development_does_not_consume_a_turn(self):
        campaign = self._new_test_campaign()
        action_id = campaign["current_event"]["actions"][0]["action_id"]
        with self.assertRaisesRegex(ValueError, "可負擔"):
            advance_campaign(campaign, action_id, "not-a-development")
        self.assertEqual(campaign["turn"], 0)
        self.assertEqual(len(campaign["history"]), 0)

    def test_decision_cannot_spend_more_than_available_funds(self):
        campaign = self._new_test_campaign()
        campaign["treasury"] = 0
        action = campaign["current_event"]["actions"][0]
        action["cost"] = 40
        with self.assertRaisesRegex(ValueError, "校務基金不足"):
            advance_campaign(campaign, action["action_id"], "austerity")
        self.assertEqual(campaign["turn"], 0)


if __name__ == "__main__":
    unittest.main()
