# Planning Strategies Reference

> Comparison and application guide for AI agent planning strategies.
> Source: "AI Agents in Action" (Manning, 2025), Chapter 11

---

## Core Principle

> "Agents and assistants who can't plan and only follow simple interactions
> are nothing more than chatbots." — Chapter 11

Planning is what separates an intelligent agent from a glorified chatbot.
It enables agents to take a goal, decompose it, execute steps, and deliver results.

---

## Strategy Comparison

### 1. No Planner (Raw LLM)

```
User → Goal → LLM → Single response (may fail on multi-step tasks)
```

| Aspect | Detail |
|:---|:---|
| **When to use** | Simple Q&A, no tool use, single-step tasks |
| **Limitation** | Cannot chain sequential actions; only parallel actions work |
| **LLM support** | All LLMs |
| **Cost** | Lowest |

---

### 2. Sequential Planning

```
Goal → [Planner] → Step 1 → Step 2 → ... → Step N → Result
                     ↓         ↓               ↓
                  Action A   Action B         Action N
                  (depends    (depends
                   on none)    on A's output)
```

| Aspect | Detail |
|:---|:---|
| **When to use** | Actions depend on previous outputs; ordered execution required |
| **Key feature** | Each step uses the output of the previous step as input |
| **LLM support** | OpenAI Assistants, Anthropic Claude, custom planners |
| **Limitation** | GPT-4o raw API does NOT support this natively |
| **Cost** | Low-Medium |

**Example from book**: Search Wikipedia → Get page → Save to file (sequential dependency)

---

### 3. Parallel Planning

```
Goal → [Planner] → ┌─ Step A ─┐
                    ├─ Step B ─┤ → Merge → Result
                    └─ Step C ─┘
```

| Aspect | Detail |
|:---|:---|
| **When to use** | Actions are independent and can execute simultaneously |
| **Key feature** | No inter-step dependencies |
| **LLM support** | Most LLMs with tool use support |
| **Limitation** | Not suitable for dependent actions |
| **Cost** | Low (same as single call with multiple tool uses) |

---

### 4. Iterative Planning (AutoGPT Pattern)

```
Goal → Plan → Execute → Evaluate → Complete?
                 ↑                     │
                 └──── Replan ─────────┘ (No)
                                       │
                                   Result (Yes)
```

| Aspect | Detail |
|:---|:---|
| **When to use** | Goal is ambiguous, exploration needed, autonomous operation |
| **Key feature** | Agent continuously evaluates and replans |
| **LLM support** | Custom implementation required |
| **Limitation** | Unpredictable; requires guardrails |
| **Cost** | High (multiple cycles) |
| **Max iterations** | Recommend 10-20 for batch, 3-5 for interactive |

**Example from book**: AutoGPT's original design (Ch. 1, Fig. 1.9)

---

### 5. Feedback-enhanced Planning

```
Goal → Plan → Execute → Evaluate → Feedback → Improved?
                 ↑                                  │
                 └── Replan ←───────────────────────┘ (No)
                                                    │
                                                Result (Yes)
                              Feedback sources:
                              ├─ Environmental (API errors, results)
                              ├─ Human (user corrections, approvals)
                              └─ Self-generated (agent reflection)
```

| Aspect | Detail |
|:---|:---|
| **When to use** | External feedback sources available; quality improvement needed |
| **Key feature** | Integrates environmental, human, and self-generated feedback |
| **LLM support** | Custom implementation required |
| **Limitation** | Most complex to implement |
| **Cost** | Highest |

---

## Selection Decision Flow

```
Does the agent use tools/actions?
├─ No → No Planner (simple chat)
└─ Yes → Are all actions independent?
     ├─ Yes → Parallel Planning
     └─ No (dependencies exist) → Is the goal well-defined?
          ├─ Yes → Sequential Planning
          └─ No → Is external feedback available?
               ├─ Yes → Feedback-enhanced Planning
               └─ No → Iterative Planning (⚠ guardrails required)
```

---

## Application-Strategy Matrix

| Application | Planning Strategy | Reasoning | Evaluation | Feedback |
|:---|:---|:---|:---|:---|
| **Personal assistant** | Sequential | Limited (latency) | Internal | User feedback |
| **Customer service bot** | Minimal/None | Not typical | Quality scoring | Customer satisfaction |
| **Autonomous agent** | Iterative/Feedback | Essential | Internal + external | Environmental + human |
| **Collaborative workflows** | Sequential | Variable | Cross-agent | Peer review |
| **Game AI** | Sequential | Limited (speed) | Runtime | Game state |
| **Research** | Feedback-enhanced | Critical | Rubric-based | Iterative refinement |

