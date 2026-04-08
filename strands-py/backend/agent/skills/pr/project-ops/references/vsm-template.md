# Value Stream Mapping (VSM) Template

> Source: Architecture for Flow (Susanne Kaiser) — Ch.8-9
> Quick-reference for Step 4 (TOC Application / Constraint Identification)

---

## VSM Notation

```
[Process Step]
  CT: Cycle Time (actual work time)
  WT: Wait Time (idle/queue time)
  LT: Lead Time (CT + WT)
  C/A: Complete & Accurate % (quality of output)
```

---

## VSM Template (fill per change stream)

```
Change Stream: _______________________
Date: _______

[Step 1: ________] → [Step 2: ________] → [Step 3: ________] → [Step 4: ________] → [Delivered]
  CT: ___h            CT: ___h              CT: ___h              CT: ___h
  WT: ___h            WT: ___h              WT: ___h              WT: ___h
  LT: ___h            LT: ___h              LT: ___h              LT: ___h
  C/A: ___%           C/A: ___%             C/A: ___%             C/A: ___%

──────────────────────────────────────────────────────────────────────────
Summary:
  Total VA (Cycle Time):  ___h
  Total NVA (Wait Time):  ___h
  Total Lead Time:        ___h
  Flow Efficiency:        VA / LT x 100 = ____%
──────────────────────────────────────────────────────────────────────────
```

---

## Typical Software Delivery VSM Steps

| Step | Typical Actors | Common Bottleneck Signals |
|:---|:---|:---|
| **Requirement Refinement** | PO, Analyst | Incomplete specs (low C/A%), rework |
| **Development** | Developer | WIP overload, context switching |
| **Code Review** | Reviewer | Single-reviewer dependency, long queue |
| **QA / Testing** | QA Team | Manual testing, environment wait |
| **Staging Deploy** | DevOps / Platform | Manual deploy steps, environment config |
| **Production Deploy** | DevOps / Platform | Approval gates, change advisory board |
| **Monitoring / Validation** | SRE / Ops | Alert noise, missing observability |

---

## Constraint Identification Signals

| Signal | What It Means | Where to Look |
|:---|:---|:---|
| **Longest queue** | Work piling up before a step | Kanban board WIP distribution |
| **Longest wait time** | Idle time between steps | WT column in VSM |
| **Idle downstream** | Resources waiting for input | Developer idle after review bottleneck |
| **Lowest C/A%** | Quality issues causing rework | Defect rates per step, rework frequency |
| **Highest context switching** | Multitasking reduces throughput | Developer survey, WIP per person |

---

## TOC 5 Focusing Steps — Action Template

| Step | Question | Action | Evidence |
|:---|:---|:---|:---|
| **1. Identify** | Where does work pile up? | VSM analysis + queue observation | ___ |
| **2. Exploit** | How to maximize constraint output? | Remove NVA from constraint, prioritize constraint work | ___ |
| **3. Subordinate** | How to prevent flooding the constraint? | WIP limits upstream, pull-based flow | ___ |
| **4. Elevate** | How to increase constraint capacity? | Staffing, automation, skill development, tooling | ___ |
| **5. Repeat** | Is the constraint still the same? | Re-run VSM, check if bottleneck shifted | ___ |

---

## Flow Efficiency Benchmarks

| Flow Efficiency | Assessment | Typical Cause |
|:---|:---|:---|
| **< 5%** | Severely blocked | Handoffs, approvals, environment waits |
| **5-15%** | Typical (sadly common) | Functional silos, manual processes |
| **15-40%** | Good | Some SA teams, reasonable automation |
| **> 40%** | Excellent | Mature SA teams, full CI/CD, minimal handoffs |

**Key insight**: Most organizations operate at 5-15% flow efficiency. The gap between VA and NVA is where improvement lives.

> "Any improvement made anywhere besides the bottleneck is an illusion." — Eliyahu Goldratt
