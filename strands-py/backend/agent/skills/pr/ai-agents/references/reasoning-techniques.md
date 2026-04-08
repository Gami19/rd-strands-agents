# Reasoning Techniques Reference

> Comparison and selection guide for AI agent reasoning techniques.
> Source: "AI Agents in Action" (Manning, 2025), Chapter 10

---

## Technique Overview

```
Complexity & Accuracy ↑
│
│  Tree of Thought (ToT) ─── Multi-path exploration + evaluation
│       ↑
│  Self-consistency ────────── Multiple solutions, majority vote
│       ↑
│  Prompt chaining ─────────── Sequential prompt pipeline
│       ↑
│  Chain of Thought (CoT) ── Step-by-step reasoning
│       ↑
│  Zero-shot CoT ───────────── "Let's think step by step"
│       ↑
│  Few-shot prompting ──────── Examples guide the model
│       ↑
│  Zero-shot prompting ─────── No examples, use training knowledge
│       ↑
│  Q&A prompting ───────────── Direct question-answer
│
└─────────────────────────────────→ Latency & Cost
```

---

## Detailed Technique Comparison

### 1. Q&A Prompting (Direct Solution)

| Aspect | Detail |
|:---|:---|
| **How it works** | Ask a direct question, get a direct answer |
| **Complexity** | Lowest |
| **Latency** | Fastest |
| **Accuracy** | Moderate (depends on question clarity) |
| **Token cost** | Lowest |
| **When to use** | Simple factual questions, lookup tasks |
| **When to avoid** | Multi-step reasoning, complex analysis |

**Example**:
```
User: What is the capital of France?
LLM: The capital of France is Paris.
```

---

### 2. Few-shot Prompting

| Aspect | Detail |
|:---|:---|
| **How it works** | Provide 2-5 examples, then ask the model to follow the pattern |
| **Complexity** | Low |
| **Latency** | Fast (examples add tokens but no extra LLM calls) |
| **Accuracy** | High for known patterns |
| **Token cost** | Low-Medium (examples consume tokens) |
| **When to use** | Formatting output, establishing patterns, unfamiliar task types |
| **When to avoid** | Totally novel tasks with no analogous examples |

**Example**:
```
Classify the sentiment:
"I love this product" → Positive
"This is terrible" → Negative
"The weather is okay" → Neutral
"Best purchase ever!" → ?
LLM: Positive
```

**Design tip**: Choose diverse, representative examples. 3 examples is often sufficient.

---

### 3. Zero-shot Prompting

| Aspect | Detail |
|:---|:---|
| **How it works** | Ask the model to solve without any examples, relying on training |
| **Complexity** | Low |
| **Latency** | Fast |
| **Accuracy** | Variable (depends on task alignment with training) |
| **Token cost** | Lowest |
| **When to use** | General tasks, broad topics, when examples are unavailable |
| **When to avoid** | Specialized domains where the model lacks training data |

**Example**:
```
User: Translate "Hello, how are you?" to Japanese.
LLM: こんにちは、お元気ですか？
```

---

### 4. Chain of Thought (CoT)

| Aspect | Detail |
|:---|:---|
| **How it works** | Guide the model to think step by step through intermediate reasoning |
| **Complexity** | Medium |
| **Latency** | Medium (longer responses due to reasoning steps) |
| **Accuracy** | High (significant improvement on multi-step problems) |
| **Token cost** | Medium (reasoning tokens + answer tokens) |
| **When to use** | Math problems, logical reasoning, multi-step analysis |
| **When to avoid** | Simple questions (overkill), real-time latency-critical tasks |

**Example**:
```
User: If a store has 45 apples and sells 3/5 of them, how many remain?
LLM: Let me think step by step:
1. Total apples: 45
2. Fraction sold: 3/5
3. Apples sold: 45 × 3/5 = 27
4. Apples remaining: 45 - 27 = 18
Answer: 18 apples remain.
```

---

### 5. Zero-shot CoT

| Aspect | Detail |
|:---|:---|
| **How it works** | Add "Let's think step by step" to trigger reasoning without examples |
| **Complexity** | Low (minimal prompt engineering effort) |
| **Latency** | Medium |
| **Accuracy** | Moderate-High (less effective than few-shot CoT but much easier) |
| **Token cost** | Medium |
| **When to use** | Quick reasoning boost with minimal effort |
| **When to avoid** | When accuracy is critical (use full CoT or Self-consistency) |

