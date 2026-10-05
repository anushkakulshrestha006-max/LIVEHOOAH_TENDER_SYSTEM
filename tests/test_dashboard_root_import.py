import subprocess
import sys
from pathlib import Path


def test_dashboard_entrypoint_context_can_import_sheets():
    project_root = Path(__file__).resolve().parents[1]
    dashboard_dir = project_root / "dashboard"

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from pathlib import Path; "
                "import sys; "
                "PROJECT_ROOT = Path.cwd().parents[0]; "
                "sys.path.insert(0, str(PROJECT_ROOT)); "
                "from sheets.sheets_client import SheetsClient; "
                "print('IMPORT_OK')"
            ),
        ],
        cwd=dashboard_dir,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "IMPORT_OK" in result.stdout
