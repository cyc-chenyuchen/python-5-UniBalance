METRIC_NAMES = (
    "budget_remaining",
    "problem_improvement",
    "satisfaction",
    "fairness",
)


def apply_effects(metrics, effects):
    updated = dict(metrics)
    for name in METRIC_NAMES:
        updated[name] = max(0, min(100, updated[name] + effects[name]))
    return updated


def run_round_choice(metrics, action_effects):
    return apply_effects(metrics, action_effects)


def calculate_total_score(final_metrics):
    values = [final_metrics[name] for name in METRIC_NAMES]
    average = sum(values) / len(values)
    return int(average + 0.5)


def make_comment(total_score):
    if total_score >= 80:
        return "整體模擬表現佳，方案兼顧了多項校園需求，但仍需注意資源與公平性的取捨。"
    if total_score >= 60:
        return "整體模擬表現中等，方案有一定效果，也暴露出資源、滿意度或公平性的權衡。"
    return "整體模擬表現較弱，需重新檢視資源分配、問題改善與不同成員的公平性。"
