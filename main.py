from pathlib import Path

from dotenv import load_dotenv

from jobs.daily_tender_job import run_daily_tender_job


ENV_FILE = (
    Path(__file__).resolve().parent
    / ".env"
)


if __name__ == "__main__":
    load_dotenv(
        dotenv_path=ENV_FILE
    )

    result = run_daily_tender_job()

    print(result)
