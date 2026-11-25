from datetime import datetime, timezone
import random
import secrets


YEARS = 5
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
    profiles = []
    for index, resident in enumerate(source):
        profile = {field: resident[field] for field in fields if field in resident}
        profile.setdefault("satisfaction", 68 + index % 5 * 3)
        profile.setdefault("trust", 42 + index % 4 * 8)
        profile.setdefault("stress", 38 + index % 4 * 9)
        profiles.append(profile)
    return profiles


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
ANNUAL_CHALLENGES = (
    {
        "id": "fiscal_resilience",
        "title": "財政韌性",
        "description": "本年度結束時校務基金至少保有 500 點。",
        "rule": "treasury",
    },
    {
        "id": "fair_access",
        "title": "公平校園",
        "description": "本年度結束時公平性達到 68。",
        "rule": "fairness",
    },
    {
        "id": "green_campus",
        "title": "永續校園",
        "description": "本年度結束時平均資源存量達到 60。",
        "rule": "resources",
    },
    {
        "id": "trusted_community",
        "title": "信任社群",
        "description": "本年度結束時教職員生平均信任達到 58。",
        "rule": "trust",
    },
    {
        "id": "campus_builder",
        "title": "校園升級",
        "description": "至少完成一項校園建設。",
        "rule": "buildings",
    },
    {
        "id": "healthy_semester",
        "title": "安心學期",
        "description": "本年度結束時教職員生平均壓力不高於 52。",
        "rule": "stress",
    },
    {
        "id": "popular_campus",
        "title": "幸福校園",
        "description": "本年度結束時教職員生滿意度達到 70。",
        "rule": "satisfaction",
    },
    {
        "id": "solve_root_cause",
        "title": "問題突破",
        "description": "本年度結束時問題改善度達到 60。",
        "rule": "problem",
    },
)
TITLE_CATALOG = (
    {"id": "equity_champion", "name": "公平推手", "description": "公平性達到 75。", "rule": "fairness"},
    {"id": "campus_favorite", "name": "人氣校長", "description": "教職員生滿意度達到 78。", "rule": "satisfaction"},
    {"id": "fiscal_guardian", "name": "財政守門員", "description": "校務基金維持在 700 點以上。", "rule": "treasury"},
    {"id": "green_guardian", "name": "永續守護者", "description": "平均資源存量達到 70。", "rule": "resources"},
    {"id": "master_builder", "name": "空間築夢家", "description": "累計完成三項校園建設。", "rule": "buildings"},
    {"id": "trusted_leader", "name": "傾聽者", "description": "教職員生平均信任達到 58。", "rule": "trust"},
    {"id": "wellbeing_guardian", "name": "安心守護者", "description": "教職員生平均壓力降至 46 以下。", "rule": "stress"},
    {"id": "problem_solver", "name": "問題終結者", "description": "問題改善度達到 75。", "rule": "problem"},
    {"id": "challenge_collector", "name": "挑戰收藏家", "description": "完成至少三項年度挑戰。", "rule": "challenges"},
    {"id": "five_year_legend", "name": "五年傳奇", "description": "完成五年經營並取得 85 分以上。", "rule": "champion"},
)

CAMPUS_PROFILES = (
    {
        "id": "metro_commuter",
        "name": "都會通勤校園",
        "description": "通勤學生多，尖峰服務需求高；人力與公平性需要優先照顧。",
        "treasury_delta": -90,
        "population_delta": {"students": 1200, "faculty": 0, "staff": 20},
        "resource_delta": {"energy": -4, "water": -3, "staffing": -6},
        "metric_delta": {"satisfaction": -3, "fairness": -2},
        "resident_delta": {"students": {"stress": 6}},
    },
    {
        "id": "research_hub",
        "name": "研究重鎮",
        "description": "研究量能與教職員規模較大；能源消耗和教學負荷是隱憂。",
        "treasury_delta": 80,
        "population_delta": {"students": -300, "faculty": 100, "staff": 20},
        "resource_delta": {"energy": -8, "water": 0, "staffing": 3},
        "metric_delta": {"problem_improvement": 5, "satisfaction": -2},
        "resident_delta": {"faculty": {"stress": 6}},
    },
    {
        "id": "regional_community",
        "name": "地方共融校園",
        "description": "校園與在地連結緊密；資源有限但社群互助基礎良好。",
        "treasury_delta": 120,
        "population_delta": {"students": -900, "faculty": 20, "staff": 40},
        "resource_delta": {"energy": 0, "water": 5, "staffing": -3},
        "metric_delta": {"satisfaction": 3, "fairness": 7},
        "resident_delta": {"students": {"trust": 4}},
    },
    {
        "id": "innovation_campus",
        "name": "新興創意校園",
        "description": "新學院與社團快速成長；機會多，但服務量能仍在追趕。",
        "treasury_delta": -100,
        "population_delta": {"students": 600, "faculty": 40, "staff": 0},
        "resource_delta": {"energy": 5, "water": 5, "staffing": -4},
        "metric_delta": {"problem_improvement": 4, "satisfaction": 4, "fairness": -2},
        "resident_delta": {"students": {"stress": 4}, "staff": {"stress": 3}},
    },
)

