from datetime import datetime, timezone
import random
import secrets


YEARS = 10
QUARTERS_PER_YEAR = 4
TOTAL_TURNS = YEARS * QUARTERS_PER_YEAR

RESIDENTS = (
    {"name": "林沐晴", "role": "學生", "group": "students", "concern": "課業與生活平衡"},
    {"name": "陳以安", "role": "研究生", "group": "students", "concern": "研究資源與空間"},
    {"name": "周明哲", "role": "教授", "group": "faculty", "concern": "教學與研究負荷"},
    {"name": "許雅雯", "role": "教授", "group": "faculty", "concern": "研究支持與合作"},
    {"name": "王思涵", "role": "行政人員", "group": "staff", "concern": "行政流程與人力"},
    {"name": "張家豪", "role": "校園服務人員", "group": "staff", "concern": "服務品質與工作條件"},
    {"name": "李承恩", "role": "通勤學生", "group": "students", "concern": "交通與校園安全"},
    {"name": "黃可欣", "role": "國際學生", "group": "students", "concern": "友善環境與資訊取得"},
)

EVENTS = (
    {"category": "infrastructure", "title": "老舊教室設備頻繁故障", "group": "faculty"},
    {"category": "wellbeing", "title": "期中考週壓力與身心狀況受到關注", "group": "students"},
    {"category": "policy", "title": "不同學院對資源分配提出疑問", "group": "faculty"},
    {"category": "environment", "title": "熱浪讓教室空調與用電需求上升", "group": "students"},
    {"category": "finance", "title": "營運成本上升，年度預算需要重新盤點", "group": "staff"},
    {"category": "accessibility", "title": "無障礙動線在施工期間受到影響", "group": "students"},
    {"category": "infrastructure", "title": "宿舍候補人數增加，居住空間吃緊", "group": "students"},
    {"category": "wellbeing", "title": "校園諮商服務的等候時間拉長", "group": "students"},
    {"category": "policy", "title": "教師反映行政工作排擠教學與研究", "group": "faculty"},
    {"category": "environment", "title": "乾旱使校園用水調度面臨壓力", "group": "staff"},
    {"category": "finance", "title": "學生社團反映活動補助不敷需求", "group": "students"},
    {"category": "accessibility", "title": "新生反映校園資訊與服務不易取得", "group": "students"},
    {"category": "infrastructure", "title": "圖書館尖峰時段座位不足", "group": "students"},
    {"category": "wellbeing", "title": "校園餐飲選擇與價格引發討論", "group": "students"},
    {"category": "policy", "title": "跨院合作計畫需要更透明的審議制度", "group": "faculty"},
    {"category": "environment", "title": "高耗能設備讓校園減碳進度落後", "group": "staff"},
    {"category": "finance", "title": "校園維護人力不足，報修案件持續累積", "group": "staff"},
    {"category": "accessibility", "title": "通勤尖峰的接駁與自行車停放空間不足", "group": "students"},
)

RESPONSES = (
    {
        "id": "listen",
        "title": "先聽取教職員生意見，組成跨單位工作小組",
        "cost": 10,
        "effects": {"problem_improvement": 2, "satisfaction": 3, "fairness": 4},
        "resources": {"staffing": -2},
        "group_effect": 4,
        "category": "policy",
        "cause": "教職員生參與增加，後續政策更貼近需求",
    },
    {
        "id": "act",
        "title": "立即投入資源，優先處理眼前問題",
        "cost": 34,
        "effects": {"problem_improvement": 8, "satisfaction": 3, "fairness": -1},
        "resources": {"energy": -2, "water": -1},
        "group_effect": 3,
        "category": "infrastructure",
        "cause": "快速改善緩解了眼前壓力，但增加資源負擔",
    },
    {
        "id": "phase",
        "title": "小規模試辦，蒐集成效後再決定是否擴大",
        "cost": 8,
        "effects": {"problem_improvement": 4, "satisfaction": 1, "fairness": 2},
        "resources": {"staffing": -1},
        "group_effect": 2,
        "category": "accessibility",
        "cause": "試辦累積了資料，讓下一步調整更有依據",
    },
)

