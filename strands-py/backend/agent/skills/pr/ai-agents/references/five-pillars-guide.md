# Five Pillars Design Guide

> Detailed guide for designing the five core component systems of an AI agent.
> Source: "AI Agents in Action" (Manning, 2025), Chapters 1, 5, 7-11

---

## Overview

Every AI agent consists of five pillars. Not all agents need all pillars,
but understanding each is essential for informed design decisions.

```
            ┌──────────────────┐
            │  Profile/Persona │  ← Foundation (always required)
            └────────┬─────────┘
     ┌───────────────┼───────────────┐
     ↓               ↓               ↓
┌─────────┐   ┌───────────┐   ┌───────────┐
│ Actions │   │ Knowledge │   │ Reasoning │
│ & Tools │   │ & Memory  │   │ & Eval.   │
└────┬────┘   └─────┬─────┘   └─────┬─────┘
     └───────────────┼───────────────┘
                     ↓
            ┌──────────────────┐
            │ Planning/Feedback│  ← Orchestration layer
            └──────────────────┘
```

---

## Pillar 1: Profile & Persona

### Definition

The base description of the agent. Guides behavior, responses, and task approach.

### Components

| Component | Description | Example |
|:---|:---|:---|
| **Role** | What the agent does (1-2 sentences) | "Senior Python developer specializing in API design" |
| **Background** | Domain expertise and experience | "10 years in fintech, expert in PCI-DSS compliance" |
| **Demographics** | Persona characteristics (optional) | "Precise, methodical, prefers code over prose" |
| **Tone & Style** | How the agent communicates | "Professional but approachable, uses bullet points" |
| **Constraints** | What the agent must NOT do | "Never execute DELETE queries without confirmation" |
| **Output format** | Standard output structure | "Always respond with JSON containing status, data, message" |

### Generation Methods

| Method | Pros | Cons | Best For |
|:---|:---|:---|:---|
| **Handcrafted** | Full control, precise | Time-consuming, may miss edge cases | Production agents |
| **LLM-assisted** | Fast, creative variations | May need refinement | Rapid prototyping |
| **Data-driven** | Optimized by metrics | Requires evaluation pipeline | Large-scale systems |
| **Evolutionary** | Explores design space | Computationally expensive | Research, optimization |

### Quality Evaluation

Use rubrics and grounding to evaluate profile quality:

1. Define rubric criteria (specificity, accuracy, completeness)
2. Score each criterion (1-5 scale)
3. Compare variants using batch processing
4. Select the best performing profile
5. Iterate with modifications

---

## Pillar 2: Actions & Tools

### Definition

External capabilities the agent can invoke to interact with the world beyond language generation.

### Action Categories

| Category | Description | Examples |
|:---|:---|:---|
| **Task completion** | Actions that accomplish work | Database query, file creation, API call |
| **Exploration** | Actions that gather information | Web search, document retrieval, code analysis |
| **Communication** | Actions that interact with entities | Email send, Slack message, agent-to-agent message |

### Function Types

| Type | Definition | When to Use |
|:---|:---|:---|
| **Semantic function** | Prompt-based; wraps an LLM call with structured template | Transformation, summarization, reasoning |
| **Native function** | Code-based; executes deterministic logic | API calls, database queries, file I/O |
| **Composite** | Semantic wrapping native (or vice versa) | LLM reasoning about API results |

### Action Count Guidelines

| Count | Risk Level | Recommendation |
|:---|:---|:---|
| 1-3 | Low | Focused agent, predictable behavior |
| 4-7 | Medium | Monitor for tool confusion; ensure clear descriptions |
| 8-15 | High | Consider splitting into multiple agents |
| 15+ | Very High | Likely hits API limits; must split |

### Safety Classification

| Class | Description | Example | Required Guardrail |
|:---|:---|:---|:---|
| **Read-only** | No side effects | Search, query, analyze | Minimal |
| **Write** | Creates or modifies data | File write, DB insert, email send | Logging + optional approval |
| **Destructive** | Deletes or irreversibly changes | File delete, DB drop, post to social media | Mandatory approval |

### Design Principles

1. **Minimal action set**: Only provide actions needed for the goal
2. **Clear descriptions**: Each action needs a precise description of purpose, inputs, outputs
3. **Safety by default**: Classify all actions and add guardrails to destructive ones
4. **Composability**: Design actions to be combinable (semantic + native)
5. **Idempotency**: Where possible, make actions safe to retry

---

## Pillar 3: Knowledge & Memory

### Definition

Knowledge = external, persistent information.
Memory = interaction history, learned preferences, task context.

### Knowledge Implementation (RAG)

