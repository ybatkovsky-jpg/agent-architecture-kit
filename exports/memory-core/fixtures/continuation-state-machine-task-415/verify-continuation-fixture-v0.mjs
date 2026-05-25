#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const fixturePath = path.join(__dirname, 'fixture.json');
const outputPath = process.argv[2] || path.join(__dirname, 'verifier-report-v0.json');

const fixture = JSON.parse(fs.readFileSync(fixturePath, 'utf8'));

const allowedStates = new Set(fixture.states);
const allowedTransitions = new Set(
  fixture.allowed_transitions.map(([from, to]) => `${from}->${to}`),
);
const requiredFieldsByState = fixture.required_fields_by_state;
const specialRules = fixture.special_rules || {};

function hasAllFields(payload, requiredFields) {
  const missing = [];
  for (const field of requiredFields) {
    if (!(field in payload)) missing.push(field);
  }
  return missing;
}

function verifyValidCase(testCase) {
  const errors = [];
  const observations = [];
  const states = testCase.path;
  const steps = testCase.steps || [];

  if (steps.length !== states.length) {
    errors.push({ code: 'step_count_mismatch', detail: `path has ${states.length} states but steps has ${steps.length}` });
    return { ok: false, errors, observations };
  }

  for (let i = 0; i < states.length; i += 1) {
    const expectedState = states[i];
    const step = steps[i];
    if (step.state !== expectedState) {
      errors.push({ code: 'state_step_mismatch', detail: `path[${i}] expected ${expectedState} but got ${step.state}` });
    }
    if (!allowedStates.has(step.state)) {
      errors.push({ code: 'unknown_state', detail: step.state });
    }
    const payload = step.payload || {};
    const missingFields = hasAllFields(payload, requiredFieldsByState[step.state] || []);
    if (missingFields.length > 0) {
      errors.push({ code: 'missing_required_fields', state: step.state, missing: missingFields });
    }
    if ('status' in payload && payload.status !== step.state) {
      errors.push({ code: 'status_state_mismatch', state: step.state, status: payload.status });
    }
  }

  for (let i = 0; i < states.length - 1; i += 1) {
    const key = `${states[i]}->${states[i + 1]}`;
    if (!allowedTransitions.has(key)) {
      errors.push({ code: 'transition_not_allowed', transition: key });
    }
  }

  const preparedStep = steps.find((step) => step.state === 'PREPARED');
  const handoffId = preparedStep?.payload?.handoff_id;
  if (handoffId) {
    for (const step of steps) {
      const stepHandoffId = step.payload?.handoff_id;
      if (stepHandoffId !== handoffId) {
        errors.push({ code: 'handoff_id_not_stable', state: step.state, expected: handoffId, actual: stepHandoffId });
      }
    }
  } else {
    errors.push({ code: 'prepared_handoff_missing_for_stability_check' });
  }

  const ackStep = steps.find((step) => step.state === 'ACK');
  const continuationStates = new Set(['ACK', 'RUNNING', 'DONE', 'BLOCKED']);
  const hasOwnershipAcceptance = states.includes('ACK');
  if (ackStep) {
    const continuationId = ackStep.payload?.continuation_id;
    for (const step of steps) {
      if (continuationStates.has(step.state) && step.state !== 'PREPARED') {
        const actual = step.payload?.continuation_id;
        if (actual !== continuationId) {
          errors.push({ code: 'continuation_id_not_stable', state: step.state, expected: continuationId, actual });
        }
      }
    }
  }

  const terminalState = states[states.length - 1];
  const terminalPayload = steps[steps.length - 1]?.payload || {};
  if (terminalState === 'DONE') {
    for (const field of ['durable_result_anchor', 'result_kind']) {
      if (!(field in terminalPayload)) {
        errors.push({ code: 'done_terminal_field_missing', field });
      }
    }
  }
  if (terminalState === 'BLOCKED') {
    for (const field of ['blocked_reason', 'owner_for_decision', 'recovery_suggestion']) {
      if (!(field in terminalPayload)) {
        errors.push({ code: 'blocked_terminal_field_missing', field });
      }
    }
  }

  if (states.length === 2 && states[0] === 'PREPARED' && states[1] === 'BLOCKED') {
    if ('continuation_id' in terminalPayload && terminalPayload.continuation_id) {
      observations.push({ code: 'prepared_to_blocked_continuation_id_present', detail: 'allowed but not required by fixture rule' });
    }
    if (specialRules.prepared_to_blocked?.must_explain_preexecution_invalidity) {
      const text = [terminalPayload.summary, terminalPayload.blocked_reason, terminalPayload.next_action]
        .filter(Boolean)
        .join(' ')
        .toLowerCase();
      const conservativeHints = ['invalid', 'missing', 'unauthorized', 'pre-execution', 'before ownership', 'before any continuation attempt'];
      if (!conservativeHints.some((hint) => text.includes(hint))) {
        observations.push({ code: 'prepared_to_blocked_explanation_not_semantically_checked', detail: 'verifier keeps this conservative and only checks presence of explanatory fields, not deep semantics' });
      }
    }
  }

  if (hasOwnershipAcceptance && terminalState === 'BLOCKED' && !('continuation_id' in terminalPayload)) {
    errors.push({ code: 'blocked_after_ack_missing_continuation_id' });
  }

  return { ok: errors.length === 0, errors, observations };
}

