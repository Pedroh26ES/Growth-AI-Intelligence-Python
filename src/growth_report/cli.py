from __future__ import annotations

from pathlib import Path

import typer
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from rich.console import Console

from growth_report.config import load_config
from growth_report.pipeline import run_pipeline

app = typer.Typer(help="Growth AI Intelligence automation.")
console = Console()


@app.command()
def run(
    config: Path = typer.Option(Path("config.example.toml"), help="Path to TOML config."),
    dry_run: bool = typer.Option(False, help="Run without calling OpenAI."),
) -> None:
    app_config = load_config(config)
    report = run_pipeline(app_config, dry_run=dry_run)
    console.print(f"[green]Report saved:[/green] {report.report_id}")


@app.command()
def schedule(
    config: Path = typer.Option(Path("config.example.toml"), help="Path to TOML config."),
    dry_run: bool = typer.Option(False, help="Run scheduled jobs without calling OpenAI."),
) -> None:
    app_config = load_config(config)
    scheduler_config = app_config.scheduler
    scheduler = BlockingScheduler(timezone=scheduler_config.timezone)

    def job() -> None:
        report = run_pipeline(app_config, dry_run=dry_run)
        console.print(f"[green]Scheduled report saved:[/green] {report.report_id}")

    scheduler.add_job(
        job,
        CronTrigger(
            day_of_week=scheduler_config.day_of_week,
            hour=scheduler_config.hour,
            minute=scheduler_config.minute,
            timezone=scheduler_config.timezone,
        ),
        id="weekly_growth_report",
        replace_existing=True,
    )

    console.print(
        "[cyan]Scheduler started[/cyan] "
        f"({scheduler_config.day_of_week} {scheduler_config.hour:02d}:"
        f"{scheduler_config.minute:02d} {scheduler_config.timezone})."
    )
    scheduler.start()


if __name__ == "__main__":
    app()
