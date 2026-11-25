from flask import Flask, jsonify, redirect, render_template, request, session
import os
import secrets

from ai_service import (
    INTERVIEW_QUESTION_COUNT,
    ask_interview_question,
    choose_review_focus,
    generate_campaign_events,
    recommend_plans,
    recommend_campaign_plans,
)
from campus_simulation import (
    RESIDENTS,
    SEMESTERS_PER_YEAR,
    TITLE_CATALOG,
    TOTAL_TURNS,
    YEARS,
    apply_campus_profile,
    advance_campaign,
    campus_profile_for_seed,
    campaign_context,
    make_campaign_record,
    new_campaign,
    next_story_arc_context,
    resident_profiles,
    story_arc_for_seed,
    validate_campaign_choice,
)
from simulation import apply_effects, calculate_total_score, make_comment
from storage import load_menu, load_records, save_record


app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "development-only-key")
app.config["JSON_AS_ASCII"] = False


GAMES = {}


def _new_game(proposal):
    flow_id = secrets.token_urlsafe(16)
    menu = load_menu()
    GAMES[flow_id] = {
        "proposal": proposal.strip(),
        "answers": [],
        "menu": menu,
        "metrics": dict(menu["initial_metrics"]),
        "plans": None,
        "selected_plan": None,
        "round_index": 0,
        "round_choices": [],
        "scenario_title": "",
        "failure": None,
    }
    session["flow_id"] = flow_id
    return GAMES[flow_id]


def _get_game():
    flow_id = session.get("flow_id")
    if not flow_id:
        return None
    return GAMES.get(flow_id)


def _round_context(game):
    round_index = game["round_index"]
    rounds = game["plans"]["rounds"]
    return {
        "round_data": rounds[round_index],
        "round_number": round_index + 1,
        "round_count": len(rounds),
        "metrics": game["metrics"],
        "metric_changes": game.get("last_metric_changes", {}),
        "metric_labels": game["menu"]["metric_labels"],
        "selected_plan": game["selected_plan"],
        "decision_history": game["round_choices"],
    }


def _fallback_review_focus(record):
    metrics = record["final_metrics"]
    lowest = min(metrics, key=lambda name: (metrics[name], name))
    actions = record.get("actions", [])
    action_index = 0 if actions else -1
    return {"focus_metric": lowest, "action_index": action_index}


def _make_review_text(record, focus):
    focus_metric = focus["focus_metric"]
    action_index = focus["action_index"]
    actions = record["actions"]

    plan_name = record["plan_title"]
    metric_label = record["metric_labels"].get(focus_metric, focus_metric)
    metric_value = record["final_metrics"][focus_metric]
    action = actions[action_index] if 0 <= action_index < len(actions) else actions[0]
    action_text = action["action_text"]
    event = action["event"]

    return (
        f"本次採用「{plan_name}」。在「{event}」中，"
        f"玩家選擇了「{action_text}」；完成模擬後，"
        f"{metric_label}為 {metric_value}，總分為 {record['total_score']} 分。"
    )


def show_result(record):
    save_record(record)
    session["recent_record_id"] = record["record_id"]
    return redirect("/result")


@app.context_processor
def inject_demo_mode():
    return {
        "demo_mode": os.environ.get("DEMO_MODE") == "1",
        "recent_record_id": session.get("recent_record_id"),
    }


@app.errorhandler(ValueError)
def handle_value_error(error):
    return render_template("error.html", title="資料格式錯誤", message=str(error)), 400


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/characters")
def characters():
    return render_template("characters.html", characters=RESIDENTS)


@app.route("/interview/start", methods=["POST"])
def interview_start():
    proposal = request.form.get("proposal", "").strip()
    if len(proposal) < 1 or len(proposal) > 300:
        return render_template(
            "error.html",
            title="提案格式錯誤",
            message="提案長度需為 1 到 300 個字。",
        ), 400

    try:
        game = _new_game(proposal)
    except ValueError as error:
        return render_template(
            "error.html", title="無法開始任務", message=str(error)
        ), 400

    game["failure"] = "interview"
    try:
        question = ask_interview_question(proposal, [])
        game["current_question"] = question
        game["failure"] = None
        return redirect("/interview")
    except ValueError as error:
        return render_template(
            "error.html",
            title="訪談格式錯誤",
            message=str(error),
            retry=True,
        ), 400
    except Exception as error:
        return render_template("error.html", title="無法取得訪談", message=str(error), retry=True), 503


