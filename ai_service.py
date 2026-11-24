import json
import os

import requests


METRIC_RANGES = {
    "plan": {
        "budget_remaining": (-20, 0),
        "problem_improvement": (0, 20),
        "satisfaction": (-10, 10),
        "fairness": (-10, 10),
    },
    "action": {
        "budget_remaining": (-10, 0),
        "problem_improvement": (-5, 10),
        "satisfaction": (-5, 5),
        "fairness": (-5, 5),
    },
}

INTERVIEW_QUESTION_COUNT = 3
SIMULATION_ROUND_COUNT = 3

INTERVIEW_RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "question": {"type": "STRING"},
        "options": {
            "type": "ARRAY",
            "items": {"type": "STRING"},
        },
    },
    "required": ["question", "options"],
}

def _effects_schema(ranges):
    return {
        "type": "OBJECT",
        "properties": {
            name: {
                "type": "INTEGER",
                "description": (
                    f"遊戲效果整數，必須介於 {minimum} 到 {maximum}，包含邊界。"
                ),
            }
            for name, (minimum, maximum) in ranges.items()
        },
        "required": list(ranges),
    }


_PLAN_EFFECTS_SCHEMA = _effects_schema(METRIC_RANGES["plan"])
_ACTION_EFFECTS_SCHEMA = _effects_schema(METRIC_RANGES["action"])

PLAN_RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "supported": {"type": "BOOLEAN"},
        "scenario_title": {"type": "STRING"},
        "recommendations": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "title": {"type": "STRING"},
                    "strategy": {"type": "STRING"},
                    "description": {"type": "STRING"},
                    "reason": {"type": "STRING"},
                    "effects": _PLAN_EFFECTS_SCHEMA,
                },
                "required": ["title", "strategy", "description", "reason", "effects"],
            },
        },
        "rounds": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "event": {"type": "STRING"},
                    "actions": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "text": {"type": "STRING"},
                                "effects": _ACTION_EFFECTS_SCHEMA,
                            },
                            "required": ["text", "effects"],
                        },
                    },
                },
                "required": ["event", "actions"],
            },
        },
    },
    "required": ["supported", "scenario_title", "recommendations", "rounds"],
}

REVIEW_RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "focus_metric": {"type": "STRING"},
        "action_index": {"type": "INTEGER"},
    },
    "required": ["focus_metric", "action_index"],
}


def send_request(url, headers, request_data):
    try:
        response = requests.post(
            url,
            headers=headers,
            json=request_data,
            timeout=(3, 12),
        )
        response.raise_for_status()
        return response
    except requests.exceptions.Timeout as error:
        raise TimeoutError(
            "Gemini 請求逾時（連線上限 3 秒、回應上限 12 秒），請重試。"
        ) from error
    except requests.exceptions.RequestException as error:
        error_response = getattr(error, "response", None)
        status_code = getattr(error_response, "status_code", None)
        if status_code is not None:
            raise RuntimeError(
                f"Gemini 服務回應錯誤（HTTP {status_code}），請重試。"
            ) from error
        raise RuntimeError("Gemini 連線失敗，請重試。") from error


