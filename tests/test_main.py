from pathlib import Path
import runpy
from unittest.mock import patch

import jobs.daily_tender_job as daily_tender_job


def test_main_loads_project_env_before_running_daily_job():
    project_root = Path(__file__).resolve().parent.parent
    expected_env = project_root / ".env"

    events = []

    def fake_load_dotenv(
        dotenv_path=None,
        *args,
        **kwargs,
    ):
        if dotenv_path is not None:
            events.append(
                ("load_dotenv", Path(dotenv_path))
            )

        return True

    def fake_run_daily_tender_job():
        events.append(
            ("run_daily_tender_job", None)
        )

        return {
            "meta": {},
            "opportunities": [],
        }

    with patch(
        "dotenv.load_dotenv",
        side_effect=fake_load_dotenv,
    ):
        with patch.object(
            daily_tender_job,
            "run_daily_tender_job",
            side_effect=fake_run_daily_tender_job,
        ):
            runpy.run_path(
                str(project_root / "main.py"),
                run_name="__main__",
            )

    assert events == [
        ("load_dotenv", expected_env),
        ("run_daily_tender_job", None),
    ]