EVENT_TYPE_INFO = {
    "crisis": {
        "label": "緊急危機",
        "hint": "情勢正在升溫，本學期的處理方式會影響後續損失。",
        "rule": "回應本身的問題改善達 +5，成功止損；未達標會額外損失 2 點改善，焦點角色壓力 +2。",
    },
    "opportunity": {
        "label": "限時機會",
        "hint": "校外或校內出現短期機會，請衡量投入、回報與機會成本。",
        "rule": "若延遲改善至少 +4 且公平效果不為負，本回合校務基金額外 +20。",
    },
    "negotiation": {
        "label": "角色協商",
        "hint": "不同群體各有立場，協調方式會改變當事人的信任與公平感。",
        "rule": "公平效果達 +3，焦點角色額外信任 +2；公平效果為負，信任 -2。",
    },
    "campus_vote": {
        "label": "校園投票",
        "hint": "教職員生意見不一，決策需在多數支持與少數需求間取捨。",
        "rule": "公平效果達 +2，事件群體滿意度 +2；否則投票未過，群體滿意度 -2。",
    },
    "character_story": {
        "label": "人物故事",
        "hint": "事件關係到一位教職員生的個人目標與長期發展。",
        "rule": "主線幕次會累積信任、壓力與公平的支持值，並影響第三幕結局。",
    },
}

CAMPUS_REACTIONS = {
    "crisis": (
        "校務群組的驚嘆號依然很忙，但至少有了處理方向。",
        "消防栓今天有出場，還好不是只負責背景。",
        "緊急會議終於不只是在聊天室打「收到」。",
    ),
    "opportunity": (
        "機會就像限時優惠，校務基金先看完條款再按下去。",
        "基金與機會的相遇，至少有留下會議紀錄。",
        "下學期的自己表示：這次先把條件看清楚。",
    ),
    "negotiation": (
        "協商桌上沒有秒讀不回，已經是一種進展。",
        "「先這樣」今天多附了一份具體後續事項。",
        "會議紀錄不是連載，至少這一章有個句點。",
    ),
    "campus_vote": (
        "有票有真相，少數意見也能留在紀錄上。",
        "投票結果出爐，表單今天終於不是唯一主角。",
        "票數之外，也記得看一下沒來得及舉手的人。",
    ),
    "character_story": (
        "主線進度條動了，角色目標沒有繼續在待辦清單裡吃灰。",
        "群組的「收到」沒有變成大結局，支線還在更新。",
        "角色成長中，這次不是只解鎖「已讀」成就。",
    ),
}

DEVELOPMENT_PUNS = {
    "建設": ("有建設，才有建樹。", "校園地圖升級，終於不是只多一個群組。"),
    "政策": ("表單少一張，心情多一章。", "流程開始瘦身，同仁不用再替文件跑馬拉松。"),
    "資源": ("節能節水，水到渠成。", "資源省著用，耐心不用省著給。"),
    "財政": ("財政有節，校務不劫。", "帳本先喘口氣，會計室眉頭少打一個結。"),
}


def story_arc_for_seed(seed):
    resident = random.Random(f"{seed}:resident-story").choice(RESIDENTS)
    return {
        "id": f"story_{resident['id']}",
        "title": f"{resident['name']}的三學期支線",
        "resident_id": resident["id"],
        "resident_name": resident["name"],
        "resident_role": resident["role"],
        "group": resident["group"],
        "concern": resident["concern"],
        "goal": resident["goal"],
        "stage": 0,
        "next_stage": 1,
        "support_score": 0,
        "ending": None,
        "ending_text": None,
        "last_beat": None,
    }