DEVELOPMENTS = (
    {
        "id": "library",
        "category": "建設",
        "title": "擴建學習與研究空間",
        "cost": 145,
        "effects": {"problem_improvement": 2, "satisfaction": 2, "fairness": 1},
        "resources": {"staffing": 1},
        "building": "library",
        "benefit": "校園學習空間與研究容量提升",
    },
    {
        "id": "housing",
        "category": "建設",
        "title": "增建宿舍與公共生活空間",
        "cost": 170,
        "effects": {"problem_improvement": 1, "satisfaction": 3, "fairness": 1},
        "resources": {"water": -1, "energy": -1},
        "building": "housing",
        "benefit": "居住容量增加，學生生活滿意度改善",
    },
    {
        "id": "wellbeing",
        "category": "建設",
        "title": "設置健康支持與諮詢中心",
        "cost": 125,
        "effects": {"problem_improvement": 2, "satisfaction": 3, "fairness": 2},
        "resources": {"staffing": -1},
        "building": "wellbeing",
        "benefit": "身心支持服務與校園韌性提升",
    },
    {
        "id": "scholarships",
        "category": "政策",
        "title": "擴大急難與弱勢助學支持",
        "cost": 75,
        "effects": {"problem_improvement": 1, "satisfaction": 2, "fairness": 5},
        "resources": {},
        "policy": "scholarships",
        "group_effect": 2,
        "benefit": "經濟支持更普及，公平性提升",
    },
    {
        "id": "workload",
        "category": "政策",
        "title": "簡化行政流程與教職員工作負荷",
        "cost": 60,
        "effects": {"problem_improvement": 2, "satisfaction": 2, "fairness": 2},
        "resources": {"staffing": 4},
        "policy": "workload",
        "group_effect": 2,
        "benefit": "行政與教學流程改善，教職員時間增加",
    },
    {
        "id": "accessibility",
        "category": "政策",
        "title": "推動無障礙與多語服務標準",
        "cost": 65,
        "effects": {"problem_improvement": 2, "satisfaction": 2, "fairness": 4},
        "resources": {},
        "policy": "accessibility",
        "group_effect": 2,
        "benefit": "校園服務對不同背景的教職員生更友善",
    },
    {
        "id": "conservation",
        "category": "資源",
        "title": "汰換高耗能設備並節水",
        "cost": 45,
        "effects": {"problem_improvement": 1, "satisfaction": 1, "fairness": 1},
        "resources": {"energy": 9, "water": 9},
        "policy": "conservation",
        "benefit": "能源與用水韌性提升，長期營運成本下降",
    },
    {
        "id": "training",
        "category": "資源",
        "title": "培訓校園服務與支援人力",
        "cost": 40,
        "effects": {"problem_improvement": 2, "satisfaction": 2, "fairness": 1},
        "resources": {"staffing": 10},
        "policy": "training",
        "group_effect": 2,
        "benefit": "服務量能提升，教職員生等待時間縮短",
    },
    {
        "id": "audit",
        "category": "財政",
        "title": "盤點採購與合約，回收閒置預算",
        "cost": 15,
        "treasury_gain": 48,
        "effects": {"problem_improvement": 1, "satisfaction": 0, "fairness": 1},
        "resources": {},
        "benefit": "財務透明度提升並釋出可運用預算",
    },
    {
        "id": "austerity",
        "category": "財政",
        "title": "暫緩非必要支出，優先守住基本服務",
        "cost": 0,
        "treasury_gain": 32,
        "effects": {"problem_improvement": -1, "satisfaction": -2, "fairness": -1},
        "resources": {"staffing": -2},
        "benefit": "短期財務壓力下降，但教職員生服務承受代價",
    },
)

