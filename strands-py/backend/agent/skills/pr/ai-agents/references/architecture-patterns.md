# Architecture Patterns Reference

> 6 AI Agent Architecture Patterns derived from "AI Agents in Action" (Manning, 2025)

---

## Pattern A: Single Agent

### Structure

```
User → [Agent Profile + LLM] → Response
            ↓
     Actions/Tools (optional)
     Knowledge/Memory (optional)
     Reasoning (optional)
```

### Characteristics

| Aspect | Detail |
|:---|:---|
| **Topology** | 1 Agent + 1 LLM |
| **Autonomy** | L1-L2 |
| **Complexity** | Low |
| **Cost** | Low |
| **Best for** | Single-domain tasks, Q&A, data analysis |

### When to Use

- Task is confined to a single domain
- No need for cross-validation or parallel processing
- Simple enough for one agent to handle end-to-end
- Cost constraints are tight

### Examples from Book

- GPT Assistant with code interpretation (Ch. 3)
- Calculus Made Easy tutor (Ch. 3)
- Data science assistant (Ch. 3)

---

## Pattern B: Proxy Agent

### Structure

```
User → [Proxy Agent] → [Specialized Model/LLM] → Response
            ↓
     Reformulates/optimizes prompt
```

### Characteristics

| Aspect | Detail |
|:---|:---|
| **Topology** | Proxy + Target Model |
| **Autonomy** | L1 |
| **Complexity** | Low |
| **Cost** | Low-Medium |
| **Best for** | Model-to-model mediation, prompt optimization |

### When to Use

- User input needs reformulation for a specialized model
- Interfacing between different model capabilities (text → image)
- Transparent mediation is acceptable

### Examples from Book

- ChatGPT reformulating prompts for DALL-E 3 (Ch. 1)
- Proxy for specialized fine-tuned models

---

## Pattern C: Controller-Workers

### Structure

```
User → [Controller/Proxy Agent]
            ↓
     ┌──────────┴──────────┐
     ↓                      ↓
[Worker Agent A]      [Worker Agent B]
  (Specialist 1)       (Specialist 2)
     └──────────┬──────────┘
            ↓
     Coordinated Output → User
```

### Characteristics

| Aspect | Detail |
|:---|:---|
| **Topology** | Star (Controller at center) |
| **Autonomy** | L2-L3 |
| **Complexity** | Medium-High |
| **Cost** | Medium-High |
| **Best for** | Multi-domain tasks, parallel processing, cross-validation |

### When to Use

- Task requires multiple specializations (coder + tester, analyst + visualizer)
- Parallel processing of independent subtasks is beneficial
- Cross-validation between agents improves quality
- Clear delegation and coordination is needed

### Communication Patterns

| Sub-pattern | Description | Use When |
|:---|:---|:---|
| **Sequential pipeline** | Worker A → Worker B → Worker C | Tasks have strict ordering |
| **Parallel fanout** | Controller → [A, B, C] → Merge | Tasks are independent |
| **Iterative loop** | Controller → Worker → Controller (repeat) | Refinement is needed |

### Framework Support

| Framework | Implementation |
|:---|:---|
| **AutoGen** | UserProxyAgent + AssistantAgent(s) |
| **CrewAI** | Crew with sequential/hierarchical process |
| **Custom** | Nexus with multi-agent configuration |

### Examples from Book

- Coder + Tester agents (Ch. 1, 4)
- AutoGen multi-agent code generation (Ch. 4)
- CrewAI coding agents with reviewer (Ch. 4)

---

## Pattern D: Group Chat

### Structure

```
User → [Agent Group Chat]
            ↓
     Agent A ↔ Agent B ↔ Agent C
     (free-form communication)
            ↓
     Consensus/Leader Summary → User
```

### Characteristics

| Aspect | Detail |
|:---|:---|
| **Topology** | Mesh (all-to-all) |
| **Autonomy** | L2-L3 |
| **Complexity** | High |
| **Cost** | High (many LLM calls) |
| **Best for** | Brainstorming, collaborative exploration, creative tasks |

### When to Use

- Tasks benefit from emergent dialogue and diverse perspectives
- No single correct approach; exploration is valued
- Creative or research-oriented tasks
- Agents need to build on each other's ideas

### Caution

- Less predictable than Controller-Workers
- Harder to debug
- Higher token consumption
- May need a "moderator" agent to prevent off-topic drift

### Framework Support