function verifyInvalidCase(example) {
  const errors = [];
  const states = example.path || [];
  if (states.length < 2) {
    errors.push({ code: 'invalid_example_too_short' });
  }
  let detectedFailure = null;
  for (let i = 0; i < states.length - 1; i += 1) {
    const key = `${states[i]}->${states[i + 1]}`;
    if (!allowedTransitions.has(key)) {
      if (states[i] === 'DONE') detectedFailure = 'terminal_state_reopened_in_place';
      else if (states[i] === 'BLOCKED') detectedFailure = 'blocked_attempt_must_restart_as_new_attempt';
      else if (key === 'PREPARED->RUNNING') detectedFailure = 'missing_ack_transition';
      else if (key === 'ACK->DONE') detectedFailure = 'missing_running_transition';
      else if (key === 'RUNNING->ACK') detectedFailure = 'backward_transition_not_allowed';
      else detectedFailure = 'transition_not_allowed';
      break;
    }
  }
  if (!detectedFailure) {
    errors.push({ code: 'invalid_example_not_rejected', detail: states.join(' -> ') });
  }
  return {
    ok: errors.length === 0 && detectedFailure === example.expected_failure,
    detected_failure: detectedFailure,
    errors: detectedFailure === example.expected_failure ? errors : errors.concat(detectedFailure ? [{ code: 'unexpected_failure_code', expected: example.expected_failure, actual: detectedFailure }] : []),
  };
}

const validResults = fixture.cases.map((testCase) => {
  const verification = verifyValidCase(testCase);
  return {
    id: testCase.id,
    expected_valid: true,
    verdict: verification.ok ? 'pass' : 'fail',
    ...verification,
  };
});

const invalidResults = fixture.invalid_transition_examples.map((example) => {
  const verification = verifyInvalidCase(example);
  return {
    id: example.id,
    expected_valid: false,
    expected_failure: example.expected_failure,
    verdict: verification.ok ? 'pass' : 'fail',
    ...verification,
  };
});

const report = {
  verifier: {
    name: 'continuation-state-machine-verifier-v0',
    version: '0.1.0',
    mode: 'conservative-bounded',
    generated_at: new Date().toISOString(),
    fixture_path: path.relative(process.cwd(), fixturePath),
    output_path: path.relative(process.cwd(), outputPath),
  },
  fixture_contract_version: fixture.contract_version,
  summary: {
    valid_cases_total: validResults.length,
    valid_cases_passed: validResults.filter((r) => r.verdict === 'pass').length,
    invalid_cases_total: invalidResults.length,
    invalid_cases_passed: invalidResults.filter((r) => r.verdict === 'pass').length,
  },
  limitations: [
    'Verifier intentionally checks only explicit R1 fixture rules and listed invalid transition examples.',
    'For direct PREPARED -> BLOCKED, semantic meaning of pre-execution invalidity is not deeply inferred; verifier conservatively checks required fields and transition shape.',
    'No schema expansion beyond fixture.json is attempted.',
  ],
  valid_case_results: validResults,
  invalid_case_results: invalidResults,
};

report.summary.all_passed =
  report.summary.valid_cases_total === report.summary.valid_cases_passed &&
  report.summary.invalid_cases_total === report.summary.invalid_cases_passed;

fs.writeFileSync(outputPath, `${JSON.stringify(report, null, 2)}\n`, 'utf8');
console.log(JSON.stringify({ ok: true, outputPath, all_passed: report.summary.all_passed }, null, 2));