def next_story_arc_context(state, action=None):
    story = dict(state["story_arc"])
    current_stage = state["current_event"]["story_stage"]
    if current_stage:
        story["stage"] = current_stage
        story["next_stage"] = current_stage + 1 if current_stage < 3 else 0
        if action:
            story["support_score"] += (
                action["resident_effects"]["trust"]
                - action["resident_effects"]["stress"]
                + action["effects"]["fairness"]
            )
    return story


def _copy_campus_profile(profile):
    return {
        **profile,
        "population_delta": dict(profile["population_delta"]),
        "resource_delta": dict(profile["resource_delta"]),
        "metric_delta": dict(profile["metric_delta"]),
        "resident_delta": {
            group: dict(effects)
            for group, effects in profile["resident_delta"].items()
        },
    }


def campus_profile_for_seed(seed):
    profile = random.Random(f"{seed}:campus-profile").choice(CAMPUS_PROFILES)
    return _copy_campus_profile(profile)


def apply_campus_profile(state, profile):
    state["treasury"] = max(0, min(2000, state["treasury"] + profile["treasury_delta"]))
    for population, change in profile["population_delta"].items():
        state["population"][population] = max(0, state["population"][population] + change)
    for resource, change in profile["resource_delta"].items():
        state["resources"][resource] = _bounded(state["resources"][resource] + change)
    for metric, change in profile["metric_delta"].items():
        state["metrics"][metric] = _bounded(state["metrics"][metric] + change)
    residents = state.get("residents", state.get("characters", []))
    for resident in residents:
        for field, change in profile["resident_delta"].get(resident["group"], {}).items():
            if field in resident:
                resident[field] = _bounded(resident[field] + change)
    return state


def _bounded(value, minimum=0, maximum=100):
    return max(minimum, min(maximum, int(round(value))))


def _refresh_metrics(state):
    satisfaction_values = [resident["satisfaction"] for resident in state["residents"]]
    state["metrics"]["satisfaction"] = _bounded(
        sum(satisfaction_values) / len(satisfaction_values)
    )
    state["metrics"]["budget_remaining"] = _bounded(state["treasury"] / 12)


def _average_resident_metric(state, metric):
    return sum(resident[metric] for resident in state["residents"]) / len(state["residents"])


def _challenge_is_complete(state, challenge):
    rule = challenge["rule"]
    if rule == "treasury":
        return state["treasury"] >= 500
    if rule == "fairness":
        return state["metrics"]["fairness"] >= 68
    if rule == "resources":
        return sum(state["resources"].values()) / len(state["resources"]) >= 60
    if rule == "trust":
        return _average_resident_metric(state, "trust") >= 58
    if rule == "buildings":
        return sum(state["buildings"].values()) >= 1
    if rule == "stress":
        return _average_resident_metric(state, "stress") <= 52
    if rule == "satisfaction":
        return state["metrics"]["satisfaction"] >= 70
    if rule == "problem":
        return state["metrics"]["problem_improvement"] >= 60
    raise ValueError(f"未知的年度挑戰規則：{rule}")


def _title_is_earned(state, rule):
    if rule == "fairness":
        return state["metrics"]["fairness"] >= 75
    if rule == "satisfaction":
        return state["metrics"]["satisfaction"] >= 78
    if rule == "treasury":
        return state["treasury"] >= 700
    if rule == "resources":
        return sum(state["resources"].values()) / len(state["resources"]) >= 70
    if rule == "buildings":
        return sum(state["buildings"].values()) >= 3
    if rule == "trust":
        return _average_resident_metric(state, "trust") >= 58
    if rule == "stress":
        return _average_resident_metric(state, "stress") <= 46
    if rule == "problem":
        return state["metrics"]["problem_improvement"] >= 75
    if rule == "challenges":
        return sum(challenge["completed"] for challenge in state["challenges"]) >= 3
    if rule == "champion":
        return state["finished"] and calculate_campaign_score(state) >= 85
    return False


