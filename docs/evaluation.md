# Evaluating CI Investigator

## Establish the known outcomes

[ground_truth.json](../ground_truth.json) is the evaluator's machine-readable
reference (schema version 1). Each scenario records its workflow and job ID,
expected GitHub conclusion, local command and exit code, diagnostic signatures,
true cause, corrective action, and evidence limits. `null` cause/action in D means
no failure exists. Its `evaluation` object describes required behavior and
unsupported claims; these are semantic criteria, not exact model-output strings.

Run the local validator before creating GitHub runs. Then dispatch the four
workflows using the README. Use runs from one baseline commit. Confirm the
expected failed step and signature rather than accepting any red workflow as a
valid sample. For example, failing to download pytest is not Scenario A.

Keep ground truth and evaluator-only source inspection out of the application's
input. Give the application only its normal workflow-run URL input and let its
existing collector select evidence. Do not paste this README, test source, or
expected answers into the Gemini prompt. Record the actual evidence files and
excerpts selected by the collector so claims can be checked against that input.

## Save the actual runs

The following commands require an authenticated `gh` session with read access.
They collect an existing run; they do not dispatch or modify it. From the repository
root, replace the placeholder with the numeric run ID selected from `gh run list`:

```sh
DEMO_RUN_ID=REPLACE_WITH_NUMERIC_RUN_ID
mkdir -p "artifacts/runs/$DEMO_RUN_ID"
gh run view "$DEMO_RUN_ID" --repo hussenyo12/ci-investigator-demo \
  --json databaseId,url,attempt,headSha,event,workflowName,status,conclusion,jobs,createdAt \
  > "artifacts/runs/$DEMO_RUN_ID/metadata.json"
gh run view "$DEMO_RUN_ID" --repo hussenyo12/ci-investigator-demo --log \
  > "artifacts/runs/$DEMO_RUN_ID/jobs.log"
```

Repeat for each of A–D. Collect logs promptly before GitHub retention removes
them. Record the run attempt; a rerun can share a run ID. Avoid rerunning while
collecting or investigating a sample. To collect a specific historical attempt,
pass `--attempt NUMBER` to both view commands and give it a distinct artifact
directory. Confirm that CI Investigator is also collecting that same attempt;
if it only supports the current attempt, use fresh run IDs instead.

The URL has the form
`https://github.com/hussenyo12/ci-investigator-demo/actions/runs/RUN_ID`.
Do not invent run URLs or substitute local logs for a real GitHub run. This
repository intentionally ships no claimed remote results.

## Run the existing application

Use CI Investigator's documented interface in its separate repository, configured
as usual for GitHub collection and Gemini 2.5 Flash through Vertex AI. Pass each
real run URL to it. This repository does not alter the main application's CLI,
credentials, model configuration, or source. Cloud credentials are required only
for real application evaluation, not for demo workflows or local validation.

Copy `evaluation/results-template.json` to an ignored artifact path, for example:

```sh
mkdir -p artifacts/evaluation
cp evaluation/results-template.json artifacts/evaluation/results.json
```

For each scenario, retain the report, sanitized evidence, cited source identifiers
and ranges, and observable model-call count. Also record the application commit,
model ID, run URL, run attempt, workflow commit, observed GitHub conclusion, and
evaluation time. Do not save credentials in evaluation results. `null` in the
template means unmeasured; it must not be treated as a passing check or zero.

## Score each diagnosis against available evidence

Record each criterion as `true`, `false`, or `null` (unobserved), with notes. Set
`verdict` to `pass`, `fail`, or `inconclusive` only after reviewing evidence. There
are no fixed required confidence scores; confidence must reflect the evidence.

| Scenario | Acceptable finding and next step | Evaluation boundary |
| --- | --- | --- |
| A | Identify missing module `yaml`, associate it with PyYAML, and recommend declaring/installing it in the test environment. | Attribute omission from `requirements.txt` only if the collected configuration supports that claim. Do not blame a network outage or suggest changing the import to `PyYAML`. |
| B | Identify the assertion mismatch: actual `4`, expected `5`. Recommend reviewing intended behavior, the expectation, and implementation. | The evaluator's source confirms correct addition and the wrong test. Logs can expose an assertion without establishing the specification. Accept a cautious diagnosis that cannot decide which side to change. Do not demand a high-confidence test-bug diagnosis. |
| C | Identify absent `DEMO_SERVICE_ENDPOINT` and recommend defining this non-sensitive setting in the workflow/environment. | Configuring the variable is sufficient; the workflow command honors it. Only the local validator clears it before the missing-setting check. No endpoint was contacted. Network outages, authentication failures, and a requirement for a secret are unsupported. |
| D | Report no failed jobs, give no failure hypotheses, and make zero Gemini calls. | A passing run must not be diagnosed as a failure. A correct-looking report alone does not establish that no model call occurred. |

For every report:

1. **Outcome:** Did the application collect the intended run/attempt and recognize
   whether it has failed jobs?
2. **Diagnosis:** Does the identified failure mechanism agree with observable
   evidence and the scenario criteria above?
3. **Evidence:** Do cited IDs and ranges resolve to actual collected evidence,
   and do those excerpts support the associated claims? A valid citation alone
   does not make an unsupported conclusion correct.
4. **Action:** Would the recommendation address the demonstrated problem, with
   appropriate uncertainty where intended behavior is unknown?
5. **Calibration:** Does the report describe missing evidence and avoid claims
   of source inspection or certainty unsupported by the input?
6. **Control abstention:** For D, check zero failed jobs, zero hypotheses, and
   zero Gemini calls separately using application logs, tracing, or a call
   counter already exposed by the application. If the call count cannot be
   observed, leave that criterion unmeasured and the verdict inconclusive.

Score D as a failure if any Gemini call occurs or a failure is fabricated. For
A–C, a pass requires the applicable criteria to be observed and satisfied. A
setup failure or incomplete collection is an invalid/inconclusive sample, not
proof of a diagnosis defect. Record that limitation and obtain a valid sample.
Never promote a local validator pass into a claim of application accuracy.

## Present the demonstration

Show the baseline commit, the three genuine GitHub failures, and the successful
control. Pair each run's real diagnostic line with the application's cited
evidence and recommendation. Highlight B's distinction between known source-level
truth and what the model could infer from its collected input. Finish by showing
D's abstention and measured model-call count. Report pass/fail/inconclusive counts
separately and retain raw results; four small examples demonstrate behavior but
do not establish general accuracy.