@app.route("/interview")
def interview():
    game = _get_game()
    if not game or "current_question" not in game:
        return redirect("/")
    return render_template(
        "interview.html",
        proposal=game["proposal"],
        question=game["current_question"],
        question_number=len(game["answers"]) + 1,
        question_count=INTERVIEW_QUESTION_COUNT,
    )


@app.route("/interview/answer", methods=["POST"])
def interview_answer():
    game = _get_game()
    if not game:
        return redirect("/")

    answer = request.form.get("answer", "").strip()
    question = game.get("current_question", {})
    options = question.get("options", [])
    if not answer or answer not in options:
        return render_template(
            "error.html",
            title="回答格式錯誤",
            message="請從目前題目的選項中選擇一個回答。",
        ), 400

    game["answers"].append(answer)
    if len(game["answers"]) < INTERVIEW_QUESTION_COUNT:
        try:
            game["current_question"] = ask_interview_question(
                game["proposal"], game["answers"]
            )
            return redirect("/interview")
        except ValueError as error:
            game["failure"] = "interview"
            return render_template("error.html", title="訪談格式錯誤", message=str(error), retry=True), 400
        except Exception as error:
            game["failure"] = "interview"
            return render_template("error.html", title="無法取得訪談", message=str(error), retry=True), 503

    try:
        data = recommend_plans(
            game["proposal"], game["answers"], game["menu"]
        )
        if not data["supported"]:
            return render_template(
                "error.html",
                title="目前不支援此提案",
                message="AI 判斷這不是明確的校園問題，因此無法產生方案。",
            ), 400
        game["plans"] = data
        game["scenario_title"] = data["scenario_title"]
        return redirect("/plans")
    except ValueError as error:
        game["failure"] = "plans"
        return render_template("error.html", title="方案格式錯誤", message=str(error), retry=True), 400
    except Exception as error:
        game["failure"] = "plans"
        return render_template("error.html", title="無法產生方案", message=str(error), retry=True), 503


@app.route("/interview/retry", methods=["POST"])
def interview_retry():
    game = _get_game()
    if not game:
        return redirect("/")

    if game.get("failure") == "interview":
        try:
            game["current_question"] = ask_interview_question(
                game["proposal"], game["answers"]
            )
            game["failure"] = None
            return redirect("/interview")
        except Exception as error:
            return render_template("error.html", title="重試失敗", message=str(error), retry=True), 503

    try:
        data = recommend_plans(game["proposal"], game["answers"], game["menu"])
        if not data["supported"]:
            return render_template(
                "error.html",
                title="目前不支援此提案",
                message="AI 判斷這不是明確的校園問題。",
            ), 400
        game["plans"] = data
        game["scenario_title"] = data["scenario_title"]
        game["failure"] = None
        return redirect("/plans")
    except Exception as error:
        return render_template("error.html", title="重試失敗", message=str(error), retry=True), 503


@app.route("/plans")
def plans():
    game = _get_game()
    if not game or not game.get("plans"):
        return redirect("/")
    return render_template(
        "plans.html",
        scenario_title=game["scenario_title"],
        recommendations=game["plans"]["recommendations"],
        answer_count=len(game["answers"]),
    )


@app.route("/simulation/start", methods=["POST"])
def simulation_start():
    game = _get_game()
    if not game or not game.get("plans"):
        return redirect("/")
    plan_id = request.form.get("plan_id")
    plan = next(
        (item for item in game["plans"]["recommendations"] if item["plan_id"] == plan_id),
        None,
    )
    if not plan:
        return render_template("error.html", title="方案格式錯誤", message="請選擇一個有效方案。"), 400

    game["selected_plan"] = plan
    game["metrics"] = dict(game["menu"]["initial_metrics"])
    game["metrics"] = apply_effects(game["metrics"], plan["effects"])
    game["round_index"] = 0
    game["round_choices"] = []
    game["last_metric_changes"] = {}
    return redirect("/simulation")


@app.route("/simulation")
def simulation():
    game = _get_game()
    if not game or not game.get("selected_plan"):
        return redirect("/")
    if game["round_index"] >= len(game["plans"]["rounds"]):
        return redirect("/result")
    return render_template("round.html", **_round_context(game))


