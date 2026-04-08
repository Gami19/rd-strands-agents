# DORA Benchmarks & Improvement Patterns

> Source: Architecture for Flow (Susanne Kaiser) + Accelerate (Forsgren, Humble, Kim)
> Quick-reference for Step 1d and Step 6 (DORA Metrics Improvement)

---

## Performance Level Thresholds

| Level | Deployment Frequency | Lead Time for Changes | MTTR | Change Failure Rate |
|:---|:---|:---|:---|:---|
| **Elite** | On-demand (multiple/day) | < 1 hour | < 1 hour | 0-15% |
| **High** | Daily to weekly | 1 day - 1 week | < 1 day | 16-30% |
| **Medium** | Weekly to monthly | 1 week - 1 month | < 1 week | 16-30% |
| **Low** | Less than monthly | 1 month - 6 months | > 6 months | > 30% |

---

## Root Cause → DORA Impact Matrix

| Root Cause | Deploy Freq | Lead Time | MTTR | CFR | Priority Fix |
|:---|:---:|:---:|:---:|:---:|:---|
| Functional silo teams (handoff chains) | - | ++ | . | . | SA Team formation |
| Tightly coupled architecture (BBoM) | - | ++ | + | ++ | BC design, modularization |
| Cognitive load overload | - | + | + | + | BC count/complexity limits |
| Insufficient test automation | . | + | . | ++ | Unit + integration + E2E |
| No self-service platform | -- | ++ | + | . | Platform Team + TVP |
| Efficiency gap (on-prem operations) | -- | + | ++ | . | Replatforming |
| Pathological/bureaucratic culture | -- | + | + | + | Generative culture transition |

Legend: `++` strong negative impact, `+` moderate, `-` reduces, `--` strongly reduces, `.` minimal

---

## Improvement Playbooks by Metric

### Deployment Frequency: Low → Medium → High

| Current | Target | Key Actions | Timeline |
|:---|:---|:---|:---|
| Monthly | Weekly | CI pipeline, automated build, feature branches → trunk-based | 4-8 weeks |
| Weekly | Daily | Feature flags, automated integration tests, reduce review bottleneck | 6-12 weeks |
| Daily | On-demand | Trunk-based dev, automated canary deploys, zero-downtime releases | 3-6 months |

### Lead Time: Weeks → Days → Hours

| Bottleneck Pattern | Detection Signal | Fix |
|:---|:---|:---|
| Review wait time | PRs aging > 24h | Pair programming, mob review, async review SLA |
| QA wait time | QA queue growing | Shift-left testing, SA teams own QA |
| Deploy wait time | Manual deploy approval | Automated pipeline, self-service deploy |
| Cross-team coordination | "Waiting for Team X" | SA Team ownership, reduce dependencies |

### MTTR: Weeks → Days → Hours

| Capability | Impact on MTTR | Implementation |
|:---|:---|:---|
| Observability (logs, metrics, traces) | High | OpenTelemetry, structured events, SLO-based alerting |
| Runbook automation | Medium | Documented procedures, partial automation |
| Small deploy units | High | Microservices / modular monolith, feature flags |
| Incident response training | Medium | Game Days, chaos engineering, tabletop exercises |
| Rollback capability | High | Blue-green deploy, canary, instant rollback |

### Change Failure Rate: > 30% → < 15%

| Strategy | Expected CFR Reduction | Investment |
|:---|:---|:---|
| Unit test coverage > 80% | 5-10% reduction | Medium |
| Integration test automation | 5-10% reduction | High |
| Canary releases | 3-5% reduction | Medium |
| Code review quality (checklist-based) | 3-5% reduction | Low |
| Test in production (feature flags + observability) | 5-10% reduction | High |

---

## Westrum Culture Model Quick Assessment

Score each dimension 1-5:

| Dimension | 1 (Pathological) | 3 (Bureaucratic) | 5 (Generative) |
|:---|:---|:---|:---|
| Information flow | Hidden, weaponized | By the rules | Actively sought and shared |
| Failure response | Blame, cover-up | Procedural review | Investigation, learning |
| Novelty | Crushed | Causes problems | Implemented |
| Responsibility | Evaded | Siloed | Shared across teams |
| Cross-team cooperation | Discouraged | Tolerated | Encouraged and rewarded |
| Messenger treatment | Shot | Ignored | Trained |

**Total: 6-12** = Pathological, **13-22** = Bureaucratic, **23-30** = Generative
