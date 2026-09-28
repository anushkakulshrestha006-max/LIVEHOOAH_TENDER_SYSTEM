import os
import subprocess
import sys
from pathlib import Path

from config.settings import BASE_DIR


def test_logger_uses_project_relative_log_directory(
    tmp_path,
):
    env = os.environ.copy()

    existing_pythonpath = env.get(
        "PYTHONPATH",
        "",
    )

    env["PYTHONPATH"] = os.pathsep.join(
        part
        for part in (
            str(BASE_DIR),
            existing_pythonpath,
        )
        if part
    )

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from utils.logger import LOG_DIR; "
                "print(LOG_DIR.resolve())"
            ),
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )

    actual_log_dir = Path(
        result.stdout.strip()
    )

    assert actual_log_dir == (
        BASE_DIR / "logs"
    ).resolve()
