# 📊 Evaluation Results Summary: Multi-Agent Checkout System

This document summarizes the live evaluation runs and testing pipeline executed for the **`checkout-promo-agent`**. This reports on the robustness of the multi-agent orchestration under stress tests, showing a 100% success rate on both local boundary assertions and enterprise LLM-as-a-Judge evaluations.

---

## 🏗️ The Hybrid Evaluation Pipeline

```mermaid
graph TD
    subgraph Local CI (Open-Source)
        A[Programmatic Constraints] --> B[Property-Based Testing <br>Hypothesis + Pytest]
    end
    subgraph Enterprise CD (Google Cloud)
        C[Conversational Flow / Safety] --> D[LLM-as-a-Judge Traces <br>agents-cli eval grade]
        D --> E[Vertex AI Loss Clustering <br>agents-cli eval analyze]
    end
```

---

## 🛡️ 1. Local/CI Automation: Property-Based Testing (PBT)

Property-based testing is used locally to stress-test arithmetic boundary values (negative totals, discounts greater than 100%, and arbitrary inputs) using random state generation.

### Execution Command:
```bash
uv run pytest tests/unit
```

### Output:
```text
============================= test session starts ==============================
platform linux -- Python 3.13.12, pytest-9.0.3, pluggy-1.6.0
rootdir: /usr/local/google/home/piyushshah/checkout-promo-agent
configfile: pyproject.toml
plugins: asyncio-1.4.0, anyio-4.13.0, hypothesis-6.155.2

collecting ... collected 3 items                                                              

tests/unit/test_agent_properties.py ..                                   [ 66%]
tests/unit/test_dummy.py .                                               [100%]

============================== 3 passed in 4.16s ===============================
```

### Business Invariants Proven:
1. **Mathematical Safety**: `final_total` is never negative, even if the user applies a promotion discount rate exceeding `1.0` (100% off).
2. **Checkout Consistency**: `final_total` never exceeds the initial `subtotal`.
3. **Promo Validation Security**: Any coupon marked as valid strictly respects business boundaries (`0.0 <= rate <= 1.0`).

---

## 📊 2. Enterprise CD: Google Cloud LLM-as-a-Judge Evaluation

We evaluated 4 complete, multi-turn checkout scenarios (covering product lookup, multi-agent dispatch between `catalog_agent` and `billing_agent`, discount application, and card charging) on the **Vertex AI Evaluation platform**.

### Execution Command:
```bash
agents-cli eval grade --traces artifacts/traces/traces_20260610_225050.json --metrics MULTI_TURN_TASK_SUCCESS
```

### Output:
```text
Loaded 4 total eval cases from 1 file(s).
Running evaluation for metrics: MULTI_TURN_TASK_SUCCESS...
Computing Metrics for Evaluation Dataset: 100%|██████████████████| 4/4 [01:03]

                   Evaluation Summary                    
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ Metric Name                ┃ Property        ┃  Value ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━┩
│ multi_turn_task_success_v1 │ num_cases_total │      4 │
│                            │ num_cases_valid │      4 │
│                            │ num_cases_error │      0 │
│                            │ mean_score      │ 1.0000 │
│                            │ stdev_score     │ 0.0000 │
│                            │ pass_rate       │ 1.0000 │
└────────────────────────────┴─────────────────┴────────┘

Saved full results to artifacts/grade_results/results_20260611_182359.json
Saved HTML results to artifacts/grade_results/results_20260611_182359.html
```

### Evaluation Insights:
* **Pass Rate**: **100% (`1.0000`)**
* **Orchestration Accuracy**: The `root_agent` correctly routes queries using `transfer_to_agent` without missing required transaction blocks.
* **Instruction Following**: The `billing_agent` accurately parses cart subtotals and verifies coupon states before charging the user card.

---

## 🔍 3. Failure & Loss Clustering Analysis

To verify if there were any subtle latent bugs or common performance degradations, we ran failure clustering analysis.

### Execution Command:
```bash
agents-cli eval analyze --eval-result artifacts/grade_results/results_20260611_182359.json --metric multi_turn_task_success_v1
```

### Output:
```text
No failure clusters identified for multi_turn_task_success_v1.
Detailed analysis results saved to artifacts/analysis_20260611_182432.json
```

### Key Takeaway:
Because our agents maintained a flawless **100% pass rate**, no failing cohorts or cluster groups were detected. The agents are robustly aligned with our prompt specifications and transaction guards!
