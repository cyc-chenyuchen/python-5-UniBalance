import json
import os
import requests
import tempfile
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
    TITLE_CATALOG,
    TOTAL_TURNS,
    YEARS,
    _advance_story_arc,
    _campus_reaction,
    _resolve_event_rule,
    _title_is_earned,
    advance_campaign,
    campus_map_context,
    campus_profile_for_seed,
    make_campaign_record,
    new_campaign,
    next_story_arc_context,
    resident_profiles,
    story_arc_for_seed,
)
from simulation import apply_effects, calculate_total_score, make_comment, run_round_choice
from storage import load_records, save_record


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
    def test_timeout_is_bounded_and_retried_twice_before_failure(self):
        with patch(
            "ai_service.requests.post",
            side_effect=requests.exceptions.ReadTimeout,
        ) as post, patch("ai_service.time.sleep") as sleep:
            with self.assertRaisesRegex(TimeoutError, "已自動重試兩次仍失敗"):
                send_request("https://example.test/generate", {}, {})

        self.assertEqual(post.call_count, 3)
        self.assertEqual(
            [call.args[0] for call in sleep.call_args_list],
            [5, 12],
        )
        post.assert_called_with(
            "https://example.test/generate",
            headers={},
            json={},
            timeout=(5, 30),
        )

    def test_service_unavailable_retries_three_times_then_succeeds(self):
        unavailable = Mock(status_code=503)
        still_unavailable = Mock(status_code=503)
        third_unavailable = Mock(status_code=503)
        success = Mock(status_code=200)
        with (
            patch(
                "ai_service.requests.post",
                side_effect=[
                    unavailable,
                    still_unavailable,
                    third_unavailable,
                    success,
                ],
            ) as post,
            patch("ai_service.time.sleep") as sleep,
        ):
            response = send_request("https://example.test/generate", {}, {})

        self.assertIs(response, success)
        self.assertEqual(post.call_count, 4)
        self.assertEqual(
            [call.args[0] for call in sleep.call_args_list],
            [5, 12, 20],
        )

    def test_repeated_service_unavailable_reports_retry_failure(self):
        unavailable = Mock(status_code=503)
        with (
            patch(
                "ai_service.requests.post",
                side_effect=[unavailable, unavailable, unavailable, unavailable],
            ) as post,
            patch("ai_service.time.sleep") as sleep,
        ):
            with self.assertRaisesRegex(RuntimeError, "已自動重試三次仍失敗"):
                send_request("https://example.test/generate", {}, {})

        self.assertEqual(post.call_count, 4)
        self.assertEqual(
            [call.args[0] for call in sleep.call_args_list],
            [5, 12, 20],
        )

    def test_rate_limit_respects_retry_after_header(self):
        limited = Mock(status_code=429, headers={"Retry-After": "9"})
        success = Mock(status_code=200)
        with (
            patch(
                "ai_service.requests.post",
                side_effect=[limited, success],
            ),
            patch("ai_service.time.sleep") as sleep,
        ):
            response = send_request("https://example.test/generate", {}, {})

        self.assertIs(response, success)
        sleep.assert_called_once_with(9)

    def test_service_unavailable_respects_http_date_retry_after(self):
        unavailable = Mock(
            status_code=503,
            headers={"Retry-After": "Wed, 21 Oct 2099 07:28:00 GMT"},
        )
        success = Mock(status_code=200)
        with (
            patch(
                "ai_service.requests.post",
                side_effect=[unavailable, success],
            ),
            patch("ai_service.time.sleep") as sleep,
        ):
            response = send_request("https://example.test/generate", {}, {})

        self.assertIs(response, success)
        sleep.assert_called_once_with(60)


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


