from __future__ import annotations

from growth_report.models import ReportCollection, WeeklyGrowthReport


def report_revenue(report: WeeklyGrowthReport) -> float:
    return sum((campaign.revenue or 0) for campaign in report.campaigns)


def report_conversions(report: WeeklyGrowthReport) -> float:
    return sum((campaign.conversions or 0) for campaign in report.campaigns)


def report_roas(report: WeeklyGrowthReport) -> float:
    revenue = report_revenue(report)
    spend = sum((campaign.spend or 0) for campaign in report.campaigns)
    return safe_div(revenue, spend)


def safe_div(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0


def percent_delta(current: float, previous: float) -> float | None:
    if previous == 0:
        return None
    return ((current - previous) / previous) * 100


def priority_count(report: WeeklyGrowthReport) -> str:
    high_priority = sum(1 for item in report.recommendations if item.priority.value == "high")
    return f"{high_priority} alta prioridade" if high_priority else "sem alta prioridade"


def rate_label(report: WeeklyGrowthReport, name: str) -> str:
    aliases = {
        "Revenue Growth": {
            "Revenue Growth",
            "Crescimento de Receita",
            "Crescimento de Receita (Revenue Growth)",
        },
        "Conversions Growth": {
            "Conversions Growth",
            "Crescimento de Conversões",
            "Crescimento de Conversões (Conversions Growth)",
        },
    }
    accepted_names = {accepted_name.lower() for accepted_name in aliases.get(name, {name})}
    for rate in report.rates:
        if rate.name.lower() in accepted_names:
            return f"+{rate.value:.1f}{rate.unit}" if rate.value >= 0 else f"{rate.value:.1f}{rate.unit}"
    return "sem comparativo"


def previous_report(
    report: WeeklyGrowthReport,
    collection: ReportCollection,
) -> WeeklyGrowthReport | None:
    older_reports = [
        item for item in collection.reports
        if item.week_start < report.week_start
    ]
    if not older_reports:
        return None
    return max(older_reports, key=lambda item: item.week_start)


def channel_comparisons(
    report: WeeklyGrowthReport,
    collection: ReportCollection | None = None,
) -> list[dict[str, object]]:
    previous = previous_report(report, collection) if collection else None
    previous_week = (
        f"{previous.week_start:%d/%m/%Y} - {previous.week_end:%d/%m/%Y}"
        if previous
        else None
    )
    previous_by_channel = {
        channel.channel: channel.current_value or 0
        for channel in previous.channels
    } if previous else {}
    total_current = sum((channel.current_value or 0) for channel in report.channels)

    rows: list[dict[str, object]] = []
    for channel in report.channels:
        current = channel.current_value or 0
        previous_value = previous_by_channel.get(channel.channel)
        if previous is None:
            change_pct = None
            status = "sem histórico"
        elif previous_value is None:
            change_pct = None
            status = "canal novo"
        else:
            dynamic_change = percent_delta(current, previous_value)
            change_pct = round_change(dynamic_change) if dynamic_change is not None else None
            status = channel_status_label(change_pct) if change_pct is not None else "sem base"
        share = safe_div(current, total_current) * 100 if total_current else 0
        rows.append(
            {
                "channel": channel.channel,
                "summary": channel.summary,
                "current": current,
                "previous": previous_value,
                "previous_week": previous_week,
                "change_pct": change_pct,
                "share": share,
                "status": status,
            }
        )
    return rows


def channel_status_label(change_pct: float | None) -> str:
    if change_pct is None:
        return "sem histórico"
    if change_pct > 0:
        return "cresceu"
    if change_pct < 0:
        return "caiu"
    return "estável"


def round_change(value: float) -> float:
    offset = 1e-9 if value >= 0 else -1e-9
    return round(value + offset, 1)
