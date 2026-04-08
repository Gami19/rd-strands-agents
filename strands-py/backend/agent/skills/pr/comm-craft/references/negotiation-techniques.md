# Negotiation Techniques Reference (NT-1 to NT-10)

> Source: Fundamentals of Software Architecture, 2nd Edition — Ch.25
> Quick-reference for Step 3 (Negotiation Strategy Design)

---

## Technique Matrix

| ID | Technique | Target | Core Mechanism |
|:---|:---|:---|:---|
| **NT-1** | Buzzword Decoding | Business | Listen for hidden concerns behind jargon |
| **NT-2** | Pre-negotiation Intel | All | Gather facts, numbers, and context before the meeting |
| **NT-3** | Quantification | Business | Convert abstract demands to concrete numbers |
| **NT-4** | Divide and Conquer | Business | Split overreaching requirements into scoped segments |
| **NT-5** | Cost/Time (Last Resort) | Business | Present cost/time impact only after other arguments fail |
| **NT-6** | Demonstration Defeats Discussion | Architect | Settle technical disputes with PoC or benchmark data |
| **NT-7** | Stay Calm | Architect | Pause when emotions rise; resume with logic |
| **NT-8** | Self-Discovery | Developer | Let them verify concerns themselves for automatic buy-in |
| **NT-9** | Command → Question | Developer | Replace "you must" with "have you considered?" |
| **NT-10** | Request → Favor | Developer | Frame tasks as asking for help, not giving orders |

---

## Detailed Technique Guide

### NT-1: Buzzword Decoding

**When to use**: Stakeholder uses vague terms ("lightning fast", "zero downtime", "enterprise-grade").

**How**:
1. Identify the buzzword
2. Ask "What does that mean for your use case?"
3. Map to a concrete architecture characteristic (-ility)
4. Validate: "So what you really need is P95 latency < 200ms?"

**Common decodings**:

| Buzzword | Hidden Concern | Architecture Characteristic |
|:---|:---|:---|
| "lightning fast" | Performance anxiety | Latency / Throughput |
| "zero downtime" | Availability fear | Availability (99.9%+) |
| "enterprise-grade" | Security / compliance | Security / Auditability |
| "future-proof" | Extensibility worry | Modularity / Evolvability |
| "scalable" | Growth uncertainty | Elasticity / Scalability |

### NT-3: Quantification

**Translation table for common abstract demands**:

| Abstract | Quantified | Impact |
|:---|:---|:---|
| "five nines" (99.999%) | 5 min 35 sec/year downtime | ~$1M+/year infrastructure |
| "four nines" (99.99%) | 52 min 33 sec/year downtime | Standard HA setup |
| "three nines" (99.9%) | 8 hours 46 min/year downtime | Basic redundancy |
| "high performance" | P95 < 200ms, P99 < 500ms | Caching + CDN + optimization |
| "real-time" | < 100ms end-to-end | WebSocket / event-driven |
| "near real-time" | < 1 second | Streaming pipeline |

### NT-4: Divide and Conquer

**Application pattern** (Sun Tzu: "If his forces are united, separate them"):
1. Identify the overreaching requirement
2. List all system components it touches
3. Ask: "Which specific component needs this level?"
4. Negotiate per-component requirements
5. Result: Reduced scope, realistic constraints

### NT-6: Demonstration Defeats Discussion

**Implementation checklist**:
- [ ] Production-equivalent environment set up
- [ ] Both alternatives implemented as PoC
- [ ] Measurable criteria defined before testing
- [ ] Results documented with raw data
- [ ] Team invited to observe/validate

> "It's hard to argue with a working demonstration." — Richards & Ford

### NT-8: Self-Discovery

**Script template**:
> "That's an interesting approach. If you can show me that [Framework Y]
> meets our [security/performance/compliance] requirements, I'm happy
> to adopt it. Here are the specific criteria: ___"

**Why it works**: Developer either discovers the problem themselves (automatic buy-in for your proposal) or finds a creative solution you didn't think of (win-win).

---

## Negotiation Scenario Planning Template

```
1. Counterpart Profile
   - Stated position: _____
   - Inferred real concern: _____
   - Their win condition: _____

2. My Position
   - Goal: _____
   - Acceptable concessions: _____
   - Non-negotiable line: _____

3. Strategy
   - Primary technique: NT-__
   - Secondary technique: NT-__
   - Fallback technique: NT-__
   - Evidence to prepare: _____
   - Expected objections and responses: _____

4. Exit Strategy
   - Win-win scenario: _____
   - Minimum acceptable outcome: _____
   - If no agreement: next action = _____
```

---

## Anti-patterns in Negotiation

| Anti-pattern | Signal | Fix |
|:---|:---|:---|
| Leading with cost | "That's too expensive" as opening | Lead with technical justification (NT-5 = last resort) |
| Authority pull | "Because I'm the architect" | Use evidence, not title (NT-6) |
| Public shaming | Criticizing ideas in group settings | Address concerns privately; support in public |
| Command language | "You need to...", "You must..." | "Have you considered...?" (NT-9) |
| Ignoring signals | Missing body language, tone shifts | Practice active listening, check understanding |