```
Documents → Chunking → Embedding → Vector Store
                                        ↓
Query → Embedding → Similarity Search → Top-K → Prompt + Context → LLM
```

| Component | Options | Selection Criteria |
|:---|:---|:---|
| **Chunking** | Character / Token / Recursive / Semantic | Document structure, LLM context window |
| **Embedding** | OpenAI / Cohere / Local (sentence-transformers) | Cost, privacy, quality |
| **Vector DB** | Chroma / Pinecone / Weaviate / pgvector | Scale, deployment, cost |
| **Top-K** | 3-10 (typical) | Balance between context and noise |

### Memory Types

| Type | What It Stores | Implementation | Example |
|:---|:---|:---|:---|
| **Semantic** | Facts, concepts, relationships | Vector DB + fact tags | "User prefers Python over Java" |
| **Episodic** | Specific events, interactions | Vector DB + timestamps | "Last week, user asked about Tokyo" |
| **Procedural** | Skills, processes, how-to | Vector DB + task tags | "Deploy with: terraform apply" |
| **Buffer** | Current conversation | In-memory list | Last 10 messages |
| **Summary** | Compressed long-term context | LLM-generated summaries | "User is a senior dev working on fintech" |

### Design Decision

```
Need external documents? → RAG (Knowledge)
Need conversation history? → Buffer or Summary Memory
Need to remember facts about user? → Semantic Memory
Need to recall past events? → Episodic Memory
Need to remember procedures? → Procedural Memory
```

---

## Pillar 4: Reasoning & Evaluation

### Definition

Reasoning = internal thinking process.
Evaluation = quality assessment of outputs and processes.

### Reasoning Hierarchy (simplest → most complex)

1. **Q&A prompting** — Direct question-answer
2. **Few-shot** — Examples guide the model
3. **Zero-shot** — Leverages training knowledge
4. **Chain of Thought** — Step-by-step reasoning
5. **Zero-shot CoT** — "Let's think step by step"
6. **Prompt chaining** — Sequential prompt pipeline
7. **Self-consistency** — Multiple solutions, vote on best
8. **Tree of Thought** — Multi-path exploration + evaluation

### Evaluation Methods

| Method | When | Implementation |
|:---|:---|:---|
| **Rubric-based** | Design time | Score profiles against criteria |
| **Grounding** | Runtime | Compare output to reference data |
| **Self-evaluation** | Runtime | LLM evaluates its own output |
| **Cross-agent** | Runtime | Another agent evaluates |
| **Human feedback** | Post-runtime | User ratings and corrections |
| **Batch comparison** | Design time | Compare multiple variants |

### Reasoning Cost-Benefit

| Application Type | Recommended Depth | Why |
|:---|:---|:---|
| Real-time chat | Low (Q&A, Few-shot) | Latency-sensitive |
| Customer service | Low-Medium (Few-shot, CoT) | Balance speed and quality |
| Code generation | Medium (CoT, Prompt chaining) | Accuracy matters |
| Research | High (Self-consistency, ToT) | Quality over speed |
| Autonomous tasks | Medium-High | Self-correction needs |

---

## Pillar 5: Planning & Feedback

### Definition

Planning = task decomposition and sequencing.
Feedback = adaptive correction based on results.

### Planning Strategies

| Strategy | When to Use | LLM Support |
|:---|:---|:---|
| **None** | No tools, simple chat | All LLMs |
| **Parallel** | Independent actions | Most LLMs with tool use |
| **Sequential** | Dependent actions | OpenAI Assistants, Claude, custom planners |
| **Iterative** | Ambiguous goals | Custom implementation |
| **Feedback-enhanced** | External feedback available | Custom implementation |

### Planning Granularity

| Granularity | Description | Risk |
|:---|:---|:---|
| **Too coarse** | "Analyze the data" | Agent may miss subtasks |
| **Optimal** | "1. Query DB, 2. Clean data, 3. Compute stats" | Clear, actionable steps |
| **Too fine** | "1a. Open connection, 1b. Execute SELECT..." | Overwhelming, brittle |

Rule of thumb: **1 step = 1 action/tool call**

### Feedback Sources

| Source | Description | Best For |
|:---|:---|:---|
| **Environmental** | Results from action execution | Error handling, retry logic |
| **Human** | Explicit user input | Quality assurance, preference learning |
| **Self-generated** | Agent's own evaluation | Autonomous improvement |

### Feedback Integration Pattern

```
Goal → Plan → Execute → Evaluate → Improved?
                  ↑                    │
                  └── Replan ──────────┘ (No, within iteration limit)
                                       │
                                   Result (Yes, or limit reached)
```

Iteration limit recommendation: 3-5 for interactive, 10-20 for batch/autonomous.
