from datetime import datetime, timezone
import secrets


YEARS = 10
SEMESTERS_PER_YEAR = 2
TOTAL_TURNS = YEARS * SEMESTERS_PER_YEAR
GROUP_PORTRAITS = {
    "students": "portrait-student.svg",
    "faculty": "portrait-faculty.svg",
    "staff": "portrait-staff.svg",
}

RESIDENTS = (
    {
        "id": "lin_muqing", "name": "林沐晴", "role": "大學生", "group": "students",
        "concern": "課業與生活平衡", "personality": "熱心、容易替別人操心",
        "goal": "成立讓新生安心求助的同儕社群", "portrait": "portrait-lin-muqing.svg",
    },
    {
        "id": "chen_yian", "name": "陳以安", "role": "研究生", "group": "students",
        "concern": "研究資源與空間", "personality": "安靜、做事有條理",
        "goal": "完成研究並爭取海外交流機會", "portrait": "portrait-chen-yian.svg",
    },
    {
        "id": "zhou_mingzhe", "name": "周明哲", "role": "教授", "group": "faculty",
        "concern": "教學與研究負荷", "personality": "嚴謹、願意提攜後輩",
        "goal": "建立跨院合作的永續研究團隊", "portrait": "portrait-zhou-mingzhe.svg",
    },
    {
        "id": "xu_yawen", "name": "許雅雯", "role": "教授", "group": "faculty",
        "concern": "研究支持與合作", "personality": "好奇、擅長傾聽",
        "goal": "設計更多學生參與的實作課程", "portrait": "portrait-xu-yawen.svg",
    },
    {
        "id": "wang_sihan", "name": "王思涵", "role": "行政人員", "group": "staff",
        "concern": "行政流程與人力", "personality": "細心、喜歡把事情安排妥當",
        "goal": "讓校園行政服務更簡單又友善", "portrait": "portrait-wang-sihan.svg",
    },
    {
        "id": "zhang_jiahao", "name": "張家豪", "role": "校園服務人員", "group": "staff",
        "concern": "服務品質與工作條件", "personality": "爽朗、遇到問題就想動手處理",
        "goal": "改善校園維護工具與安全設備", "portrait": "portrait-zhang-jiahao.svg",
    },
    {
        "id": "li_chengen", "name": "李承恩", "role": "通勤學生", "group": "students",
        "concern": "交通與校園安全", "personality": "務實、重視時間安排",
        "goal": "組成安全通勤倡議小組", "portrait": "portrait-li-chengen.svg",
    },
    {
        "id": "huang_kexin", "name": "黃可欣", "role": "國際學生", "group": "students",
        "concern": "友善環境與資訊取得", "personality": "勇於嘗試、喜歡認識新朋友",
        "goal": "籌辦讓不同文化交流的校園活動", "portrait": "portrait-huang-kexin.svg",
    },
)

def resident_profiles(residents=None):
    source = residents if residents is not None else RESIDENTS
    fields = (
        "id", "name", "role", "group", "concern", "personality", "goal",
        "satisfaction", "trust", "stress",
    )
    return [
        {field: resident[field] for field in fields if field in resident}
        for resident in source
    ]


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
def _bounded(value, minimum=0, maximum=100):
    return max(minimum, min(maximum, int(round(value))))


def _refresh_metrics(state):
    satisfaction_values = [resident["satisfaction"] for resident in state["residents"]]
    state["metrics"]["satisfaction"] = _bounded(
        sum(satisfaction_values) / len(satisfaction_values)
    )
    state["metrics"]["budget_remaining"] = _bounded(state["treasury"] / 12)


def _materialize_event(state, raw_event, turn):
    group = raw_event["group"]
    if group not in GROUP_NAMES:
        raise ValueError("AI 事件格式錯誤：受影響對象無效。")
    source = raw_event.get("source", "gemini")
    resident_id = raw_event.get("resident_id")
    resident = next(
        (item for item in state["residents"] if item["id"] == resident_id),
        None,
    )
    if resident is None or resident["group"] != group:
        raise ValueError("AI 事件格式錯誤：指定的教職員生不存在或類型不符。")
    actions = []
    for action in raw_event["actions"]:
        effects = dict(action["effects"])
        actions.append({
            "action_id": action["action_id"],
            "title": action["title"],
            "text": action["text"],
            "cost": action["cost"],
            "effects": effects,
            "resident_effects": dict(action["resident_effects"]),
            "resources": {},
            "group_effect": effects["satisfaction"],
            "cause": f"這項決策使問題改善 {effects['problem_improvement']:+d}、滿意度 {effects['satisfaction']:+d}、公平性 {effects['fairness']:+d}",
        })
    return {
        "title": (
            "離線示範起始議題" if source == "demo" else "玩家提出的起始議題"
        ) if turn == 0 else (
            "離線示範延伸議題" if source == "demo" else "AI 延伸校園議題"
        ),
        "event": raw_event["event"],
        "category": raw_event["category"],
        "group": group,
        "group_label": GROUP_NAMES[group],
        "resident": resident,
        "actions": actions,
        "quote": raw_event["resident_quote"],
        "resident_concern": raw_event["resident_concern"],
        "source": source,
    }


