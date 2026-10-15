# CI Investigator evaluation repository

Four small GitHub Actions scenarios with known outcomes for evaluating
[CI Investigator](https://github.com/hussenyo12/ci-investigator). This standalone
repository contains only demo code, workflows, and evaluation material. All
workflows require an explicit manual dispatch; pushes and pull requests trigger
nothing.

| Scenario | Workflow | Expected run conclusion | Ground truth |
| --- | --- | --- | --- |
| A | [01-missing-dependency.yml](.github/workflows/01-missing-dependency.yml) | `failure` | `requirements.txt` omits PyYAML; importing `yaml` fails. |
| B | [02-assertion-mismatch.yml](.github/workflows/02-assertion-mismatch.yml) | `failure` | Correct addition returns `4`; the test incorrectly expects `5`. |
| C | [03-missing-env-var.yml](.github/workflows/03-missing-env-var.yml) | `failure` | `DEMO_SERVICE_ENDPOINT` is absent. |
| D | [04-success-control.yml](.github/workflows/04-success-control.yml) | `success` | Four valid arithmetic checks pass; no failure exists. |

The failures are real Python/pytest failures. Workflows do not suppress their exit
codes or use `continue-on-error`. Each independently checks out the repository,
selects Python 3.12 on `ubuntu-latest`, creates a virtual environment without system
packages, and installs the pinned [requirements.txt](requirements.txt). External
pytest plugin discovery is disabled. Action revisions are pinned to verified v6
commits from the official [checkout](https://github.com/actions/checkout) and
[setup-python](https://github.com/actions/setup-python) repositories.

No secrets, API keys, databases, credentials, or service endpoints are needed to
execute the workflows. Ordinary GitHub-hosted Actions access and access to GitHub
and public Python package downloads are sufficient. The demo endpoint script only
checks whether a setting is present; it never makes a network request.

## Validate locally

With Python 3.12 installed, run from the repository root:

```sh
python3.12 scripts/validate_local.py
```

The validator uses the standard library to create a fresh temporary environment
for **each** scenario and install `requirements.txt`. It checks the actual exit
codes and diagnostic text against [ground_truth.json](ground_truth.json), checks
that `yaml` is unavailable in A, and verifies that C succeeds when supplied with
the harmless value `https://demo.invalid`. A static check also verifies that C's
workflow runs the script directly without unsetting its required variable.
The local validator clears that variable before the missing-setting check.
D exercises the same addition function
as B with correct expectations. No GitHub authentication, Google Cloud, Gemini,
or main-application installation is required.

Expected validator output (timing and report path can vary):

```text
PASS C workflow: script runs directly without unsetting the variable
PASS A: exit 2, expected 2
PASS B: exit 1, expected 1
PASS C: exit 1, expected 1
PASS D: exit 0, expected 0
```

The validator exits `0` only if all four outcomes match. A dependency installation
failure is a validation error, not an expected scenario failure. Actual logs and a
machine-readable report are saved in ignored `artifacts/local-validation/`;
temporary virtual environments are removed. This validates scenario behavior,
not GitHub execution, the application's collector, or Gemini diagnosis quality.

For an offline validation after downloading public wheels once:

```sh
python3.12 -m pip download --only-binary=:all: -r requirements.txt -d /tmp/ci-demo-wheels
python3.12 scripts/validate_local.py --wheelhouse /tmp/ci-demo-wheels
```

If you want an ordinary passing pytest run instead:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -I -m pytest -q
```

`pytest.ini` selects only D by default. A and B must be selected explicitly as
shown in their workflows; collecting all of `scenarios/` intentionally fails.
For optional workflow syntax checks with [actionlint](https://github.com/rhysd/actionlint)
installed, run `actionlint .github/workflows/*.yml`.

## Create real workflow runs

The workflow files must first be committed and pushed to this repository's
default branch (`main`) so GitHub exposes manual dispatch. This repository does
not include a script that publishes changes or triggers runs automatically.
Ensure Actions is enabled, then open the repository's **Actions** tab, select a
workflow, choose **Run workflow**, select `main`, and dispatch it. Repeat for all
four workflows. Instructions for manual dispatch are in
[GitHub's documentation](https://docs.github.com/en/actions/managing-workflow-runs-and-deployments/managing-workflow-runs/manually-running-a-workflow).

Alternatively, with an authenticated GitHub CLI account permitted to run Actions:

```sh
gh workflow run 01-missing-dependency.yml --repo hussenyo12/ci-investigator-demo --ref main
gh workflow run 02-assertion-mismatch.yml --repo hussenyo12/ci-investigator-demo --ref main
gh workflow run 03-missing-env-var.yml --repo hussenyo12/ci-investigator-demo --ref main
gh workflow run 04-success-control.yml --repo hussenyo12/ci-investigator-demo --ref main
```

Dispatch does not wait for completion or return the investigation URL. For each
workflow, inspect its recent runs (replace the filename for B, C, and D):

```sh
gh run list --repo hussenyo12/ci-investigator-demo \
  --workflow 01-missing-dependency.yml --event workflow_dispatch --limit 10 \
  --json databaseId,url,headSha,status,conclusion,createdAt
```

Wait until `status` is `completed`, and select the run for the intended commit and
dispatch time. Verify all four use the same repository commit. A, B, and C should
conclude `failure`; D should conclude `success`. Setup/download failures,
cancellations, or timeouts are invalid evaluation samples. Open the failed step
and confirm the expected diagnostic signature from `ground_truth.json` before
evaluating the application.

## Collect and evaluate

Use the `url` field from GitHub as CI Investigator's workflow-run URL input. Do
this for D as well as the failures. The [evaluation guide](docs/evaluation.md)
explains how to save run metadata and logs, evaluate evidence references and
confidence, and record results using
[results-template.json](evaluation/results-template.json).

For B, identifying `actual 4` versus `expected 5` with an explicit evidence
limitation is acceptable. The evaluator knows the test is wrong, but collected
logs and selected configuration may not establish that fact to the model. Do
not require unjustified certainty or penalize a careful request to inspect the
test and implementation. For D, the application should report no failed jobs,
produce no failure hypotheses, and make **zero Gemini calls**.

Keep the deliberately broken baseline intact for comparison. Demonstrate fixes
on a separate branch or commit and record their different commit SHA and run
URLs. In C, configure `DEMO_SERVICE_ENDPOINT` in the workflow or environment;
the existing command honors the configured value.
