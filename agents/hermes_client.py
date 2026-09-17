import subprocess
import json


class HermesClient:
    """
    Bridge between Python (Windows) and Hermes CLI (WSL)
    """

    def run(self, prompt: str) -> str:
        """
        Runs Hermes in WSL and returns raw text output
        """

        cmd = [
            "wsl",
            "bash",
            "-lc",
            f'hermes -z "{prompt}"'
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise Exception(result.stderr.strip())

        return result.stdout.strip()

    def run_json(self, prompt: str) -> dict:
        """
        Forces Hermes to return JSON and parses it into Python dict
        """

        cmd = [
            "wsl",
            "bash",
            "-lc",
            f'hermes -z \'Return ONLY valid JSON: {prompt}\''
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise Exception(result.stderr.strip())

        output = result.stdout.strip()

        # Parse JSON safely
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            raise Exception(f"Invalid JSON returned by Hermes:\n{output}")