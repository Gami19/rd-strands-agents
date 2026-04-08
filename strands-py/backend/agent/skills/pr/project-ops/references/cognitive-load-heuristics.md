# Cognitive Load Heuristics Reference

> Source: Architecture for Flow (Susanne Kaiser) — Ch.6-7
> Quick-reference for Step 3 (Cognitive Load Optimization)

---

## Evolution Stage → BC Capacity Heuristics

| Evolution Stage | Cynefin Domain | Max BCs/Team | Practice Type | Rationale |
|:---|:---|:---|:---|:---|
| **Genesis** | Chaotic / Complex | 1 | Novel | High uncertainty, constant experimentation, unknown unknowns |
| **Custom-Built** | Complex | 1-2 | Emergent | Patterns emerging but unstable, domain expertise required |
| **Product (+rental)** | Complicated | 2-3 | Good | Established patterns, documented processes, stable APIs |
| **Commodity (+utility)** | Clear | 3+ | Best | Standardized, well-understood, low cognitive overhead |

### Cynefin Correction Factor

**Important**: Cynefin may override Wardley Evolution Stage when team experience diverges from component maturity.

| Scenario | Wardley Stage | Team Experience | Effective Cynefin | Adjusted BC Limit |
|:---|:---|:---|:---|:---|
| Senior team, mature tech | Commodity | High | Clear | 4-5 BCs |
| Junior team, mature tech | Commodity | Low | **Complex** | 1-2 BCs |
| Senior team, new tech | Genesis | High | Complex | 1 BC |
| Junior team, new tech | Genesis | Low | **Chaotic** | 1 BC (with Enabling Team support) |

---

## 3 Modalities of Cognitive Load (Sweller's CLT)

| Modality | Definition | Software Examples | Optimization Strategy |
|:---|:---|:---|:---|
| **Intrinsic** | Inherent complexity of the task | Domain complexity, algorithm complexity, regulatory requirements | Split Bounded Context, create Complicated-subsystem Team |
| **Extraneous** | Caused by poor task presentation | Unclear code structure, missing docs, tooling friction, legacy workarounds | Platform Team TVP, documentation, developer experience investment |
| **Germane** | Spent on learning and pattern recognition | New technology adoption, domain knowledge acquisition, unfamiliar architecture | Enabling Team coaching, pair programming, Software Teaming |

### Cognitive Load Assessment Template

| Team | Domain Complexity (Intrinsic) | Tooling Friction (Extraneous) | Learning Burden (Germane) | Total Assessment | Action |
|:---|:---|:---|:---|:---|:---|
| (Team A) | High / Med / Low | High / Med / Low | High / Med / Low | Overloaded / Optimal / Underloaded | (specific action) |

**Red flags** (any of these = immediate intervention):
- Team owns 2+ Genesis-stage BCs
- Intrinsic AND Extraneous both rated High
- Team has no access to Enabling Team despite Complex domain
- Bus factor = 1 for any BC

---

## Mindset Mix (T-shaped Teams)

| Evolution Stage | Dominant Mindset | Behavior Profile |
|:---|:---|:---|
| Genesis / Custom-Built | **Explorer** | Experiments, tolerates ambiguity, rapid prototyping |
| Product (+rental) | **Villager** | Improves, stabilizes, refines processes |
| Commodity (+utility) | **Town Planner** | Optimizes, standardizes, scales |

**Key insight**: Mono-mindset teams are anti-patterns:
- Explorer-only → never ships stable product
- Villager-only → never innovates
- Town Planner-only → over-optimizes prematurely

Balance: T-shaped team with dominant mindset + secondary capabilities.

---

## Platform Team TVP Maturity Ladder

| Phase | Offering | Team Interaction Mode | Indicator to Advance |
|:---|:---|:---|:---|
| **Phase 0** | Documentation, standards, checklists, best practices | N/A (reference material) | SA teams ask for more automation |
| **Phase 1** | Templates, pre-configured settings, cookbooks | Facilitating | SA teams request self-service |
| **Phase 2** | Self-service APIs, CLI tools, internal developer portal | X-as-a-Service (partial) | High adoption, low support tickets |
| **Phase 3** | Full digital platform (automated provisioning, observability, CI/CD) | X-as-a-Service (full) | SA teams rarely need direct support |