@app.route("/simulation/choose", methods=["POST"])
def simulation_choose():
    game = _get_game()
    if not game or not game.get("selected_plan"):
        return redirect("/")

    round_index = game["round_index"]
    round_data = game["plans"]["rounds"][round_index]
    action_id = request.form.get("action_id")
    action = next(
        (item for item in round_data["actions"] if item["action_id"] == action_id),
        None,
    )
    if not action:
        return render_template("error.html", title="行動格式錯誤", message="請選擇一個有效行動。"), 400

    previous_metrics = game["metrics"]
    game["metrics"] = apply_effects(previous_metrics, action["effects"])
    game["last_metric_changes"] = {
        name: game["metrics"][name] - previous_metrics[name]
        for name in game["metrics"]
    }
    action_index = round_data["actions"].index(action)
    game["round_choices"].append({
        "round": round_index + 1,
        "event": round_data["event"],
        "action_index": action_index,
        "action_id": action["action_id"],
        "action_text": action["text"],
        "action_effects": dict(action["effects"]),
    })
    game["round_index"] += 1

    if game["round_index"] < len(game["plans"]["rounds"]):
        if request.headers.get("X-Game-Update") == "1":
            return render_template("_round_update.html", **_round_context(game))
        return redirect("/simulation")

    plan = game["selected_plan"]
    record = {
        "record_id": secrets.token_hex(16),
        "created_at": _utc_now(),
        "scenario_id": "campus_custom",
        "scenario_title": game["scenario_title"],
        "proposal": game["proposal"],
        "plan_id": plan["plan_id"],
        "plan_title": plan["title"],
        "plan_strategy": plan["strategy"],
        "plan_description": plan["description"],
        "plan_reason": plan["reason"],
        "plan_effects": dict(plan["effects"]),
        "initial_metrics": dict(game["menu"]["initial_metrics"]),
        "final_metrics": dict(game["metrics"]),
        "metric_labels": dict(game["menu"]["metric_labels"]),
        "actions": game["round_choices"],
        "total_score": calculate_total_score(game["metrics"]),
    }
    record["comment"] = make_comment(record["total_score"])

    try:
        focus = choose_review_focus(record)
        review_source = "gemini"
    except Exception:
        focus = _fallback_review_focus(record)
        review_source = "local"

    try:
        record["review"] = _make_review_text(record, focus)
    except Exception:
        focus = _fallback_review_focus(record)
        record["review"] = _make_review_text(record, focus)
        review_source = "local"

    if review_source == "gemini":
        record["review_note"] = "回顧焦點由 AI 選擇，回顧文字由本機已存紀錄整理。"
    else:
        record["review_note"] = "回顧採用本機整理的提示；AI 回顧失敗或欄位無效。"

    session["recent_record_id"] = record["record_id"]
    session["flow_id"] = session.get("flow_id")
    GAMES[session["flow_id"]]["result"] = record
    return show_result(record)


@app.route("/result")
def result():
    game = _get_game()
    record = game.get("result") if game else None
    if not record:
        record_id = session.get("recent_record_id")
        records = load_records()
        record = next((item for item in records if item.get("record_id") == record_id), None)
    if not record:
        return redirect("/")
    return render_template("result.html", record=record)


@app.route("/records")
def records():
    return render_template("records.html", records=load_records())


@app.route("/titles")
def titles():
    earned_by_id = {}
    for record in load_records():
        if not isinstance(record, dict) or record.get("scenario_id") != "campus_decade":
            continue
        record_titles = record.get("titles", [])
        if not isinstance(record_titles, list):
            continue
        for title in record_titles:
            if isinstance(title, dict) and isinstance(title.get("id"), str):
                earned_by_id.setdefault(title["id"], []).append(title)

    collection = []
    for title in TITLE_CATALOG:
        collection.append({
            "id": title["id"],
            "name": title["name"],
            "description": title["description"],
            "unlocked": title["id"] in earned_by_id,
            "earned_runs": len(earned_by_id.get(title["id"], [])),
        })
    return render_template(
        "titles.html",
        titles=collection,
        unlocked_count=sum(title["unlocked"] for title in collection),
    )


@app.route("/leaderboard")
def leaderboard():
    candidates = []
    for record in load_records():
        if (
            not isinstance(record, dict)
            or record.get("scenario_id") != "campus_decade"
            or record.get("years") != YEARS
            or isinstance(record.get("total_score"), bool)
            or not isinstance(record.get("total_score"), int)
        ):
            continue
        created_at = record.get("created_at")
        candidates.append({
            "plan_title": record.get("plan_title") if isinstance(record.get("plan_title"), str) else "校務經營",
            "total_score": record["total_score"],
            "date": created_at[:10] if isinstance(created_at, str) else "",
            "created_at": created_at if isinstance(created_at, str) else "",
        })
    candidates.sort(
        key=lambda record: (record["total_score"], record["created_at"]),
        reverse=True,
    )
    return render_template("leaderboard.html", records=candidates[:10])