def _award_available_titles(state):
    earned_ids = {title["id"] for title in state["titles"]}
    for title in TITLE_CATALOG:
        if title["id"] in earned_ids or not _title_is_earned(state, title["rule"]):
            continue
        state["titles"].append({
            "id": title["id"],
            "name": title["name"],
            "description": title["description"],
            "earned_turn": state["turn"],
        })


def _materialize_event(state, raw_event, turn):
    group = raw_event["group"]
    if group not in GROUP_NAMES:
        raise ValueError("AI 事件格式錯誤：受影響對象無效。")
    story_stage = raw_event.get("story_stage", 0)
    source = raw_event.get("source", "gemini")
    resident_id = raw_event.get("resident_id")
    resident = next(
        (item for item in state["residents"] if item["id"] == resident_id),
        None,
    )
    if resident is None or resident["group"] != group:
        raise ValueError("AI 事件格式錯誤：指定的教職員生不存在或類型不符。")
    if story_stage and (
        resident["id"] != state["story_arc"]["resident_id"]
        or story_stage != state["story_arc"]["next_stage"]
    ):
        raise ValueError("AI 事件格式錯誤：人物故事線階段或角色不符。")
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
            "follow_up": action["follow_up"],
            "delayed_effects": dict(action["delayed_effects"]),
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
        "event_type": raw_event["event_type"],
        "event_type_label": EVENT_TYPE_INFO[raw_event["event_type"]]["label"],
        "event_type_hint": EVENT_TYPE_INFO[raw_event["event_type"]]["hint"],
        "event_type_rule": EVENT_TYPE_INFO[raw_event["event_type"]]["rule"],
        "story_stage": story_stage,
        "story_stage_label": f"人物故事第 {story_stage} 幕" if story_stage else None,
        "group": group,
        "group_label": GROUP_NAMES[group],
        "resident": resident,
        "actions": actions,
        "quote": raw_event["resident_quote"],
        "resident_concern": raw_event["resident_concern"],
        "source": source,
    }