GROUP_NAMES = {"students": "學生", "faculty": "教職員", "staff": "行政與服務人員"}
RESOURCE_LABELS = {"energy": "能源", "water": "用水", "staffing": "人力"}
BUILDING_LABELS = {"library": "學習空間", "housing": "宿舍", "wellbeing": "健康支持中心"}
POLICY_LABELS = {
    "scholarships": "助學支持",
    "workload": "簡政減負",
    "accessibility": "無障礙與多語服務",
    "conservation": "節能節水",
    "training": "服務人力培訓",
}
DEVELOPMENT_EVENT_CATEGORIES = {
    "建設": "infrastructure",
    "政策": "policy",
    "資源": "environment",
    "財政": "finance",
}


def _bounded(value, minimum=0, maximum=100):
    return max(minimum, min(maximum, int(round(value))))


def _refresh_metrics(state):
    satisfaction_values = [resident["satisfaction"] for resident in state["residents"]]
    state["metrics"]["satisfaction"] = _bounded(
        sum(satisfaction_values) / len(satisfaction_values)
    )
    state["metrics"]["budget_remaining"] = _bounded(state["treasury"] / 12)


def _event_for(state, turn, starting_concern=None, cause_category=None):
    rng = random.Random(f"{state['seed']}:{turn}")
    if starting_concern:
        category = "infrastructure"
        issue = starting_concern
        group = "students"
        title = "你提出的校園議題"
    else:
        events = list(EVENTS)
        previous_category = DEVELOPMENT_EVENT_CATEGORIES.get(cause_category)
        if previous_category:
            favored = [event for event in events if event["category"] == previous_category]
            events.extend(favored)
        if state["metrics"]["budget_remaining"] < 35:
            events.extend(event for event in EVENTS if event["category"] == "finance")
        if min(state["resources"].values()) < 35:
            events.extend(event for event in EVENTS if event["category"] == "environment")
        event = rng.choice(events)
        category = event["category"]
        issue = event["title"]
        group = event["group"]
        title = "校園突發議題"

    residents = [resident for resident in state["residents"] if resident["group"] == group]
    resident = rng.choice(residents)
    actions = []
    for template in RESPONSES:
        action = dict(template)
        action["effects"] = dict(template["effects"])
        action["resources"] = dict(template["resources"])
        action["action_id"] = template["id"]
        action["text"] = template["title"]
        actions.append(action)
    return {
        "title": title,
        "event": issue,
        "category": category,
        "group": group,
        "group_label": GROUP_NAMES[group],
        "resident": resident,
        "actions": actions,
        "quote": f"「{resident['concern']}是我最近最在意的事，希望學校能讓我們知道後續。」",
    }


def new_campaign(concern, seed=None):
    concern = (concern or "").strip()
    if not concern or len(concern) > 160:
        raise ValueError("校園議題需為 1 到 160 個字。")
    if seed is None:
        seed = secrets.randbits(64)
    state = {
        "seed": seed,
        "concern": concern,
        "turn": 0,
        "treasury": 850,
        "population": {"students": 9000, "faculty": 720, "staff": 380},
        "resources": {"energy": 68, "water": 72, "staffing": 64},
        "buildings": {"library": 0, "housing": 0, "wellbeing": 0},
        "policies": {},
        "metrics": {"budget_remaining": 71, "problem_improvement": 45, "satisfaction": 70, "fairness": 63},
        "residents": [
            dict(resident, satisfaction=68 + index % 5 * 3)
            for index, resident in enumerate(RESIDENTS)
        ],
        "history": [],
        "yearly": [],
        "finished": False,
    }
    state["current_event"] = _event_for(state, 0, starting_concern=concern)
    _refresh_metrics(state)
    return state


def available_developments(state):
    options = []
    for item in DEVELOPMENTS:
        if item.get("building") and state["buildings"][item["building"]] >= 3:
            continue
        if item.get("policy") and state["policies"].get(item["policy"], 0) >= 3:
            continue
        if item["cost"] > state["treasury"]:
            continue
        option = dict(item)
        option["effects"] = dict(item["effects"])
        option["resources"] = dict(item["resources"])
        options.append(option)
    return options


