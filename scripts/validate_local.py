"""Reproduce expected outcomes in fresh environments, without cloud credentials."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import venv

ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str], environment: dict[str, str], timeout: int = 180) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=ROOT,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )


def clean_environment() -> dict[str, str]:
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("PYTHON", "PYTEST", "PIP_"))
        and key not in {"VIRTUAL_ENV", "DEMO_SERVICE_ENDPOINT"}
    }
    environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    return environment


def validate_scenario_c_workflow(workflow_text: str) -> None:
    run_lines = [line.strip() for line in workflow_text.splitlines() if line.strip().startswith("run:")]
    expected = "run: .venv/bin/python -I scripts/require_endpoint.py"
    if not run_lines or run_lines[-1] != expected:
        raise ValueError("Scenario C workflow must run the script directly without unsetting DEMO_SERVICE_ENDPOINT")


def validate_scenario(scenario: dict, directory: Path, output: Path, wheelhouse: Path | None) -> dict:
    scenario_id = scenario["id"]
    environment = clean_environment()
    environment_dir = directory / scenario_id
    venv.EnvBuilder(with_pip=True, system_site_packages=False).create(environment_dir)
    python = str(environment_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python"))
    install_command = [
        python, "-I", "-m", "pip", "--isolated", "install",
        "--disable-pip-version-check", "--no-input", "--no-cache-dir",
    ]
    if wheelhouse:
        install_command.extend(["--no-index", "--find-links", str(wheelhouse)])
    install = run([*install_command, "-r", str(ROOT / "requirements.txt")], environment)
    (output / f"{scenario_id}-install.log").write_text(install.stdout, encoding="utf-8")
    if install.returncode:
        raise RuntimeError(f"Scenario {scenario_id}: dependency installation failed; see {output / f'{scenario_id}-install.log'}")

    if scenario_id == "A":
        isolation = run(
            [python, "-I", "-c", "import importlib.util; assert importlib.util.find_spec('yaml') is None"],
            environment,
        )
        if isolation.returncode:
            raise RuntimeError("Scenario A: yaml is unexpectedly available in the isolated environment")

    for key in scenario.get("unset_environment", []):
        environment.pop(key, None)
    command = [python, *scenario["command"][1:]]
    result = run(command, environment, timeout=30)
    (output / f"{scenario_id}.log").write_text(result.stdout, encoding="utf-8")
    missing_signatures = [text for text in scenario["log_signatures"] if text not in result.stdout]
    passed = result.returncode == scenario["expected_exit_code"] and not missing_signatures
    positive_check = None
    if scenario_id == "C":
        environment["DEMO_SERVICE_ENDPOINT"] = "https://demo.invalid"
        fixed = run(command, environment, timeout=30)
        (output / "C-configured.log").write_text(fixed.stdout, encoding="utf-8")
        positive_check = fixed.returncode == 0 and "no network request is made" in fixed.stdout
        passed = passed and positive_check
    print(f"{'PASS' if passed else 'FAIL'} {scenario_id}: exit {result.returncode}, expected {scenario['expected_exit_code']}")
    return {
        "scenario_id": scenario_id,
        "passed": passed,
        "expected_exit_code": scenario["expected_exit_code"],
        "actual_exit_code": result.returncode,
        "missing_log_signatures": missing_signatures,
        "configured_endpoint_check_passed": positive_check,
        "log": f"{scenario_id}.log",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheelhouse", type=Path, help="Install exclusively from a pre-downloaded wheel directory")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/local-validation", help="Directory for logs and report.json")
    arguments = parser.parse_args()
    if sys.version_info[:2] != (3, 12):
        parser.error("Use Python 3.12 to match the GitHub workflows")
    wheelhouse = arguments.wheelhouse.resolve() if arguments.wheelhouse else None
    if wheelhouse is not None and not wheelhouse.is_dir():
        parser.error("--wheelhouse must be an existing directory")
    output = arguments.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    # Invalidate a previous success report before any work that might fail.
    report_path = output / "report.json"
    report = {"schema_version": 1, "scope": "local scenarios; no GitHub or Gemini calls", "passed": False, "scenarios": [], "error": None}
    report["scenario_c_workflow_static_check_passed"] = False
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    try:
        ground_truth = json.loads((ROOT / "ground_truth.json").read_text(encoding="utf-8"))
        scenarios = ground_truth["scenarios"]
        if ground_truth["schema_version"] != 1 or [scenario["id"] for scenario in scenarios] != ["A", "B", "C", "D"]:
            raise ValueError("Expected ground truth schema version 1 and scenarios A, B, C, D")
        validate_scenario_c_workflow((ROOT / scenarios[2]["workflow"]).read_text(encoding="utf-8"))
        report["scenario_c_workflow_static_check_passed"] = True
        print("PASS C workflow: script runs directly without unsetting the variable")
        with tempfile.TemporaryDirectory(prefix="ci-investigator-demo-") as temporary:
            for scenario in scenarios:
                report["scenarios"].append(validate_scenario(scenario, Path(temporary), output, wheelhouse))
        report["passed"] = all(result["passed"] for result in report["scenarios"])
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as error:
        report["error"] = str(error)
        print(f"Validation error: {error}", file=sys.stderr)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Local report: {report_path}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
