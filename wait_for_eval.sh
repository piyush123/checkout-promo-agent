#!/bin/bash
while true; do
  output=$(GOOGLE_API_USE_CLIENT_CERTIFICATE=false GOOGLE_API_USE_MTLS_ENDPOINT=never agents-cli eval results --run-id projects/837227393259/locations/global/evaluationRuns/8986792318929469440 2>&1)
  if echo "$output" | grep -q "EvaluationRunState.SUCCEEDED"; then
    agentapi send-message 1a5f5bc0-3c39-4f2b-b12e-2bd784cffc8a "✅ Vertex AI Evaluation Run has completed! Your scorecard and HTML dashboard are now available in your terminal / 'artifacts/grade_results/' directory."
    break
  fi
  if echo "$output" | grep -q "EvaluationRunState.FAILED"; then
    agentapi send-message 1a5f5bc0-3c39-4f2b-b12e-2bd784cffc8a "❌ Vertex AI Evaluation Run has failed. Please check the logs in your workspace."
    break
  fi
  sleep 30
done
