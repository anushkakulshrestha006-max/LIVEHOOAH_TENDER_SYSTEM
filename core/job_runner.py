import traceback
from infra.error_handler import safe_fail


class JobRunner:

    def run(self, job_func, *args, **kwargs):

        try:
            return job_func(*args, **kwargs)

        except Exception as e:
            print("❌ JOB CRASH CAUGHT (SAFE MODE ACTIVE)")
            print(traceback.format_exc())

            return safe_fail(str(e))


def dummy_job():
    print("✅ Dummy job executed")
    return {"status": "ok"}


if __name__ == "__main__":

    runner = JobRunner()

    result = runner.run(dummy_job)

    print("\nRESULT:")
    print(result)