class StorageRetentionTests(unittest.TestCase):
    def test_saving_records_keeps_only_the_most_recent_twenty(self):
        with tempfile.TemporaryDirectory() as directory:
            records_file = Path(directory) / "records.json"
            records_file.write_text(
                json.dumps([{"record_id": str(index)} for index in range(25)]),
                encoding="utf-8",
            )
            with patch("storage.RECORDS_FILE", records_file):
                self.assertEqual(
                    [item["record_id"] for item in load_records()],
                    [str(index) for index in range(5, 25)],
                )
                save_record({"record_id": "record-25"})
                records = load_records()
                saved_records = json.loads(
                    records_file.read_text(encoding="utf-8")
                )

        self.assertEqual(len(records), 20)
        self.assertEqual(records[0]["record_id"], "6")
        self.assertEqual(records[-1]["record_id"], "record-25")
        self.assertEqual(len(saved_records), 20)


class CampaignAiGenerationTests(unittest.TestCase):
    def _event_payload(self, count=CAMPAIGN_EVENT_BATCH_SIZE):
        events = []
        for event_index in range(count):
            events.append({
                "event": f"由玩家決策衍生的校園議題 {event_index + 1}",
                "category": "policy",
                "event_type": "negotiation",
                "story_stage": 0,
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
                        "follow_up": "後續學期持續觀察執行成效。",
                        "delayed_effects": {
                            "problem_improvement": 2,
                            "fairness": 1,
                            "treasury": -5,
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
        self.assertEqual(
            user_prompt["continuity_contract"]["primary_issue"],
            "圖書館座位不足",
        )
        self.assertFalse(
            user_prompt["continuity_contract"]["unrelated_campus_events_allowed"]
        )
        self.assertTrue(
            user_prompt["continuity_contract"]["include_unexpected_event"]
        )
        self.assertIn(
            "起因出乎意料",
            user_prompt["continuity_contract"]["unexpected_event_requirements"][0],
        )
        self.assertIn("proposal 是整局經營的核心問題", request.call_args.args[0])
        self.assertIn("至少安排一個真正未預期的突發事件", request.call_args.args[0])
        self.assertEqual(request.call_args.kwargs["temperature"], 0.9)

    def test_demo_event_batch_uses_distinct_play_formats(self):
        events = generate_campaign_events(
            "圖書館座位不足",
            [],
            {"characters": resident_profiles()},
        )

        self.assertEqual(len(events), CAMPAIGN_EVENT_BATCH_SIZE)
        self.assertEqual(
            len({event["event_type"] for event in events}),
            CAMPAIGN_EVENT_BATCH_SIZE,
        )
        for event in events:
            self.assertEqual(
                event["event_type"] == "character_story",
                event["story_stage"] > 0,
            )
            if event["event_type"] == "crisis":
                self.assertTrue(any(
                    action["effects"]["problem_improvement"] >= 5
                    for action in event["actions"]
                ))
            if event["event_type"] == "opportunity":
                self.assertTrue(any(
                    action["delayed_effects"]["problem_improvement"] >= 4
                    and action["delayed_effects"]["fairness"] >= 0
                    for action in event["actions"]
                ))

    def test_demo_event_batch_advances_the_resident_story_arc(self):
        story_arc = story_arc_for_seed(18)
        events = generate_campaign_events(
            "校園空間不足",
            [],
            {
                "characters": resident_profiles(),
                "story_arc": story_arc,
            },
        )

        self.assertEqual(events[0]["story_stage"], 1)
        self.assertEqual(events[0]["resident_id"], story_arc["resident_id"])
        self.assertEqual(events[0]["event_type"], "character_story")
        self.assertEqual(
            [event["story_stage"] for event in events],
            [1, 2],
        )
        self.assertEqual(events[1]["resident_id"], story_arc["resident_id"])

    def test_api_story_batch_must_follow_the_requested_arc_stage(self):
        payload = self._event_payload()
        payload["events"][0]["event_type"] = "character_story"
        payload["events"][0]["story_stage"] = 2
        payload["events"][1]["event_type"] = "character_story"
        payload["events"][1]["story_stage"] = 3
        story_arc = {"next_stage": 2, "resident_id": "lin_muqing"}
        state = {
            "characters": resident_profiles(),
            "story_arc": story_arc,
        }

        with (
            patch.dict(os.environ, {"DEMO_MODE": "0"}),
            patch("ai_service._request_gemini", return_value=payload),
        ):
            events = generate_campaign_events("改善校園服務", [], state)

        self.assertEqual(
            [event["story_stage"] for event in events],
            [2, 3],
        )

        payload["events"][0]["story_stage"] = 1
        with (
            patch.dict(os.environ, {"DEMO_MODE": "0"}),
            patch("ai_service._request_gemini", return_value=payload),
        ):
            with self.assertRaisesRegex(ValueError, "人物故事線順序不符"):
                generate_campaign_events("改善校園服務", [], state)

    def test_api_retries_once_when_story_stage_order_is_wrong(self):
        invalid_payload = self._event_payload()
        valid_payload = self._event_payload()
        for event, stage in zip(valid_payload["events"], (2, 3)):
            event["event_type"] = "character_story"
            event["story_stage"] = stage
        state = {
            "characters": resident_profiles(),
            "story_arc": {"next_stage": 2, "resident_id": "lin_muqing"},
        }

        with (
            patch.dict(os.environ, {"DEMO_MODE": "0"}),
            patch(
                "ai_service._request_gemini",
                side_effect=[invalid_payload, valid_payload],
            ) as request,
        ):
            events = generate_campaign_events("改善校園服務", [], state)

        self.assertEqual([event["story_stage"] for event in events], [2, 3])
        self.assertEqual(request.call_count, 2)
        retry_prompt = json.loads(request.call_args_list[1].args[1])
        self.assertEqual(retry_prompt["required_story_stages"], [2, 3])
        self.assertIn("格式錯誤", retry_prompt["format_correction"])

    def test_api_retries_once_when_event_rules_have_no_playable_success(self):
        invalid_payload = self._event_payload()
        invalid_payload["events"][0]["event_type"] = "opportunity"
        valid_payload = self._event_payload()
        valid_payload["events"][0]["event_type"] = "opportunity"
        valid_payload["events"][0]["actions"][0]["delayed_effects"] = {
            "problem_improvement": 4,
            "fairness": 0,
            "treasury": 0,
        }

        with (
            patch.dict(os.environ, {"DEMO_MODE": "0"}),
            patch(
                "ai_service._request_gemini",
                side_effect=[invalid_payload, valid_payload],
            ) as request,
        ):
            events = generate_campaign_events(
                "改善校園服務", [], {"characters": resident_profiles()}
            )

        self.assertEqual(events[0]["event_type"], "opportunity")
        self.assertEqual(request.call_count, 2)
        retry_prompt = json.loads(request.call_args_list[1].args[1])
        self.assertIn("格式錯誤", retry_prompt["format_correction"])

    def test_api_rejects_event_rules_without_a_success_option(self):
        invalid_cases = (
            ("crisis", "止損選項"),
            ("opportunity", "基金紅利條件"),
        )
        for event_type, message in invalid_cases:
            with self.subTest(event_type=event_type):
                payload = self._event_payload()
                payload["events"][0]["event_type"] = event_type
                with (
                    patch.dict(os.environ, {"DEMO_MODE": "0"}),
                    patch("ai_service._request_gemini", return_value=payload),
                ):
                    with self.assertRaisesRegex(ValueError, message):
                        generate_campaign_events(
                            "改善校園服務",
                            [],
                            {"characters": resident_profiles()},
                            opening=True,
                        )

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

    def test_character_story_event_requires_an_active_story_stage(self):
        payload = self._event_payload()
        payload["events"][0]["event_type"] = "character_story"
        with (
            patch.dict(os.environ, {"DEMO_MODE": "0"}),
            patch("ai_service._request_gemini", return_value=payload),
        ):
            with self.assertRaisesRegex(ValueError, "必須安排有效主線幕次"):
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

    def test_invalid_event_type_and_delayed_effects_are_rejected(self):
        invalid_cases = (
            ("event_type", "routine", "事件玩法類型無效"),
            ("delayed_effects", {
                "problem_improvement": 9,
                "fairness": 1,
                "treasury": 0,
            }, "problem_improvement=9"),
        )
        for field, value, message in invalid_cases:
            with self.subTest(field=field):
                payload = self._event_payload()
                if field == "event_type":
                    payload["events"][0][field] = value
                else:
                    payload["events"][0]["actions"][0][field] = value
                with (
                    patch.dict(os.environ, {"DEMO_MODE": "0"}),
                    patch("ai_service._request_gemini", return_value=payload),
                ):
                    with self.assertRaisesRegex(ValueError, message):
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
                "story_arc": story_arc_for_seed(seed),
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

    def test_campus_dashboard_shows_current_average_values(self):
        campaign = self._new_test_campaign()
        campaign["resources"] = {"energy": 61, "water": 72, "staffing": 68}
        campaign["buildings"]["library"] = 2
        for index, resident in enumerate(campaign["residents"]):
            resident["satisfaction"] = 51 + index
            resident["trust"] = 41 + index
            resident["stress"] = 31 + index

        flow_id = "campus-average-dashboard-test"
        GAMES[flow_id] = {"campaign": campaign}
        self.addCleanup(GAMES.pop, flow_id, None)
        with self.client.session_transaction() as session:
            session["flow_id"] = flow_id

        response = self.client.get("/campus")
        page = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        for value in ("67.0", "54.5", "44.5", "34.5"):
            self.assertIn(value, page)
        self.assertIn("平均資源存量", page)
        self.assertIn("平均滿意度／信任度／壓力值", page)
        self.assertIn('class="interactive-campus-map"', page)
        self.assertIn('data-facility-id="library"', page)
        self.assertIn('data-facility-level="2"', page)
        self.assertLess(page.index('class="campus-map-card game-panel"'), page.index('class="event-command game-panel"'))

    def test_campaign_result_shows_final_average_values(self):
        campaign = self._new_test_campaign()
        campaign["resources"] = {"energy": 61, "water": 72, "staffing": 68}
        for index, resident in enumerate(campaign["residents"]):
            resident["satisfaction"] = 51 + index
            resident["trust"] = 41 + index
            resident["stress"] = 31 + index
        record = make_campaign_record(campaign)

        flow_id = "campus-result-average-test"
        GAMES[flow_id] = {"campaign": campaign, "result": record}
        self.addCleanup(GAMES.pop, flow_id, None)
        with self.client.session_transaction() as session:
            session["flow_id"] = flow_id

        response = self.client.get("/campus/result")
        page = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        for value in ("67.0", "54.5", "44.5", "34.5"):
            self.assertIn(value, page)
        for label in ("平均資源存量", "平均滿意度", "平均信任度", "平均壓力值"):
            self.assertIn(label, page)
        self.assertIn('class="interactive-campus-map"', page)

    def test_map_context_keeps_legacy_records_explicit_about_missing_options(self):
        context = campus_map_context({
            "buildings": {},
            "resources": {},
            "policies": {},
            "history": [],
            "residents": [],
        })

        self.assertEqual(context["facilities"]["library"]["level"], 0)
        self.assertIn(
            "本局結果不提供下一步選擇",
            context["facilities"]["library"]["next_step"],
        )

    def test_records_archive_shows_new_details_and_keeps_legacy_records(self):
        campaign = self._new_test_campaign()
        current_record = make_campaign_record(campaign)
        current_record["titles"] = [{
            "name": "共融校園",
            "description": "公平性達到目標。",
            "earned_turn": 4,
        }]
        legacy_record = {
            "scenario_title": "舊版校園任務",
            "plan_title": "舊版方案",
            "total_score": 72,
        }

        with patch("app.load_records", return_value=[current_record, legacy_record]):
            response = self.client.get("/records")

        self.assertEqual(response.status_code, 200)
        self.assertIn("舊版校園任務".encode("utf-8"), response.data)
        self.assertIn("五年校務任期".encode("utf-8"), response.data)
        self.assertIn("教職員生滿意度".encode("utf-8"), response.data)
        self.assertIn("共融校園".encode("utf-8"), response.data)

    def test_title_catalog_has_twenty_titles_with_reachable_conditions(self):
        self.assertEqual(len(TITLE_CATALOG), 20)
        campaign = self._new_test_campaign()
        added_titles = TITLE_CATALOG[10:]
        self.assertTrue(
            all(not _title_is_earned(campaign, title["rule"]) for title in added_titles)
        )

        campaign["resources"] = {"energy": 90, "water": 90, "staffing": 90}
        campaign["metrics"]["satisfaction"] = 95
        campaign["buildings"] = {"library": 1, "housing": 1, "wellbeing": 1}
        campaign["policies"] = {
            "scholarships": 1,
            "workload": 1,
            "accessibility": 1,
        }
        for resident in campaign["residents"]:
            resident["trust"] = 80
            resident["stress"] = 20
        for challenge in campaign["challenges"]:
            challenge["completed"] = True
        campaign["story_arc"]["stage"] = 3
        campaign["story_arc"]["support_score"] = 20

        self.assertTrue(
            all(_title_is_earned(campaign, title["rule"]) for title in added_titles)
        )

    def test_campaign_result_lists_completed_annual_challenges(self):
        campaign = self._new_test_campaign()
        campaign["challenges"][0]["completed"] = True
        campaign["challenges"][1]["completed"] = False
        record = make_campaign_record(campaign)

        flow_id = "campus-result-challenge-test"
        GAMES[flow_id] = {"campaign": campaign, "result": record}
        self.addCleanup(GAMES.pop, flow_id, None)
        with self.client.session_transaction() as session:
            session["flow_id"] = flow_id

        response = self.client.get("/campus/result")
        page = response.get_data(as_text=True)
        completed = campaign["challenges"][0]
        uncompleted = campaign["challenges"][1]

        self.assertEqual(response.status_code, 200)
        self.assertIn("年度挑戰".encode("utf-8"), response.data)
        self.assertIn(f"1 / {YEARS} 完成".encode("utf-8"), response.data)
        self.assertIn(completed["title"].encode("utf-8"), response.data)
        self.assertIn(uncompleted["title"].encode("utf-8"), response.data)
        self.assertIn("未完成".encode("utf-8"), response.data)
        self.assertIn(
            f"基金 +{completed['reward']}".encode("utf-8"),
            response.data,
        )

    def test_campaign_result_keeps_long_timeline_details_collapsed(self):
        campaign = self._new_test_campaign()
        event = "圖書館尖峰時段座位不足，學生經常找不到合適的自習空間"
        response_text = "延長開放時間並增設夜間服務，定期收集學生使用意見"
        consequence = {
            "origin_event": "上學期圖書館空間調整",
            "description": "夜間使用人數增加，後續需持續留意清潔與人力安排",
        }
        campaign["history"] = [{
            "year": 1,
            "semester": 2,
            "event": event,
            "resident": "蕭述一",
            "role": "大學生",
            "response": response_text,
            "development": "延長圖書館開放時間並增設夜間服務",
            "category": "校園服務",
            "butterfly": "增加夜間使用機會，也提高了晚間清潔與服務人力需求。",
            "settled_consequences": [consequence],
        }]
        record = make_campaign_record(campaign)

        flow_id = "campus-result-compact-chronicle-test"
        GAMES[flow_id] = {"campaign": campaign, "result": record}
        self.addCleanup(GAMES.pop, flow_id, None)
        with self.client.session_transaction() as session:
            session["flow_id"] = flow_id

        response = self.client.get("/campus/result")
        page = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('class="chronicle-turn">Y1 · S2</span>', page)
        self.assertIn('<details class="chronicle-more">', page)
        self.assertIn("<summary>影響與後續 1 項</summary>", page)
        self.assertIn(f'title="{event}"', page)
        self.assertIn(
            f'<strong>{consequence["origin_event"]}</strong> · {consequence["description"]}',
            page,
        )

    def test_homepage_has_one_problem_input(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        page = response.get_data(as_text=True)
        self.assertEqual(page.count("<textarea"), 1)
        self.assertIn('href="/characters"'.encode("utf-8"), response.data)

    def test_character_directory_uses_all_existing_residents(self):
        response = self.client.get("/characters")
        page = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("校園人物誌".encode("utf-8"), response.data)
        self.assertIn('class="character-directory"'.encode("utf-8"), response.data)
        for resident in resident_profiles():
            self.assertIn(resident["name"], page)
            self.assertIn(resident["concern"], page)
            self.assertIn(resident["goal"], page)

    def test_five_year_campaign_runs_ten_turns_and_saves_report(self):
        with patch("app.save_record") as save_record:
            response = self.client.post(
                "/campus/start",
                data={"proposal": "圖書館尖峰時段座位不足"},
                follow_redirects=True,
            )
            self.assertEqual(response.status_code, 200)
            self.assertIn("圖書館尖峰時段座位不足".encode("utf-8"), response.data)
            self.assertIn("離線示範策略".encode("utf-8"), response.data)
            self.assertIn("人物主線".encode("utf-8"), response.data)
            response = self.client.post(
                "/campus/plan",
                data={"plan_id": "plan_1"},
                follow_redirects=True,
            )
            self.assertEqual(response.status_code, 200)
            self.assertIn("第 1 年".encode("utf-8"), response.data)
            self.assertIn("第 1 學期".encode("utf-8"), response.data)
            self.assertIn('class="event-portrait"'.encode("utf-8"), response.data)
            self.assertIn("目標：".encode("utf-8"), response.data)
            self.assertIn("本類特殊規則".encode("utf-8"), response.data)
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
                    self.assertIn('data-campaign-turn="2"'.encode("utf-8"), response.data)
                    self.assertIn("你的決策已影響校園".encode("utf-8"), response.data)
                elif turn == 1:
                    self.assertIn('data-campaign-turn="3"'.encode("utf-8"), response.data)

        self.assertIn("五年後的校園".encode("utf-8"), response.data)
        self.assertIn("十學期決策年表".encode("utf-8"), response.data)
        self.assertIn("第 5 年".encode("utf-8"), response.data)
        self.assertEqual(save_record.call_count, 1)
        campaign = GAMES[flow_id]["campaign"]
        self.assertTrue(campaign["finished"])
        self.assertEqual(len(campaign["history"]), TOTAL_TURNS)
        self.assertTrue(all(
            item["event_rule_result"] and item["campus_reaction"]
            for item in campaign["history"]
        ))
        self.assertEqual(len(campaign["yearly"]), YEARS)
        self.assertEqual(campaign["story_arc"]["stage"], 3)
        self.assertIsNotNone(campaign["story_arc"]["ending"])
        self.assertEqual(
            [
                turn
                for turn, item in enumerate(campaign["history"])
                if item["story_beat"]
            ],
            [1, 2, 3],
        )

    def test_each_play_gets_five_unique_annual_challenges(self):
        first = self._new_test_campaign()
        second = self._new_test_campaign(seed=8)
        first_challenges = [item["id"] for item in first["challenges"]]
        second_challenges = [item["id"] for item in second["challenges"]]

        self.assertEqual(len(first_challenges), YEARS)
        self.assertEqual(len(set(first_challenges)), YEARS)
        self.assertNotEqual(first_challenges, second_challenges)
        self.assertEqual(first["challenges"][0]["reward"], 30)

    def test_seed_reuses_the_same_random_campus_profile(self):
        profile = campus_profile_for_seed(42)
        campaign = self._new_test_campaign(seed=42)

        self.assertEqual(campus_profile_for_seed(42), profile)
        self.assertEqual(campaign["campus_profile"]["id"], profile["id"])
        self.assertEqual(campaign["initial_metrics"], campaign["metrics"])
        self.assertEqual(
            campaign["population"]["students"],
            9000 + profile["population_delta"]["students"],
        )
        self.assertEqual(
            {
                campus_profile_for_seed(seed)["id"]
                for seed in range(12)
            },
            {
                "metro_commuter",
                "research_hub",
                "regional_community",
                "innovation_campus",
            },
        )

    def test_story_arc_branches_on_player_support(self):
        cooperative = self._new_test_campaign(seed=18)
        stalled = self._new_test_campaign(seed=18)

        for campaign, signal in ((cooperative, 15), (stalled, -15)):
            resident = next(
                item for item in campaign["residents"]
                if item["id"] == campaign["story_arc"]["resident_id"]
            )
            for stage in range(1, 4):
                _advance_story_arc(
                    campaign,
                    {"story_stage": stage, "resident": resident},
                    {
                        "effects": {"fairness": signal // 3},
                        "resident_effects": {
                            "trust": signal // 3,
                            "stress": -signal // 3,
                        },
                    },
                )

        self.assertEqual(cooperative["story_arc"]["ending"], "co_created")
        self.assertIn("沒有停在群組", cooperative["story_arc"]["ending_text"])
        self.assertEqual(stalled["story_arc"]["ending"], "stalled")
        self.assertIn("待跨單位會議確認", stalled["story_arc"]["ending_text"])

    def test_delayed_choice_effects_settle_one_semester_later(self):
        campaign = self._new_test_campaign(seed=12)
        control = self._new_test_campaign(seed=12)
        for state in (campaign, control):
            state["metrics"]["problem_improvement"] = 50
            state["metrics"]["fairness"] = 50
            state["treasury"] = 1000
            state["pending_consequences"] = []

        action = campaign["current_event"]["actions"][0]
        control_action = control["current_event"]["actions"][0]
        for selected in (action, control_action):
            selected["effects"] = {
                "problem_improvement": 0,
                "satisfaction": 0,
                "fairness": 0,
            }
            selected["group_effect"] = 0
            selected["resident_effects"] = {"trust": 0, "stress": 0}
            selected["cost"] = 0
        action["follow_up"] = "兩學期後完成服務擴充。"
        action["delayed_effects"] = {
            "problem_improvement": 7,
            "fairness": 4,
            "treasury": 40,
        }
        control_action["follow_up"] = action["follow_up"]
        control_action["delayed_effects"] = {
            "problem_improvement": 0,
            "fairness": 0,
            "treasury": 0,
        }

        advance_campaign(campaign, action["action_id"], "audit")
        advance_campaign(control, control_action["action_id"], "audit")
        self.assertEqual(len(campaign["pending_consequences"]), 1)
        self.assertEqual(campaign["turn"], 1)

        next_events = generate_campaign_events(
            campaign["concern"],
            campaign["history"],
            {
                "characters": resident_profiles(campaign["residents"]),
                "story_arc": next_story_arc_context(campaign),
            },
        )
        advance_campaign(
            campaign,
            campaign["current_event"]["actions"][0]["action_id"],
            "audit",
            next_events,
        )
        outcome = advance_campaign(
            control,
            control["current_event"]["actions"][0]["action_id"],
            "audit",
            next_events,
        )

        self.assertEqual(
            campaign["metrics"]["problem_improvement"]
            - control["metrics"]["problem_improvement"],
            7,
        )
        self.assertEqual(
            campaign["metrics"]["fairness"] - control["metrics"]["fairness"], 4
        )
        self.assertEqual(
            campaign["treasury"] - control["treasury"],
            40 + campaign["yearly"][0]["challenge_reward"],
        )
        self.assertEqual(len(campaign["history"][-1]["settled_consequences"]), 1)
        self.assertEqual(
            outcome["settled_consequences"][0]["effects"],
            {"problem_improvement": 0, "fairness": 0, "treasury": 0},
        )

    def test_final_turn_settles_pending_consequences(self):
        campaign = self._new_test_campaign()
        campaign["turn"] = TOTAL_TURNS - 1
        action = campaign["current_event"]["actions"][0]
        action["delayed_effects"] = {
            "problem_improvement": 1,
            "fairness": 1,
            "treasury": 1,
        }

        outcome = advance_campaign(campaign, action["action_id"], "audit")

        self.assertTrue(campaign["finished"])
        self.assertEqual(campaign["pending_consequences"], [])
        self.assertEqual(len(outcome["settled_consequences"]), 1)

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

    def test_event_rules_apply_success_and_failure_effects(self):
        crisis = self._new_test_campaign()
        event = crisis["current_event"]
        event["event_type"] = "crisis"
        action = event["actions"][0]
        action["effects"]["problem_improvement"] = 5
        improvement_before = crisis["metrics"]["problem_improvement"]
        stress_before = event["resident"]["stress"]
        self.assertIn("成功", _resolve_event_rule(crisis, event, action))
        self.assertEqual(crisis["metrics"]["problem_improvement"], improvement_before)
        self.assertEqual(event["resident"]["stress"], stress_before)

        action["effects"]["problem_improvement"] = 4
        self.assertIn("未達門檻", _resolve_event_rule(crisis, event, action))
        self.assertEqual(crisis["metrics"]["problem_improvement"], improvement_before - 2)
        self.assertEqual(event["resident"]["stress"], stress_before + 2)

        opportunity = self._new_test_campaign()
        event = opportunity["current_event"]
        event["event_type"] = "opportunity"
        action = event["actions"][0]
        action["delayed_effects"]["problem_improvement"] = 4
        action["delayed_effects"]["fairness"] = 0
        treasury_before = opportunity["treasury"]
        _resolve_event_rule(opportunity, event, action)
        self.assertEqual(opportunity["treasury"], treasury_before + 20)
        action["delayed_effects"]["fairness"] = -1
        _resolve_event_rule(opportunity, event, action)
        self.assertEqual(opportunity["treasury"], treasury_before + 20)

        negotiation = self._new_test_campaign()
        event = negotiation["current_event"]
        event["event_type"] = "negotiation"
        action = event["actions"][0]
        action["effects"]["fairness"] = 3
        trust_before = event["resident"]["trust"]
        _resolve_event_rule(negotiation, event, action)
        self.assertEqual(event["resident"]["trust"], trust_before + 2)
        action["effects"]["fairness"] = -1
        _resolve_event_rule(negotiation, event, action)
        self.assertEqual(event["resident"]["trust"], trust_before)

        vote = self._new_test_campaign()
        event = vote["current_event"]
        event["event_type"] = "campus_vote"
        action = event["actions"][0]
        action["effects"]["fairness"] = 2
        satisfaction_before = event["resident"]["satisfaction"]
        _resolve_event_rule(vote, event, action)
        self.assertEqual(event["resident"]["satisfaction"], satisfaction_before + 2)
        action["effects"]["fairness"] = 1
        _resolve_event_rule(vote, event, action)
        self.assertEqual(event["resident"]["satisfaction"], satisfaction_before)

    def test_campus_reaction_is_reproducible_for_the_same_seed_and_turn(self):
        campaign = self._new_test_campaign(seed=42)
        event = campaign["current_event"]
        development = {"category": "政策"}

        first = _campus_reaction(campaign, event, development)
        second = _campus_reaction(campaign, event, development)

        self.assertEqual(first, second)

    def test_failed_event_batch_keeps_the_decision_retryable(self):
        response = self.client.post(
            "/campus/start",
            data={"proposal": "圖書館尖峰座位不足"},
            follow_redirects=True,
        )
        self.assertIn("離線示範策略".encode("utf-8"), response.data)
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
                "story_arc": next_story_arc_context(campaign),
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