def campaign_context(state):
    turn = state["turn"]
    return {
        "year": turn // QUARTERS_PER_YEAR + 1,
        "quarter": turn % QUARTERS_PER_YEAR + 1,
        "turn_number": turn + 1,
        "total_turns": TOTAL_TURNS,
        "progress": turn * 100 // TOTAL_TURNS,
        "event": state["current_event"],
        "metrics": dict(state["metrics"]),
        "treasury": state["treasury"],
        "population": dict(state["population"]),
        "resources": dict(state["resources"]),
        "resource_labels": RESOURCE_LABELS,
        "buildings": dict(state["buildings"]),
        "building_labels": BUILDING_LABELS,
        "policies": dict(state["policies"]),
        "policy_labels": POLICY_LABELS,
        "developments": available_developments(state),
        "residents": state["residents"],
        "history": state["history"],
        "yearly": state["yearly"],
        "forecast": forecast(state),
    }


def _apply_effects(state, effects):
    for key, amount in effects.items():
        if key in state["metrics"]:
            state["metrics"][key] = _bounded(state["metrics"][key] + amount)


def _update_residents(state, group, change):
    for resident in state["residents"]:
        if resident["group"] == group:
            resident["satisfaction"] = _bounded(
                resident["satisfaction"] + change * (1 if resident is state["current_event"]["resident"] else 0.35)
            )