def _request_gemini(system_prompt, user_prompt, response_schema):
    api_key = os.environ.get("GEMINI_API_KEY")
    model = os.environ.get("GEMINI_MODEL")
    if not api_key:
        raise RuntimeError("未設定 GEMINI_API_KEY。")
    if not model:
        raise RuntimeError("未設定 GEMINI_MODEL。")

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )
    headers = {"Content-Type": "application/json"}
    request_data = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"parts": [{"text": user_prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": response_schema,
        },
    }
    response = send_request(url, headers, request_data)
    try:
        payload = response.json()
        text = payload["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError, ValueError) as error:
        raise ValueError("Gemini 回覆格式錯誤：找不到 JSON 文字內容。") from error
    return _read_json_reply(text)


def _read_json_reply(text):
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Gemini 回覆格式錯誤：回覆不是有效 JSON。")
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError as error:
        raise ValueError("Gemini 回覆格式錯誤：回覆不是有效 JSON。") from error
    if not isinstance(value, dict):
        raise ValueError("Gemini 回覆格式錯誤：根節點必須為物件。")
    return value


def _validate_text(value, limit, message):
    if not isinstance(value, str):
        raise ValueError(message)
    value = value.strip()
    if not value or len(value) > limit:
        raise ValueError(message)
    return value


def _validate_effects(effects, ranges, message):
    if not isinstance(effects, dict) or set(effects) != set(ranges):
        expected = "、".join(ranges)
        raise ValueError(f"{message}效果欄位必須恰好包含：{expected}。")
    for name, (minimum, maximum) in ranges.items():
        value = effects[name]
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{message}{name} 必須是整數（不可為布林值）。")
        if value < minimum or value > maximum:
            raise ValueError(
                f"{message}{name}={value} 超出允許範圍 {minimum}～{maximum}。"
            )
    return dict(effects)


def ask_interview_question(proposal, answers):
    if os.environ.get("DEMO_MODE") == "1":
        if not answers:
            return {
                "question": "你最希望先改善校園的哪個部分？",
                "options": ["改善使用流程", "增加可用資源"],
            }
        if len(answers) == 1:
            return {
                "question": "你希望改革時優先考慮哪項需求？",
                "options": ["公平性", "便利性", "預算控制"],
            }
        return {
            "question": "你認為要如何確認這項改善真的有效？",
            "options": ["持續收集使用者意見", "觀察服務使用狀況", "訂定定期檢視指標"],
        }

    system_prompt = (
        "你是校園改革訪談助理。只針對校園生活、成員、設施、服務或制度問題提問。"
        f"訪談共 {INTERVIEW_QUESTION_COUNT} 題，每次只產生一道題目，選項 2 到 4 個。"
        "依據提案與先前回答逐步深入，不重複詢問已涵蓋的內容。"
        "回覆必須是單一 JSON 物件，格式為 "
        '{"question":"問題文字","options":["選項一","選項二"]}。'
        "不可回傳 JSON 陣列、Markdown 或額外說明。"
    )
    user_prompt = json.dumps(
        {
            "proposal": proposal,
            "previous_answers": answers,
            "question_number": len(answers) + 1,
            "question_count": INTERVIEW_QUESTION_COUNT,
        },
        ensure_ascii=False,
    )
    data = _request_gemini(
        system_prompt, user_prompt, INTERVIEW_RESPONSE_SCHEMA
    )
    question = _validate_text(data.get("question"), 100, "訪談問題格式錯誤。")
    options = data.get("options")
    if not isinstance(options, list) or not 2 <= len(options) <= 4:
        raise ValueError("訪談選項格式錯誤：必須為 2 到 4 個選項。")
    validated = []
    for option in options:
        validated.append(_validate_text(option, 100, "訪談選項格式錯誤。"))
    if len(set(item.lower() for item in validated)) != len(validated):
        raise ValueError("訪談選項格式錯誤：選項不能重複。")
    return {"question": question, "options": validated}


def recommend_plans(proposal, answers, game_config):
    if os.environ.get("DEMO_MODE") == "1":
        return _demo_recommendation()

    system_prompt = (
        "你是校園改革模擬設計助理。只有明確非校園問題才回 supported=false。"
        f"必須產生恰好兩個方案與恰好 {SIMULATION_ROUND_COUNT} 個回合，每回合恰好兩個行動。"
        "所有效果為遊戲假設，且必須遵守輸入中的 effect_ranges："
        "方案效果與行動效果使用不同範圍；所有效果必須是整數，不可超界。"
        "回覆必須是單一 JSON 物件，最外層不可為陣列。"
        "支援時物件欄位為 supported=true、scenario_title、recommendations、rounds；"
        "不支援時仍回傳物件，並使用 supported=false、scenario_title=\"\"、"
        "recommendations=[]、rounds=[]。只輸出 JSON，不得使用 Markdown 或解釋。"
    )
    user_prompt = json.dumps(
        {
            "proposal": proposal,
            "answers": answers,
            "simulation_round_count": SIMULATION_ROUND_COUNT,
            "game_config": {
                "metric_labels": game_config["metric_labels"],
                "initial_metrics": game_config["initial_metrics"],
            },
            "limits": {
                "scenario_title": 30,
                "plan_title": 30,
                "strategy": 24,
                "description": 90,
                "reason": 90,
                "round_event": 100,
                "action_text": 70,
            },
            "effect_ranges": METRIC_RANGES,
        },
        ensure_ascii=False,
    )
    data = _request_gemini(
        system_prompt, user_prompt, PLAN_RESPONSE_SCHEMA
    )
    return _validate_recommendation(data)


def _validate_recommendation(data):
    if not isinstance(data, dict):
        raise ValueError("方案回覆格式錯誤：根節點必須為物件。")
    if data.get("supported") is False:
        return {
            "supported": False,
            "scenario_title": "",
            "recommendations": [],
            "rounds": [],
        }
    if data.get("supported") is not True:
        raise ValueError("方案回覆格式錯誤：缺少有效的 supported 欄位。")

    scenario_title = _validate_text(data.get("scenario_title"), 30, "情境名稱格式錯誤。")
    recommendations = data.get("recommendations")
    rounds = data.get("rounds")
    if not isinstance(recommendations, list) or len(recommendations) != 2:
        raise ValueError("方案數量格式錯誤：必須恰好為兩個方案。")
    if not isinstance(rounds, list) or len(rounds) != SIMULATION_ROUND_COUNT:
        raise ValueError(
            f"模擬回合格式錯誤：必須恰好為 {SIMULATION_ROUND_COUNT} 個回合。"
        )

    strategies = set()
    validated_plans = []
    for index, plan in enumerate(recommendations):
        if not isinstance(plan, dict):
            raise ValueError("方案格式錯誤。")
        title = _validate_text(plan.get("title"), 30, "方案標題格式錯誤。")
        strategy = _validate_text(plan.get("strategy"), 24, "方案策略格式錯誤。")
        normalized = strategy.lower()
        if normalized in strategies:
            raise ValueError("方案策略格式錯誤：兩個策略不能完全重複。")
        strategies.add(normalized)
        description = _validate_text(plan.get("description"), 90, "方案描述格式錯誤。")
        reason = _validate_text(plan.get("reason"), 90, "方案理由格式錯誤。")
        effects = _validate_effects(
            plan.get("effects"), METRIC_RANGES["plan"], "方案效果格式錯誤："
        )
        validated_plans.append({
            "plan_id": f"plan_{index + 1}",
            "title": title,
            "strategy": strategy,
            "description": description,
            "reason": reason,
            "effects": effects,
        })

    validated_rounds = []
    for round_index, round_data in enumerate(rounds):
        if not isinstance(round_data, dict):
            raise ValueError("模擬回合格式錯誤。")
        event = _validate_text(round_data.get("event"), 100, "回合事件格式錯誤。")
        actions = round_data.get("actions")
        if not isinstance(actions, list) or len(actions) != 2:
            raise ValueError("回合行動格式錯誤：每回合必須恰好有兩個行動。")
        validated_actions = []
        for action_index, action in enumerate(actions):
            if not isinstance(action, dict):
                raise ValueError("行動格式錯誤。")
            text = _validate_text(action.get("text"), 70, "行動文字格式錯誤。")
            effects = _validate_effects(
                action.get("effects"),
                METRIC_RANGES["action"],
                "行動效果格式錯誤：",
            )
            validated_actions.append({
                "action_id": f"r{round_index + 1}_a{action_index + 1}",
                "text": text,
                "effects": effects,
            })
        validated_rounds.append({
            "round_id": f"round_{round_index + 1}",
            "event": event,
            "actions": validated_actions,
        })

    return {
        "supported": True,
        "scenario_title": scenario_title,
        "recommendations": validated_plans,
        "rounds": validated_rounds,
    }


def _demo_recommendation():
    return {
        "supported": True,
        "scenario_title": "校園服務改善示範",
        "recommendations": [
            {
                "plan_id": "plan_1",
                "title": "分時段改善方案",
                "strategy": "分時段輪流使用",
                "description": "依需求時段調整資源，先改善最需要的校園服務。",
                "reason": "能兼顧使用便利與公平分配。",
                "effects": {
                    "budget_remaining": -10,
                    "problem_improvement": 10,
                    "satisfaction": 5,
                    "fairness": 5,
                },
            },
            {
                "plan_id": "plan_2",
                "title": "集中資源方案",
                "strategy": "集中資源快速處理",
                "description": "集中預算處理單一重點問題，以求明顯改善。",
                "reason": "能在短期帶來較快的問題改善。",
                "effects": {
                    "budget_remaining": -15,
                    "problem_improvement": 15,
                    "satisfaction": 0,
                    "fairness": -5,
                },
            },
        ],
        "rounds": [
            {
                "round_id": "round_1",
                "event": "第一次試行後，部分學生反映使用方式不夠清楚。",
                "actions": [
                    {
                        "action_id": "r1_a1",
                        "text": "增加說明並安排協助",
                        "effects": {
                            "budget_remaining": -5,
                            "problem_improvement": 5,
                            "satisfaction": 5,
                            "fairness": 2,
                        },
                    },
                    {
                        "action_id": "r1_a2",
                        "text": "維持原方式並收集意見",
                        "effects": {
                            "budget_remaining": 0,
                            "problem_improvement": 2,
                            "satisfaction": -2,
                            "fairness": 0,
                        },
                    },
                ],
            },
            {
                "round_id": "round_2",
                "event": "第二回合需要決定是否擴大試行範圍。",
                "actions": [
                    {
                        "action_id": "r2_a1",
                        "text": "擴大範圍並增加名額",
                        "effects": {
                            "budget_remaining": -8,
                            "problem_improvement": 8,
                            "satisfaction": 4,
                            "fairness": 3,
                        },
                    },
                    {
                        "action_id": "r2_a2",
                        "text": "小規模試行並持續評估",
                        "effects": {
                            "budget_remaining": -3,
                            "problem_improvement": 4,
                            "satisfaction": 2,
                            "fairness": 4,
                        },
                    },
                ],
            },
            {
                "round_id": "round_3",
                "event": "試行後蒐集到更多使用情況，需要決定如何持續調整。",
                "actions": [
                    {
                        "action_id": "r3_a1",
                        "text": "依據意見微調服務安排",
                        "effects": {
                            "budget_remaining": -2,
                            "problem_improvement": 4,
                            "satisfaction": 3,
                            "fairness": 3,
                        },
                    },
                    {
                        "action_id": "r3_a2",
                        "text": "維持現況並定期檢視",
                        "effects": {
                            "budget_remaining": 0,
                            "problem_improvement": 2,
                            "satisfaction": 1,
                            "fairness": 2,
                        },
                    },
                ],
            },
        ],
    }


def choose_review_focus(record):
    if os.environ.get("DEMO_MODE") == "1":
        return _fallback_review_focus(record)

    system_prompt = (
        "你只負責從已記錄資料中選擇回顧焦點。"
        "只能回傳一個存在的 focus_metric 和一個有效的 action_index。"
    )
    user_prompt = json.dumps({
        "final_metrics": record["final_metrics"],
        "plan_name": record["plan_title"],
        "plan_strategy": record["plan_strategy"],
        "actions": [
            {
                "action_index": index,
                "action_text": action["action_text"],
            }
            for index, action in enumerate(record["actions"])
        ],
    }, ensure_ascii=False)
    data = _request_gemini(
        system_prompt, user_prompt, REVIEW_RESPONSE_SCHEMA
    )
    focus = data.get("focus_metric")
    action_index = data.get("action_index")
    if focus not in record["final_metrics"]:
        raise ValueError("回顧焦點中的指標不存在於紀錄。")
    if isinstance(action_index, bool) or not isinstance(action_index, int):
        raise ValueError("回顧焦點中的行動索引無效。")
    if action_index < 0 or action_index >= len(record["actions"]):
        raise ValueError("回顧焦點中的行動索引不存在於紀錄。")
    return {"focus_metric": focus, "action_index": action_index}


def _fallback_review_focus(record):
    metrics = record["final_metrics"]
    lowest = min(metrics, key=lambda name: (metrics[name], name))
    actions = record.get("actions", [])
    return {
        "focus_metric": lowest,
        "action_index": 0 if actions else -1,
    }