**Example**:
```
User: A farmer has 15 sheep. All but 8 die. How many are left?
       Let's think step by step.
LLM: Step 1: The farmer starts with 15 sheep.
     Step 2: "All but 8 die" means 8 survive.
     Step 3: Therefore, 8 sheep are left.
Answer: 8
```

---

### 6. Prompt Chaining

| Aspect | Detail |
|:---|:---|
| **How it works** | Break a problem into sequential prompts, each building on the previous |
| **Complexity** | Medium |
| **Latency** | Medium-High (multiple LLM calls) |
| **Accuracy** | High (focused prompts for each subtask) |
| **Token cost** | Medium-High (N separate LLM calls) |
| **When to use** | Multi-stage problems (extract → analyze → format → summarize) |
| **When to avoid** | Simple tasks that don't benefit from decomposition |

**Example chain**:
```
Prompt 1: "Extract all numerical data from this report"
→ Output: [list of numbers and labels]

Prompt 2: "Analyze the trends in this numerical data: {output_1}"
→ Output: [trend analysis]

Prompt 3: "Write an executive summary based on: {output_2}"
→ Output: [executive summary]
```

**Design tip**: Each prompt should be focused and self-contained. Pass only necessary context between steps.

---

### 7. Self-consistency

| Aspect | Detail |
|:---|:---|
| **How it works** | Generate N solutions, then select the most common/consistent answer |
| **Complexity** | High |
| **Latency** | High (N × single solution time) |
| **Accuracy** | Very High (reduces random errors through majority voting) |
| **Token cost** | High (N × single solution cost) |
| **When to use** | High-stakes decisions, math, logic, verification tasks |
| **When to avoid** | Cost-sensitive tasks, real-time applications |

**Implementation**:
```
1. Send the same prompt N times (typically N=5 to 10)
2. Collect all responses
3. Parse the final answers from each
4. Select the most frequent answer (majority vote)
5. Optionally: use an LLM to evaluate and pick the best
```

**Example**: For a math problem, generate 5 solutions. If 4 say "42" and 1 says "38", select "42".

---

### 8. Tree of Thought (ToT)

| Aspect | Detail |
|:---|:---|
| **How it works** | Explore multiple reasoning paths, evaluate each, prune bad branches |
| **Complexity** | Highest |
| **Latency** | Highest |
| **Accuracy** | Highest |
| **Token cost** | Highest |
| **When to use** | Complex problems with multiple valid approaches, strategic planning |
| **When to avoid** | Simple problems, cost constraints, time constraints |

**Implementation**:
```
1. Generate N initial approaches to the problem
2. For each approach, take one reasoning step
3. Evaluate each partial solution (self-evaluation or cross-evaluation)
4. Prune low-scoring branches
5. Continue expanding promising branches
6. Select the best complete solution
```

**Key difference from Self-consistency**: ToT evaluates at each step (pruning), while Self-consistency evaluates only the final answer.

---

## Selection Decision Matrix

| Criterion | Q&A | Few-shot | Zero-shot | CoT | ZS-CoT | Chaining | Self-con. | ToT |
|:---|:---|:---|:---|:---|:---|:---|:---|:---|
| **Setup effort** | None | Low | None | Low | Minimal | Medium | Medium | High |
| **Latency** | 1x | 1x | 1x | 1.5x | 1.5x | Nx | Nx | N*Mx |
| **Cost** | 1x | 1.2x | 1x | 1.5x | 1.5x | Nx | Nx | N*Mx |
| **Simple facts** | Best | Good | Good | Overkill | Overkill | Overkill | Overkill | Overkill |
| **Pattern matching** | Fair | Best | Good | Good | Good | Good | Good | Good |
| **Multi-step logic** | Poor | Fair | Fair | Best | Good | Good | Very Good | Best |
| **Complex strategy** | Poor | Poor | Poor | Good | Fair | Good | Good | Best |
| **Output formatting** | Fair | Best | Fair | Good | Good | Good | Good | Good |

---

## Application-Technique Mapping

| Application Type | Primary Technique | Secondary | Why |
|:---|:---|:---|:---|
| **Customer service bot** | Few-shot | Q&A | Speed + consistent formatting |
| **Code generation** | CoT | Prompt chaining | Step-by-step correctness |
| **Data analysis** | CoT | Self-consistency | Accurate calculations |
| **Research** | ToT | Self-consistency | Thorough exploration |
| **Creative writing** | Few-shot | Zero-shot | Style guidance |
| **Math/Logic** | Self-consistency | CoT | Error reduction |
| **Summarization** | Prompt chaining | Zero-shot | Stage-by-stage compression |
| **Game AI** | Zero-shot CoT | Q&A | Speed with some reasoning |