def advance_campaign(state, action_id, development_id):
    if state["finished"] or state["turn"] >= TOTAL_TURNS:
        raise ValueError("這場十年經營已經結束。")
    event = state["current_event"]
    action = next((item for item in event["actions"] if item["action_id"] == action_id), None)
    if action is None:
        raise ValueError("請選擇有效的教職員生問題處理方式。")
    development = next(
        (item for item in available_developments(state) if item["id"] == development_id),
        None,
    )
    if development is None:
        raise ValueError("請選擇可負擔的建設、政策或資源方案。")
    net_cost = action["cost"] + development["cost"] - development.get("treasury_gain", 0)
    if net_cost > state["treasury"]:
        raise ValueError("校務基金不足以支應這組決策；請改選較低成本的回應或財政措施。")

    state["treasury"] -= action["cost"] + development["cost"]
    state["treasury"] += development.get("treasury_gain", 0)
    _apply_effects(state, action["effects"])
    _apply_effects(state, development["effects"])
    for resource, amount in action["resources"].items():
        state["resources"][resource] = _bounded(state["resources"][resource] + amount)
    for resource, amount in development["resources"].items():
        state["resources"][resource] = _bounded(state["resources"][resource] + amount)
    _update_residents(state, event["group"], action["group_effect"])
    if development.get("group_effect"):
        target_group = "faculty" if development.get("policy") == "workload" else "students"
        _update_residents(state, target_group, development["group_effect"])
    if development.get("building"):
        building = development["building"]
        state["buildings"][building] += 1
    if development.get("policy"):
        policy = development["policy"]
        state["policies"][policy] = state["policies"].get(policy, 0) + 1

    maintenance = sum(state["buildings"].values()) * 4
    revenue = 59 + min(12, state["population"]["students"] // 1000)
    state["treasury"] = max(0, min(2000, state["treasury"] + revenue - 58 - maintenance))
    _refresh_metrics(state)
    state["turn"] += 1
    year = (state["turn"] - 1) // QUARTERS_PER_YEAR + 1

    if state["turn"] % QUARTERS_PER_YEAR == 0:
        satisfaction = state["metrics"]["satisfaction"]
        student_delta = 80 if satisfaction >= 75 else (-80 if satisfaction < 45 else 15)
        state["population"]["students"] = max(0, state["population"]["students"] + student_delta)
        state["population"]["faculty"] = max(0, state["population"]["faculty"] + (12 if satisfaction >= 65 else -8))
        state["population"]["staff"] = max(0, state["population"]["staff"] + (6 if state["resources"]["staffing"] >= 40 else -5))
        state["yearly"].append({
            "year": year,
            "satisfaction": state["metrics"]["satisfaction"],
            "population": sum(state["population"].values()),
            "treasury": state["treasury"],
            "score": calculate_campaign_score(state),
        })

    next_event = None
    if state["turn"] >= TOTAL_TURNS:
        state["finished"] = True
    else:
        next_event = _event_for(
            state,
            state["turn"],
            cause_category=development["category"],
        )

    outcome = {
        "year": year,
        "quarter": (state["turn"] - 1) % QUARTERS_PER_YEAR + 1,
        "event": event["event"],
        "resident": event["resident"]["name"],
        "role": event["resident"]["role"],
        "response": action["title"],
        "development": development["title"],
        "category": development["category"],
        "benefit": development["benefit"],
        "cause": action["cause"],
        "next_event": next_event["event"] if next_event else "十年校務成果已完成",
        "butterfly": (
            f"{development['title']}使{development['benefit']}；"
            f"{action['cause']}，接續浮現「{next_event['event']}」"
            if next_event else f"{development['title']}使{development['benefit']}，十年改革進入成果盤點"
        ),
        "metrics": dict(state["metrics"]),
    }
    state["history"].append(outcome)
    state["last_outcome"] = outcome
    if next_event:
        state["current_event"] = next_event
    return outcome


def forecast(state):
    satisfaction = state["metrics"]["satisfaction"]
    resource_average = sum(state["resources"].values()) / len(state["resources"])
    population_change = 80 if satisfaction >= 75 else (-80 if satisfaction < 45 else 15)
    return {
        "next_year_population": max(0, sum(state["population"].values()) + population_change + 18),
        "next_year_satisfaction": _bounded(
            satisfaction + (3 if resource_average >= 60 and state["metrics"]["fairness"] >= 60 else -3)
        ),
        "risk": (
            "財政與資源緩衝偏低，建議先投資韌性"
            if state["treasury"] < 250 or resource_average < 35
            else "教職員生滿意度與公平性將影響招生及人才留任"
            if satisfaction < 55 or state["metrics"]["fairness"] < 50
            else "目前趨勢穩定，可逐步擴大長期建設"
        ),
    }


def calculate_campaign_score(state):
    resources = sum(state["resources"].values()) / len(state["resources"])
    campus = sum(state["buildings"].values()) / max(1, len(state["buildings"]) * 3) * 100
    values = [
        state["metrics"]["problem_improvement"],
        state["metrics"]["satisfaction"],
        state["metrics"]["fairness"],
        state["metrics"]["budget_remaining"],
        resources,
        campus,
    ]
    return int(sum(values) / len(values) + 0.5)


def make_campaign_record(state):
    score = calculate_campaign_score(state)
    return {
        "record_id": secrets.token_hex(16),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "scenario_id": "campus_decade",
        "scenario_title": f"十年校園經營：{state['concern']}",
        "proposal": state["concern"],
        "plan_title": "十年校務發展藍圖",
        "plan_strategy": "教職員生回應、設施建設與永續治理並進",
        "plan_description": "每季處理校園事件並選擇一項年度經營措施。",
        "initial_metrics": {
            "budget_remaining": 71, "problem_improvement": 45, "satisfaction": 70, "fairness": 63,
        },
        "final_metrics": dict(state["metrics"]),
        "metric_labels": {
            "budget_remaining": "財政健康",
            "problem_improvement": "問題改善",
            "satisfaction": "教職員生滿意度",
            "fairness": "公平性",
        },
        "total_score": score,
        "comment": (
            "十年校務兼顧了教職員生需求、財政韌性與長期發展。"
            if score >= 70 else "十年校務仍有改善空間，可優先補足低分指標並維持教職員生參與。"
        ),
        "years": YEARS,
        "history": state["history"],
        "yearly": state["yearly"],
        "population": dict(state["population"]),
        "resources": dict(state["resources"]),
        "buildings": dict(state["buildings"]),
        "building_labels": dict(BUILDING_LABELS),
        "policies": dict(state["policies"]),
        "policy_labels": dict(POLICY_LABELS),
        "treasury": state["treasury"],
        "residents": state["residents"],
        "forecast": forecast(state),
    }