### Detailed Application Guidance

**Personal Assistant**:
- Planning is essential for coordinating tools (calendar, email, search)
- Reasoning should be limited to avoid slow responses
- Feedback primarily from user preferences

**Customer Service Bot**:
- Usually operates in a controlled environment with specific tools
- Extensive planning is rarely needed
- Focus on consistent, accurate responses rather than complex reasoning

**Autonomous Agent**:
- Planning is the core requirement
- Must handle sequential, dependent actions
- Iterative planning with feedback for complex goals
- Strong guardrails and evaluation are mandatory

**Collaborative Workflows**:
- Think: agents working alongside developers
- Planning coordinates between multiple agents or human-agent pairs
- Cross-agent evaluation improves quality

**Game AI**:
- Planning for tactical decisions
- Speed is critical; reasoning must be fast
- Environmental feedback from game state

**Research**:
- Most demanding: deep reasoning + extensive planning
- Feedback-enhanced planning for iterative hypothesis refinement
- Cost is secondary to quality

---

## Framework Support Matrix

| Framework | Sequential | Parallel | Iterative | Feedback | Custom Planner |
|:---|:---|:---|:---|:---|:---|
| **OpenAI Assistants** | Built-in | Built-in | Partial | Limited | No |
| **Anthropic Claude** | Built-in | Built-in | Partial | Limited | No |
| **AutoGen** | Via orchestration | Yes | Yes | Yes | Yes |
| **CrewAI** | Via process | Yes | Via task loop | Yes | Yes |
| **Semantic Kernel** | Built-in planners | Yes | Yes | Custom | Yes (SK Planner API) |
| **LangChain** | Via chains | Via parallel chain | Via agents | Via callbacks | Yes (Agent class) |
| **Nexus** | Custom planner | Yes | Custom | Custom | Yes (full control) |

### Key Insight from Book

> "Anthropic's Claude and OpenAI Assistants support sequential action planning.
> This means both models can be called with sequential plans, and the model
> will execute them and return the results." — Chapter 11

Most raw LLM APIs (e.g., GPT-4o chat completions) only support parallel actions.
For sequential planning, use either:
1. A platform with built-in planning (OpenAI Assistants, Claude)
2. A custom planner implementation
3. An orchestration framework (AutoGen, CrewAI, Semantic Kernel)

---

## Custom Planner Implementation Pattern

### Prompt-based Planner

```python
# Pseudo-code for a basic sequential planner
PLANNER_PROMPT = """
Given the following goal, create a step-by-step plan.
Each step should use exactly one available action.
Format: Step N: [action_name](parameters) - purpose

Goal: {goal}
Available actions: {actions}
"""

def plan_and_execute(goal, actions, llm):
    # 1. Generate plan
    plan = llm.call(PLANNER_PROMPT.format(goal=goal, actions=actions))
    steps = parse_steps(plan)

    # 2. Execute sequentially
    context = {}
    for step in steps:
        result = execute_action(step.action, step.params, context)
        context[step.name] = result

        # 3. Evaluate (optional)
        if not evaluate(result, step.expected):
            # 4. Replan from this point
            remaining = replan(goal, steps[step.index:], context, llm)
            steps = steps[:step.index] + remaining

    return context
```

### Feedback-enhanced Planner

Add a feedback loop after execution:

```python
def plan_with_feedback(goal, actions, llm, max_iterations=5):
    for i in range(max_iterations):
        plan = generate_plan(goal, actions, llm)
        results = execute_plan(plan)
        evaluation = evaluate_results(results, goal)

        if evaluation.score >= threshold:
            return results

        # Incorporate feedback into next iteration
        feedback = collect_feedback(evaluation, results)
        goal = refine_goal(goal, feedback)

    return results  # Return best effort after max iterations
```

---

## Action Selection Best Practices

From Chapter 11, key warnings about action design for planners:

1. **Limit actions**: Too many confuse the agent
2. **API limits**: Most APIs limit the number of tool definitions
3. **Unintended use**: Agents may use actions in unexpected ways
4. **Safety**: Actions have real consequences; agents can go rogue
5. **Match actions to plan**: Each plan step should map to exactly one action

> "While writing this book and working with and building agents over many hours,
> I have encountered several instances of agents going rogue with actions, from
> downloading files to writing and executing code when not intended." — Chapter 11
