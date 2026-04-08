# Team Effectiveness Patterns Reference

> Source: Fundamentals of Software Architecture, 2nd Edition — Ch.24
> Quick-reference for Step 5 (Team Effectiveness) and Step 6 (Anti-pattern Detection)

---

## Elastic Leadership Scoring Guide

### 5-Factor Assessment

| Factor | -20 (Low Involvement) | 0 (Balanced) | +20 (High Involvement) |
|:---|:---|:---|:---|
| **Team Familiarity** | Long-tenured, deep mutual understanding | Some new, some veteran | Mostly new members, unfamiliar with each other |
| **Team Size** | 3-5 (small, self-organizing) | 6-8 (standard) | 12+ (large, complex communication) |
| **Overall Experience** | Senior-dominant, autonomous | Mixed seniority | Junior-dominant, needs guidance |
| **Project Complexity** | Simple CRUD, well-understood domain | Moderate complexity | Novel domain, cutting-edge tech, high risk |
| **Project Duration** | < 3 months (sprint) | 3-12 months | 12+ months (marathon) |

### Interpretation

| Score Range | Recommended Style | Architect Behavior |
|:---|:---|:---|
| **-100 to -40** | Hands-off | Set guardrails, review periodically. Trust team judgment |
| **-40 to +40** | Balanced | Guide on key decisions, delegate implementation details |
| **+40 to +100** | Hands-on | Active participation, frequent reviews, mentoring |

### Re-evaluation triggers:
- Team member joins/leaves
- Major scope change
- Technology shift
- Project phase transition (exploration → implementation → stabilization)

---

## Team Warning Signs

### TE-1: Process Loss (Brooks's Law)

**Detection signals**:
- Merge conflicts increasing in frequency
- Multiple developers modifying same code sections
- Standup meetings exceeding 15 minutes
- Communication overhead growing non-linearly

**Root cause**: Adding people to a late project makes it later. Communication paths = n(n-1)/2.

**Resolution**:
1. Identify parallelizable work streams
2. If work cannot be parallelized → reject staffing request
3. If parallelizable → organize streams with clear ownership boundaries
4. Monitor merge conflict frequency as proxy metric

### TE-2: Pluralistic Ignorance ("Emperor's New Clothes")

**Detection signals**:
- Unanimous agreement with no debate
- Members avoiding eye contact during consensus
- "I thought it was just me" confessions in 1:1s
- Decisions that "nobody wanted" surfacing later

**Resolution**:
1. As facilitator, directly ask quiet/skeptical members: "What concerns do you have?"
2. Explicitly support dissenting voices: "That's a good point"
3. Use anonymous polling for sensitive decisions
4. Create psychological safety: "There are no stupid questions"

### TE-3: Diffusion of Responsibility

**Detection signals**:
- Tasks falling through cracks: "I thought someone was handling it"
- Unclear ownership of cross-cutting concerns
- Bug reports aging without assignee
- "Not my responsibility" sentiment

**Resolution**:
1. Explicit responsibility assignment (name + deadline)
2. Reduce team size to natural trust boundary (5-9 people)
3. RACI matrix for cross-cutting concerns
4. Regular ownership review: "Who owns this?"

---

## Room Metaphor: Constraint Design

### Decision Framework

| Decision Type | Analogy | Architect Role | Developer Role |
|:---|:---|:---|:---|
| **Framework selection** | The room itself (walls, foundation) | Decides | Analyzes, recommends |
| **General-purpose libraries** | Furniture | Approves | Analyzes, recommends |
| **Special-purpose libraries** | Decorations | Trusts | Decides freely |
| **Internal component design** | Room arrangement | Trusts | Decides freely |
| **Inter-component interfaces** | Doorways between rooms | Defines contracts | Implements |
| **Coding standards** | House rules | Sets minimum bar | Self-governs beyond minimum |

### Calibration Questions

| Too Tight (Control Freak) | Just Right | Too Loose (Armchair) |
|:---|:---|:---|
| "Use this exact class structure" | "The API contract is X; implementation is yours" | "Build whatever you want" |
| "Name it `CustomerServiceImpl`" | "Follow the naming convention guide" | No naming guidance at all |
| "Here's pseudocode, implement it" | "Here's the component diagram, design internals" | No architecture guidance |

---

## Leadership Patterns

### LP-1: Become the Go-to Person
- Be available for technical and non-technical questions
- Informal check-ins: "Coffee? Let's walk"
- Remember names and personal details

### LP-2: Lunch and Learn Sessions
- Weekly or bi-weekly
- Topics: new tech, post-mortems, domain deep-dives
- Presenter rotates across team (not just architect)

### LP-3: Meeting Hygiene
- Every meeting needs an agenda and a purpose
- "Why is my attendance necessary?"
- Schedule around developer flow state (avoid mid-morning)
- If it can be an email, make it an email

### LP-4: Physical/Virtual Proximity
- Sit with the team, not in a corner office
- Remote: maintain high-frequency async communication
- Visibility = trust; invisibility = suspicion

### LP-5: Protect Flow State
- Never interrupt a developer in the zone
- Use async channels for non-urgent questions
- Batch interruptions: office hours, not random taps

---

## Architect Personality Anti-patterns

| Anti-pattern | Key Signal | Self-check Question | Fix |
|:---|:---|:---|:---|
| **Control Freak** | Writing pseudocode for developers | "Am I defining internals or interfaces?" | Focus on component boundaries, not implementations |
| **Armchair Architect** | Haven't coded in months | "When did I last write code?" | Maintain hands-on involvement, at minimum code reviews |
| **Ivory Tower** | Decisions without team input | "Did I explain my reasoning?" | Always lead with WHY, seek feedback before deciding |
| **Accidental Complexity** | Overly complex diagrams/docs | "Is this complexity essential or accidental?" | Apply 4Cs: Communication, Collaboration, Clear, Concise |

### Self-diagnostic Questionnaire

Score each 1-5 (1 = never, 5 = always):

1. I explain the reasoning behind every architectural decision: ___
2. I ask for team input before finalizing designs: ___
3. I code or review code at least weekly: ___
4. I trust developers with implementation details: ___
5. My documentation is as simple as possible: ___

- **20-25**: Healthy balance
- **15-19**: Watch for emerging anti-patterns
- **10-14**: Active anti-pattern present — seek feedback from team
- **5-9**: Multiple anti-patterns — consider coaching or role adjustment