@app.route("/records/<record_id>")
def record_detail(record_id):
    record = next(
        (item for item in load_records() if item.get("record_id") == record_id),
        None,
    )
    if not record:
        return render_template("error.html", title="找不到紀錄", message="此紀錄沒有新格式識別碼或已不存在。"), 404
    if record.get("scenario_id") == "campus_decade":
        return render_template("campus_result.html", record=record)
    return render_template("result.html", record=record)


@app.route("/reset", methods=["POST"])
def reset():
    flow_id = session.pop("flow_id", None)
    if flow_id:
        GAMES.pop(flow_id, None)
    session.pop("recent_record_id", None)
    return redirect("/")


@app.route("/campus/start", methods=["POST"])
def campus_start():
    proposal = request.form.get("proposal", "").strip()
    if not proposal or len(proposal) > 300:
        return render_template(
            "error.html",
            title="校園議題格式錯誤",
            message="請輸入 1 到 300 個字的校園問題。",
        ), 400

    flow_id = secrets.token_urlsafe(16)
    campaign_seed = secrets.randbits(64)
    game = {
        "proposal": proposal,
        "campaign_seed": campaign_seed,
        "story_arc": story_arc_for_seed(campaign_seed),
        "campaign": None,
        "failure": "campaign_start",
    }
    GAMES[flow_id] = game
    session["flow_id"] = flow_id
    session.pop("recent_record_id", None)
    try:
        if not _prepare_campaign_start(game):
            return render_template(
                "error.html",
                title="目前不支援此提案",
                message="請描述與校園生活、設施、服務或制度相關的問題。",
            ), 400
    except ValueError as error:
        return render_template(
            "error.html",
            title="AI 方案或事件格式錯誤",
            message=str(error),
            retry=True,
            retry_url="/campus/retry-start",
        ), 503
    except Exception as error:
        return render_template(
            "error.html",
            title="無法分析校園問題",
            message=str(error),
            retry=True,
            retry_url="/campus/retry-start",
        ), 503
    return redirect("/campus/plans")


def _prepare_campaign_start(game):
    menu = load_menu()
    plans = game.get("campaign_plans")
    if not plans:
        plans = recommend_campaign_plans(game["proposal"], menu)
        if not plans["supported"]:
            return False
        game["campaign_plans"] = plans
    game["campus_profile"] = campus_profile_for_seed(game["campaign_seed"])
    initial_state = {
        "year": 1,
        "semester": 1,
        "metrics": dict(menu["initial_metrics"]),
        "treasury": 850,
        "population": {"students": 9000, "faculty": 720, "staff": 380},
        "resources": {"energy": 68, "water": 72, "staffing": 64},
        "buildings": {"library": 0, "housing": 0, "wellbeing": 0},
        "policies": {},
        "characters": resident_profiles(),
        "campus_profile": game["campus_profile"],
        "story_arc": game["story_arc"],
    }
    apply_campus_profile(initial_state, game["campus_profile"])
    events = generate_campaign_events(
        game["proposal"],
        [],
        initial_state,
        opening=True,
    )
    game["campaign_events"] = events
    game["failure"] = None
    return True


@app.route("/campus/retry-start", methods=["POST"])
def campus_retry_start():
    game = _get_game()
    if not game or game.get("failure") != "campaign_start":
        return redirect("/")
    try:
        if not _prepare_campaign_start(game):
            return render_template(
                "error.html",
                title="目前不支援此提案",
                message="請描述與校園生活、設施、服務或制度相關的問題。",
            ), 400
    except Exception as error:
        return render_template(
            "error.html",
            title="重試分析失敗",
            message=str(error),
            retry=True,
            retry_url="/campus/retry-start",
        ), 503
    return redirect("/campus/plans")


@app.route("/campus/plans")
def campus_plans():
    game = _get_game()
    if not game or not game.get("campaign_plans"):
        return redirect("/")
    return render_template(
        "campus_plans.html",
        proposal=game["proposal"],
        scenario_title=game["campaign_plans"]["scenario_title"],
        recommendations=game["campaign_plans"]["recommendations"],
        event_count=len(game["campaign_events"]),
        campus_profile=game["campus_profile"],
        story_arc=game["story_arc"],
    )


@app.route("/campus/plan", methods=["POST"])
def campus_plan():
    game = _get_game()
    if not game or not game.get("campaign_plans"):
        return redirect("/")
    if game.get("campaign"):
        return redirect("/campus")
    plan_id = request.form.get("plan_id")
    plan = next(
        (
            item for item in game["campaign_plans"]["recommendations"]
            if item["plan_id"] == plan_id
        ),
        None,
    )
    if not plan:
        return render_template(
            "error.html", title="方案格式錯誤", message="請選擇一個有效的 AI 方案。"
        ), 400
    game["campaign"] = new_campaign(
        game["proposal"],
        game["campaign_events"],
        plan,
        game["campaign_plans"]["scenario_title"],
        seed=game["campaign_seed"],
        campus_profile_id=game["campus_profile"]["id"],
    )
    return redirect("/campus")