| Framework | Implementation |
|:---|:---|
| **AutoGen** | GroupChat + GroupChatManager |
| **CrewAI** | Crew with hierarchical process |

### Examples from Book

- AutoGen group chat for collaborative coding (Ch. 4)
- CrewAI jokester crew (Ch. 4)

---

## Pattern E: Agentic Behavior Tree (ABT)

### Structure

```
User → [Goal] → Behavior Tree Root
                    ↓
            [Root: Sequence]
           ┌────┬────┬────┐
           ↓    ↓    ↓    ↓
        [Cond] [Action] [Selector] [Decorator]
                  ↓         ↓
             [LLM Call]  [Fallback Action]
```

### Node Types

| Node | Symbol | Behavior |
|:---|:---|:---|
| **Selector** | `?` | OR: succeeds if any child succeeds |
| **Sequence** | `→` | AND: succeeds if all children succeed in order |
| **Condition** | `◇` | Tests a state/condition, returns success/failure |
| **Action** | `□` | Performs work (LLM call, API call, etc.) |
| **Decorator** | `◯` | Wraps a child node with additional behavior |
| **Parallel** | `⇉` | Runs multiple children simultaneously |

### Characteristics

| Aspect | Detail |
|:---|:---|
| **Topology** | Tree (hierarchical) |
| **Autonomy** | L3 |
| **Complexity** | High |
| **Cost** | Variable |
| **Best for** | Complex workflows, robotics-like control, multi-step orchestration |

### When to Use

- Task has a well-defined structure with clear conditions and branches
- Modularity and reusability of subtrees is important
- Debugging and visualization of execution flow is needed
- Combining structured and emergent behaviors

### Construction Method: Back Chaining

1. Define the goal (root outcome)
2. Identify the final action needed to achieve the goal
3. Work backward: what conditions and prior actions are needed?
4. Continue backward until all leaf nodes are defined
5. Optimize: combine common subtrees, add fallbacks

### Examples from Book

- Code competition solver (Ch. 6)
- YouTube-to-X posting pipeline (Ch. 6)
- ABT with back chaining for complex systems (Ch. 6)

---

## Pattern F: Platform Agent (Nexus Pattern)

### Structure

```
┌─────────────────────────────────────┐
│          User Interface              │
│  (Web Chat / Dashboard / API / Bot)  │
├─────────────────────────────────────┤
│          Agent Engine                │
│  ├── Profile Manager                 │
│  ├── Action/Tool Registry            │
│  ├── Planner (configurable)          │
│  └── LLM Connector (multi-provider)  │
├─────────────────────────────────────┤
│          Knowledge & Memory Layer    │
│  ├── Document Store (RAG)            │
│  ├── Vector Database                 │
│  └── Memory Store (Sem/Epi/Proc)     │
├─────────────────────────────────────┤
│          Observation & Evaluation    │
│  ├── Monitoring (AgentOps)           │
│  ├── Evaluation Pipeline             │
│  └── Feedback Collector              │
└─────────────────────────────────────┘
```

### Characteristics

| Aspect | Detail |
|:---|:---|
| **Topology** | Full stack (all Five Pillars integrated) |
| **Autonomy** | L1-L3 (configurable) |
| **Complexity** | Highest |
| **Cost** | Highest (but most capable) |
| **Best for** | Production systems, enterprise agents, full-featured platforms |

### When to Use

- All Five Pillars (Profile, Actions, Knowledge, Reasoning, Planning) are needed
- Multiple LLM providers need to be supported
- Full observability and monitoring is required
- The system will evolve and scale over time

### Framework Support

| Framework | Implementation |
|:---|:---|
| **Nexus** | Native support (book's reference platform) |
| **Custom** | Build with Streamlit/Gradio + LangChain/SK |

### Examples from Book

- Nexus platform (Ch. 7)
- Full-featured agent with RAG + Memory + Planner (Ch. 7, 8, 11)

---

## Pattern Selection Quick Reference

```
Single domain, simple task? ──────────────→ Pattern A (Single Agent)
Need prompt optimization for target model? → Pattern B (Proxy Agent)
Multiple specialists needed? ─────────────→ Pattern C (Controller-Workers)
Exploration/brainstorming? ───────────────→ Pattern D (Group Chat)
Complex structured workflow? ─────────────→ Pattern E (ABT)
Full-featured production system? ─────────→ Pattern F (Platform Agent)
```