def new_campaign(concern, event_deck, plan, scenario_title, seed=None):
    concern = (concern or "").strip()
    if not concern or len(concern) > 300:
        raise ValueError("校園議題需為 1 到 300 個字。")
    if not isinstance(event_deck, list) or not event_deck:
        raise ValueError("尚未產生校園事件，請重新分析起始問題。")
    if not isinstance(plan, dict):
        raise ValueError("請先選擇一項 AI 校務方案。")
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
            dict(
                resident,
                satisfaction=68 + index % 5 * 3,
                trust=42 + index % 4 * 8,
                stress=38 + index % 4 * 9,
            )
            for index, resident in enumerate(RESIDENTS)
        ],
        "history": [],
        "yearly": [],
        "finished": False,
        "selected_plan": dict(plan),
        "scenario_title": scenario_title,
        "event_queue": list(event_deck[1:]),
    }
    for name, effect in plan["effects"].items():
        if name == "budget_remaining":
            state["treasury"] = max(0, min(2000, state["treasury"] + effect * 12))
        elif name == "satisfaction":
            for resident in state["residents"]:
                resident["satisfaction"] = _bounded(resident["satisfaction"] + effect)
        else:
            state["metrics"][name] = _bounded(state["metrics"][name] + effect)
    state["current_event"] = _materialize_event(state, event_deck[0], 0)
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
        "year": turn // SEMESTERS_PER_YEAR + 1,
        "semester": turn % SEMESTERS_PER_YEAR + 1,
        "turn_number": turn + 1,
        "total_turns": TOTAL_TURNS,
        "progress": turn * 100 // TOTAL_TURNS,
        "event": state["current_event"],
        "selected_plan": state["selected_plan"],
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


def validate_campaign_choice(state, action_id, development_id):
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
    return action, development


def _update_residents(state, group, change):
    for resident in state["residents"]:
        if resident["group"] == group:
            resident["satisfaction"] = _bounded(
                resident["satisfaction"] + change * (1 if resident is state["current_event"]["resident"] else 0.35)
            )


def advance_campaign(state, action_id, development_id, next_events=None):
    action, development = validate_campaign_choice(state, action_id, development_id)
    event = state["current_event"]
    if state["turn"] + 1 < TOTAL_TURNS and not state["event_queue"] and not next_events:
        raise ValueError("下一批 AI 校園事件尚未準備完成。")

    state["treasury"] -= action["cost"] + development["cost"]
    state["treasury"] += development.get("treasury_gain", 0)
    _apply_effects(state, action["effects"])
    _apply_effects(state, development["effects"])
    for resource, amount in action["resources"].items():
        state["resources"][resource] = _bounded(state["resources"][resource] + amount)
    for resource, amount in development["resources"].items():
        state["resources"][resource] = _bounded(state["resources"][resource] + amount)
    _update_residents(state, event["group"], action["group_effect"])
    personal_effects = action["resident_effects"]
    event["resident"]["trust"] = _bounded(
        event["resident"]["trust"] + personal_effects["trust"]
    )
    event["resident"]["stress"] = _bounded(
        event["resident"]["stress"] + personal_effects["stress"]
    )
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
    year = (state["turn"] - 1) // SEMESTERS_PER_YEAR + 1

    if state["turn"] % SEMESTERS_PER_YEAR == 0:
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
        if not state["event_queue"]:
            state["event_queue"] = list(next_events[1:])
            next_raw_event = next_events[0]
        else:
            next_raw_event = state["event_queue"].pop(0)
        next_event = _materialize_event(state, next_raw_event, state["turn"])

    outcome = {
        "year": year,
        "semester": (state["turn"] - 1) % SEMESTERS_PER_YEAR + 1,
        "event": event["event"],
        "resident": event["resident"]["name"],
        "role": event["resident"]["role"],
        "resident_trust": event["resident"]["trust"],
        "resident_stress": event["resident"]["stress"],
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
        "scenario_title": state["scenario_title"],
        "proposal": state["concern"],
        "plan_title": state["selected_plan"]["title"],
        "plan_strategy": state["selected_plan"]["strategy"],
        "plan_description": state["selected_plan"]["description"],
        "plan_reason": state["selected_plan"]["reason"],
        "plan_effects": dict(state["selected_plan"]["effects"]),
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