def new_campaign(
    concern,
    event_deck,
    plan,
    scenario_title,
    seed=None,
    campus_profile_id=None,
):
    concern = (concern or "").strip()
    if not concern or len(concern) > 300:
        raise ValueError("校園議題需為 1 到 300 個字。")
    if not isinstance(event_deck, list) or not event_deck:
        raise ValueError("尚未產生校園事件，請重新分析起始問題。")
    if not isinstance(plan, dict):
        raise ValueError("請先選擇一項 AI 校務方案。")
    if seed is None:
        seed = secrets.randbits(64)
    challenge_deck = random.Random(seed).sample(ANNUAL_CHALLENGES, YEARS)
    if campus_profile_id is None:
        campus_profile = campus_profile_for_seed(seed)
    else:
        profile = next(
            (profile for profile in CAMPUS_PROFILES if profile["id"] == campus_profile_id),
            None,
        )
        if profile is None:
            raise ValueError("指定的校園開局條件不存在。")
        campus_profile = _copy_campus_profile(profile)
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
        "campus_profile": campus_profile,
        "story_arc": story_arc_for_seed(seed),
        "pending_consequences": [],
        "challenges": [
            dict(challenge, year=year, completed=False, reward=30)
            for year, challenge in enumerate(challenge_deck, start=1)
        ],
        "titles": [],
        "selected_plan": dict(plan),
        "scenario_title": scenario_title,
        "event_queue": list(event_deck[1:]),
    }
    apply_campus_profile(state, campus_profile)
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
    state["initial_metrics"] = dict(state["metrics"])
    _award_available_titles(state)
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
    residents = state["residents"]
    resource_values = state["resources"].values()
    story_arc = dict(state["story_arc"])
    if story_arc["stage"] == 0:
        story_arc["support_label"] = "故事即將展開"
    elif story_arc["support_score"] >= 18:
        story_arc["support_label"] = "合作默契穩固"
    elif story_arc["support_score"] >= 6:
        story_arc["support_label"] = "合作正在建立"
    else:
        story_arc["support_label"] = "信任仍需經營"
    return {
        "years": YEARS,
        "year": turn // SEMESTERS_PER_YEAR + 1,
        "semester": turn % SEMESTERS_PER_YEAR + 1,
        "turn_number": turn + 1,
        "total_turns": TOTAL_TURNS,
        "progress": turn * 100 // TOTAL_TURNS,
        "event": state["current_event"],
        "selected_plan": state["selected_plan"],
        "campus_profile": state["campus_profile"],
        "story_arc": story_arc,
        "metrics": dict(state["metrics"]),
        "averages": {
            "resource_stock": round(sum(resource_values) / len(state["resources"]), 1),
            "satisfaction": round(
                sum(resident["satisfaction"] for resident in residents) / len(residents),
                1,
            ),
            "trust": round(
                sum(resident["trust"] for resident in residents) / len(residents),
                1,
            ),
            "stress": round(
                sum(resident["stress"] for resident in residents) / len(residents),
                1,
            ),
        },
        "treasury": state["treasury"],
        "population": dict(state["population"]),
        "resources": dict(state["resources"]),
        "resource_labels": RESOURCE_LABELS,
        "buildings": dict(state["buildings"]),
        "building_labels": BUILDING_LABELS,
        "policies": dict(state["policies"]),
        "policy_labels": POLICY_LABELS,
        "developments": available_developments(state),
        "residents": residents,
        "history": state["history"],
        "yearly": state["yearly"],
        "current_challenge": state["challenges"][turn // SEMESTERS_PER_YEAR],
        "challenges": state["challenges"],
        "completed_challenge_count": sum(
            challenge["completed"] for challenge in state["challenges"]
        ),
        "pending_consequences": [
            {
                **consequence,
                "turns_left": max(0, consequence["due_turn"] - turn),
            }
            for consequence in state["pending_consequences"]
        ],
        "titles": state["titles"],
        "title_catalog": TITLE_CATALOG,
        "forecast": forecast(state),
    }


def _apply_effects(state, effects):
    for key, amount in effects.items():
        if key in state["metrics"]:
            state["metrics"][key] = _bounded(state["metrics"][key] + amount)


def validate_campaign_choice(state, action_id, development_id):
    if state["finished"] or state["turn"] >= TOTAL_TURNS:
        raise ValueError(f"這場 {YEARS} 年經營已經結束。")
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


def _resolve_event_rule(state, event, action):
    event_type = event["event_type"]
    effects = action["effects"]
    resident = event["resident"]

    if event_type == "crisis":
        if effects["problem_improvement"] >= 5:
            return "危機止損成功：本次改善達標，沒有追加損失。"
        state["metrics"]["problem_improvement"] = _bounded(
            state["metrics"]["problem_improvement"] - 2
        )
        resident["stress"] = _bounded(resident["stress"] + 2)
        return "止損未達門檻：問題改善額外 -2，焦點角色壓力 +2。"

    if event_type == "opportunity":
        delayed = action["delayed_effects"]
        if delayed["problem_improvement"] >= 4 and delayed["fairness"] >= 0:
            state["treasury"] = min(2000, state["treasury"] + 20)
            return "把握限時機會：校務基金獲得 20 點紅利。"
        return "機會稍縱即逝：本次未達紅利條件。"

    if event_type == "negotiation":
        if effects["fairness"] >= 3:
            resident["trust"] = _bounded(resident["trust"] + 2)
            return "協商取得公平共識：焦點角色信任額外 +2。"
        if effects["fairness"] < 0:
            resident["trust"] = _bounded(resident["trust"] - 2)
            return "協商失衡：焦點角色信任額外 -2。"
        return "協商暫時維持現狀：信任沒有額外變化。"

    if event_type == "campus_vote":
        change = 2 if effects["fairness"] >= 2 else -2
        _update_residents(state, event["group"], change)
        return (
            "投票通過：事件群體滿意度額外 +2。"
            if change > 0
            else "投票未獲足夠支持：事件群體滿意度額外 -2。"
        )

    if event_type == "character_story":
        return "人物主線會記下這次選擇，信任、公平與壓力將影響後續結局。"

    raise ValueError("校園事件玩法類型無效，無法結算特殊規則。")


def _campus_reaction(state, event, development):
    rng = random.Random(f"{state['seed']}:campus-reaction:{state['turn']}")
    event_reaction = rng.choice(CAMPUS_REACTIONS[event["event_type"]])
    development_pun = rng.choice(DEVELOPMENT_PUNS[development["category"]])
    return f"校園匿名板熱帖：{event_reaction} {development_pun}"


def _schedule_delayed_consequence(state, event, action):
    state["pending_consequences"].append({
        "origin_event": event["event"],
        "resident": event["resident"]["name"],
        "description": action["follow_up"],
        "effects": dict(action["delayed_effects"]),
        "due_turn": min(TOTAL_TURNS, state["turn"] + 2),
    })


def _advance_story_arc(state, event, action):
    story_stage = event["story_stage"]
    if not story_stage:
        return None

    story = state["story_arc"]
    if (
        story_stage != story["next_stage"]
        or event["resident"]["id"] != story["resident_id"]
    ):
        raise ValueError("人物故事線順序錯誤，無法結算本次決策。")

    effects = action["effects"]
    relationship = action["resident_effects"]
    support = (
        relationship["trust"]
        - relationship["stress"]
        + effects["fairness"]
    )
    story["support_score"] += support
    story["stage"] = story_stage
    story["next_stage"] = story_stage + 1 if story_stage < 3 else 0

    if story_stage == 1:
        message = (
            f"第 1 幕完成：{story['resident_name']}願意把目標說出口。"
            "校園支線正式開啟，這次不是只在群組回「收到」。"
        )
    elif story_stage == 2:
        message = (
            f"第 2 幕完成：試辦結果讓{story['resident_name']}的目標有了新方向。"
            "進度條終於動了，先別急著截圖慶祝。"
        )
    else:
        resident = event["resident"]
        if story["support_score"] >= 18:
            story["ending"] = "co_created"
            story["ending_text"] = (
                f"{story['resident_name']}與校方一起推進了「{story['goal']}」。"
                "這條支線沒有停在群組的「收到」。"
            )
            resident["satisfaction"] = _bounded(resident["satisfaction"] + 4)
            resident["stress"] = _bounded(resident["stress"] - 3)
            state["metrics"]["problem_improvement"] = _bounded(
                state["metrics"]["problem_improvement"] + 2
            )
            state["metrics"]["fairness"] = _bounded(
                state["metrics"]["fairness"] + 2
            )
        elif story["support_score"] >= 6:
            story["ending"] = "fragile_progress"
            story["ending_text"] = (
                f"{story['resident_name']}的「{story['goal']}」取得有限進展，"
                "仍需要下一任校長接力。"
            )
            resident["satisfaction"] = _bounded(resident["satisfaction"] + 1)
        else:
            story["ending"] = "stalled"
            story["ending_text"] = (
                f"{story['resident_name']}的「{story['goal']}」暫時卡關；"
                "進度進入「待跨單位會議確認」狀態。"
            )
            resident["trust"] = _bounded(resident["trust"] - 2)
            resident["stress"] = _bounded(resident["stress"] + 3)

        message = f"第 3 幕完成：{story['ending_text']}"

    story["last_beat"] = message
    return {
        "stage": story_stage,
        "support_change": support,
        "message": message,
        "ending": story["ending"],
    }


def _settle_delayed_consequences(state, final=False):
    settled = []
    pending = []
    for consequence in state["pending_consequences"]:
        if consequence["due_turn"] > state["turn"] and not final:
            pending.append(consequence)
            continue
        effects = consequence["effects"]
        state["metrics"]["problem_improvement"] = _bounded(
            state["metrics"]["problem_improvement"] + effects["problem_improvement"]
        )
        state["metrics"]["fairness"] = _bounded(
            state["metrics"]["fairness"] + effects["fairness"]
        )
        state["treasury"] = max(
            0, min(2000, state["treasury"] + effects["treasury"])
        )
        settled.append(consequence)
    state["pending_consequences"] = pending
    return settled


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
    event_rule_result = _resolve_event_rule(state, event, action)
    story_update = _advance_story_arc(state, event, action)
    _schedule_delayed_consequence(state, event, action)

    maintenance = sum(state["buildings"].values()) * 4
    revenue = 59 + min(12, state["population"]["students"] // 1000)
    state["treasury"] = max(0, min(2000, state["treasury"] + revenue - 58 - maintenance))
    _refresh_metrics(state)
    state["turn"] += 1
    settled_consequences = _settle_delayed_consequences(
        state, final=state["turn"] >= TOTAL_TURNS
    )
    _refresh_metrics(state)
    year = (state["turn"] - 1) // SEMESTERS_PER_YEAR + 1
    annual_challenge = None
    challenge_reward = 0

    if state["turn"] % SEMESTERS_PER_YEAR == 0:
        satisfaction = state["metrics"]["satisfaction"]
        student_delta = 80 if satisfaction >= 75 else (-80 if satisfaction < 45 else 15)
        state["population"]["students"] = max(0, state["population"]["students"] + student_delta)
        state["population"]["faculty"] = max(0, state["population"]["faculty"] + (12 if satisfaction >= 65 else -8))
        state["population"]["staff"] = max(0, state["population"]["staff"] + (6 if state["resources"]["staffing"] >= 40 else -5))
        challenge = state["challenges"][year - 1]
        challenge["completed"] = _challenge_is_complete(state, challenge)
        annual_challenge = challenge
        if challenge["completed"]:
            challenge_reward = challenge["reward"]
            state["treasury"] = min(2000, state["treasury"] + challenge_reward)
            _refresh_metrics(state)
        state["yearly"].append({
            "year": year,
            "satisfaction": state["metrics"]["satisfaction"],
            "population": sum(state["population"].values()),
            "treasury": state["treasury"],
            "score": calculate_campaign_score(state),
            "challenge": challenge["title"],
            "challenge_completed": challenge["completed"],
            "challenge_reward": challenge_reward,
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

    _award_available_titles(state)
    campus_reaction = _campus_reaction(state, event, development)
    if next_event:
        butterfly = (
            f"{development['title']}使{development['benefit']}；"
            f"{action['cause']}，接續浮現「{next_event['event']}」"
        )
    else:
        butterfly = f"{development['title']}使{development['benefit']}，五年改革進入成果盤點"
    butterfly += f"；選擇後續回響：{action['follow_up']}"
    if story_update:
        butterfly += f"；{story_update['message']}"
    if annual_challenge:
        challenge_status = "完成" if annual_challenge["completed"] else "未完成"
        butterfly += (
            f"；年度挑戰「{annual_challenge['title']}」{challenge_status}"
            + (f"，獲得 {challenge_reward} 點基金獎勵" if challenge_reward else "")
        )
    if settled_consequences:
        settled_summary = "；".join(
            f"「{item['origin_event']}」的後續影響已結算"
            for item in settled_consequences
        )
        butterfly += f"；{settled_summary}"

    outcome = {
        "year": year,
        "semester": (state["turn"] - 1) % SEMESTERS_PER_YEAR + 1,
        "event": event["event"],
        "resident": event["resident"]["name"],
        "role": event["resident"]["role"],
        "resident_trust": event["resident"]["trust"],
        "resident_stress": event["resident"]["stress"],
        "response": action["title"],
        "follow_up": action["follow_up"],
        "delayed_effects": dict(action["delayed_effects"]),
        "story_beat": story_update,
        "event_rule_result": event_rule_result,
        "campus_reaction": campus_reaction,
        "settled_consequences": [
            {
                "origin_event": item["origin_event"],
                "resident": item["resident"],
                "description": item["description"],
                "effects": dict(item["effects"]),
            }
            for item in settled_consequences
        ],
        "development": development["title"],
        "category": development["category"],
        "benefit": development["benefit"],
        "cause": action["cause"],
        "next_event": next_event["event"] if next_event else f"{YEARS}年校務成果已完成",
        "annual_challenge": annual_challenge["title"] if annual_challenge else None,
        "challenge_completed": annual_challenge["completed"] if annual_challenge else None,
        "challenge_reward": challenge_reward,
        "butterfly": butterfly,
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
        "initial_metrics": dict(state["initial_metrics"]),
        "final_metrics": dict(state["metrics"]),
        "metric_labels": {
            "budget_remaining": "財政健康",
            "problem_improvement": "問題改善",
            "satisfaction": "教職員生滿意度",
            "fairness": "公平性",
        },
        "total_score": score,
        "comment": (
            "五年校務兼顧了教職員生需求、財政韌性與長期發展。"
            if score >= 70 else "五年校務仍有改善空間，可優先補足低分指標並維持教職員生參與。"
        ),
        "years": YEARS,
        "campus_profile": state["campus_profile"],
        "story_arc": state["story_arc"],
        "history": state["history"],
        "yearly": state["yearly"],
        "challenges": state["challenges"],
        "titles": state["titles"],
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