@app.route("/campus")
def campus():
    game = _get_game()
    campaign = game.get("campaign") if game else None
    if not campaign:
        return redirect("/")
    if campaign["finished"]:
        return redirect("/campus/result")
    return render_template("campus.html", **campaign_context(campaign))


@app.route("/campus/choose", methods=["POST"])
def campus_choose():
    game = _get_game()
    campaign = game.get("campaign") if game else None
    if not campaign:
        return redirect("/")

    return _process_campaign_decision(
        game,
        request.form.get("action_id", ""),
        request.form.get("development_id", ""),
    )


def _process_campaign_decision(game, action_id, development_id):
    campaign = game["campaign"]
    try:
        action, development = validate_campaign_choice(
            campaign, action_id, development_id
        )
    except ValueError as error:
        return render_template(
            "error.html", title="經營決策格式錯誤", message=str(error)
        ), 400

    next_events = None
    if not campaign["event_queue"] and campaign["turn"] + 1 < TOTAL_TURNS:
        game["pending_decision"] = {
            "action_id": action_id,
            "development_id": development_id,
        }
        try:
            next_events = generate_campaign_events(
                game["proposal"],
                campaign["history"],
                {
                    "year": campaign["turn"] // SEMESTERS_PER_YEAR + 1,
                    "semester": campaign["turn"] % SEMESTERS_PER_YEAR + 1,
                    "metrics": dict(campaign["metrics"]),
                    "treasury": campaign["treasury"],
                    "population": dict(campaign["population"]),
                    "resources": dict(campaign["resources"]),
                    "buildings": dict(campaign["buildings"]),
                    "policies": dict(campaign["policies"]),
                    "characters": resident_profiles(campaign["residents"]),
                    "campus_profile": campaign["campus_profile"],
                    "story_arc": next_story_arc_context(campaign, action),
                    "pending_consequences": [
                        {
                            "turns_left": max(
                                0, item["due_turn"] - campaign["turn"]
                            ),
                            "resident": item["resident"],
                            "description": item["description"],
                            "effects": dict(item["effects"]),
                        }
                        for item in campaign["pending_consequences"]
                    ],
                    "current_challenge": campaign["challenges"][
                        campaign["turn"] // SEMESTERS_PER_YEAR
                    ],
                    "completed_challenge_count": sum(
                        item["completed"] for item in campaign["challenges"]
                    ),
                    "titles": list(campaign["titles"]),
                },
                next_decision={
                    "current_issue": campaign["current_event"]["event"],
                    "response": action["title"],
                    "management_measure": development["title"],
                    "follow_up": action["follow_up"],
                    "delayed_effects": dict(action["delayed_effects"]),
                    "relationship_effects": dict(action["resident_effects"]),
                    "immediate_effects": dict(action["effects"]),
                },
            )
        except Exception as error:
            return render_template(
                "error.html",
                title="無法產生下一批校園事件",
                message=str(error),
                retry=True,
                retry_url="/campus/retry-choice",
            ), 503

    try:
        advance_campaign(campaign, action_id, development_id, next_events)
    except ValueError as error:
        return render_template(
            "error.html", title="經營決策格式錯誤", message=str(error)
        ), 400
    game.pop("pending_decision", None)

    if campaign["finished"]:
        record = make_campaign_record(campaign)
        game["result"] = record
        save_record(record)
        session["recent_record_id"] = record["record_id"]
        return redirect("/campus/result")
    return redirect("/campus")


@app.route("/campus/retry-choice", methods=["POST"])
def campus_retry_choice():
    game = _get_game()
    pending = game.get("pending_decision") if game else None
    if not game or not pending:
        return redirect("/campus")
    return _process_campaign_decision(
        game,
        pending["action_id"],
        pending["development_id"],
    )


@app.route("/campus/result")
def campus_result():
    game = _get_game()
    record = game.get("result") if game else None
    if not record:
        record_id = session.get("recent_record_id")
        record = next(
            (
                item for item in load_records()
                if item.get("record_id") == record_id
                and item.get("scenario_id") == "campus_decade"
            ),
            None,
        )
    if not record:
        return redirect("/")
    return render_template("campus_result.html", record=record)


def _utc_now():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    app.run(debug=True)