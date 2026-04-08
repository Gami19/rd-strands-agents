# Memory & Knowledge Design Guide

> RAG pipelines, memory types, and compression strategies for AI agents.
> Source: "AI Agents in Action" (Manning, 2025), Chapter 8

---

## Knowledge vs. Memory

| Aspect | Knowledge | Memory |
|:---|:---|:---|
| **Definition** | External, persistent information | Interaction history, learned context |
| **Source** | Documents, databases, APIs | Conversations, tasks, events |
| **Persistence** | Long-lived, relatively static | Dynamic, grows with use |
| **Pattern** | RAG (Retrieval Augmented Generation) | Semantic/Episodic/Procedural recall |
| **Purpose** | Answer questions about external data | Personalize and contextualize interactions |
| **Update frequency** | Periodic (document re-indexing) | Continuous (every interaction) |

---

## Knowledge Architecture (RAG)

### Full RAG Pipeline

```
┌──────────────────── Ingestion (offline) ────────────────────┐
│                                                              │
│  Documents → Loader → Splitter → Embedder → Vector Store     │
│  (PDF/Web)   (LangChain)  (Token/Recursive)  (OpenAI)  (Chroma) │
│                                                              │
└──────────────────────────────────────────────────────────────┘

┌──────────────────── Retrieval (runtime) ────────────────────┐
│                                                              │
│  User Query → Embedder → Similarity Search → Top-K chunks    │
│                                Vector Store ↗                │
│                                                              │
│  Top-K chunks + Query → Prompt Assembly → LLM → Response     │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Document Loading Options

| Source Type | Tool | Notes |
|:---|:---|:---|
| **PDF** | LangChain PDFLoader, docling | Handles structured/unstructured PDFs |
| **Web pages** | LangChain WebBaseLoader | Requires URL access |
| **Databases** | LangChain SQLDatabaseLoader | SQL query results as documents |
| **APIs** | Custom loader | Transform API responses to documents |
| **Local files** | LangChain DirectoryLoader | Batch loading from filesystem |

### Chunking Strategies

| Strategy | How It Works | Best For | Chunk Size |
|:---|:---|:---|:---|
| **Character** | Split at fixed character count | Simple text | 500-1000 chars |
| **Token** | Split at fixed token count | LLM context-aware | 256-512 tokens |
| **Recursive** | Split hierarchically (paragraphs → sentences → words) | Structured documents | Varies |
| **Semantic** | Split by meaning boundaries | Technical documents | Varies |

**Selection guidance**:
- Start with Token splitting (most LLM-friendly)
- Use Recursive for documents with clear hierarchy (manuals, specifications)
- Use Semantic for research papers and technical content

### Embedding Models

| Model | Provider | Quality | Cost | Privacy |
|:---|:---|:---|:---|:---|
| **text-embedding-3-large** | OpenAI | Highest | $0.13/1M tokens | Data sent to API |
| **text-embedding-3-small** | OpenAI | High | $0.02/1M tokens | Data sent to API |
| **all-MiniLM-L6-v2** | Sentence Transformers | Good | Free (local) | Fully local |
| **nomic-embed-text** | Nomic AI | Good | Free (local) | Fully local |

### Vector Databases

| Database | Type | Scale | Deployment | Best For |
|:---|:---|:---|:---|:---|
| **Chroma** | In-process | Small-Medium | Local/embedded | Prototyping, small projects |
| **Pinecone** | Managed cloud | Large | Cloud | Production, high-scale |
| **Weaviate** | Self-hosted/cloud | Large | Self-host or cloud | Enterprise, hybrid search |
| **pgvector** | PostgreSQL extension | Medium-Large | Self-host | Existing PostgreSQL infrastructure |
| **FAISS** | In-process | Medium | Local | Research, high-performance |

### Similarity Search Parameters

| Parameter | Default | Range | Effect |
|:---|:---|:---|:---|
| **Top-K** | 5 | 3-20 | More results = more context but also more noise |
| **Score threshold** | 0.7 | 0.5-0.9 | Higher = more relevant but fewer results |
| **Search type** | Cosine similarity | Cosine/Euclidean/Dot product | Cosine is standard for text |

---

## Memory Architecture

### Memory Types

#### Semantic Memory (Facts & Concepts)

| Aspect | Detail |
|:---|:---|
| **Stores** | Facts, relationships, preferences, domain knowledge |
| **Example** | "User prefers Python", "Company uses AWS", "Budget is $50K" |
| **Implementation** | Vector DB with metadata tags: `{type: "semantic", topic: "..."}` |
| **Retrieval** | Semantic similarity search on fact embeddings |
| **Lifetime** | Long-term (persists across sessions) |

#### Episodic Memory (Experiences & Events)

| Aspect | Detail |
|:---|:---|
| **Stores** | Specific events, interactions, timestamps |
| **Example** | "Feb 15: User reported bug in auth module", "Jan 10: Deployed v2.0" |
| **Implementation** | Vector DB with metadata: `{type: "episodic", timestamp: "...", context: "..."}` |
| **Retrieval** | Time-based + semantic similarity |
| **Lifetime** | Medium-term to long-term |

#### Procedural Memory (Skills & Processes)

| Aspect | Detail |
|:---|:---|
| **Stores** | Learned procedures, workflows, how-to knowledge |
| **Example** | "To deploy: git push → CI runs → deploy to staging → smoke test" |
| **Implementation** | Vector DB with metadata: `{type: "procedural", task: "...", steps: [...]}` |
| **Retrieval** | Task-based similarity search |
| **Lifetime** | Long-term (persists as agent learns) |

#### Buffer Memory (Short-term Context)

| Aspect | Detail |
|:---|:---|
| **Stores** | Current conversation messages |
| **Example** | Last 10-20 messages in the current session |
| **Implementation** | In-memory list or sliding window |
| **Retrieval** | Append to prompt directly |
| **Lifetime** | Session-only (cleared between sessions) |

#### Summary Memory (Compressed Context)

| Aspect | Detail |
|:---|:---|
| **Stores** | LLM-generated summaries of conversation history |
| **Example** | "User has been working on a Python API project, focusing on auth" |
| **Implementation** | Periodically summarize buffer memory using LLM |
| **Retrieval** | Prepend to system prompt |
| **Lifetime** | Cross-session (persists as compressed summary) |

### Memory Selection Decision Tree

```
Does the agent need to remember across sessions?
├─ No → Buffer Memory only (in-memory, session-scoped)
└─ Yes → What needs to be remembered?
     ├─ Facts about user/domain → Semantic Memory
     ├─ Specific past events → Episodic Memory
     ├─ Learned procedures → Procedural Memory
     └─ General conversation context → Summary Memory
```

### Memory Augmentation Pattern (Nexus)

```
User query → Retrieve relevant memories
                 ↓
          ┌──────────────────┐
          │ Semantic matches  │ (top-3 relevant facts)
          │ Episodic matches  │ (top-2 related events)
          │ Procedural matches│ (top-1 relevant procedure)
          │ Buffer (recent)   │ (last 5 messages)
          │ Summary           │ (session summary)
          └──────────────────┘
                 ↓
          Augmented prompt → LLM → Response
                 ↓
          Store new memories (if relevant)
```

---

## Compression Strategies

### When to Compress

| Condition | Action |
|:---|:---|
| Memory entries > 1000 | Apply compression |
| Retrieval latency > 500ms | Apply compression or increase Top-K filtering |
| Storage cost exceeding budget | Apply clustering + summarization |
| Relevancy declining | Apply re-indexing + summarization |

### Clustering

**How it works**: Group related memory entries and merge duplicates.

```
Before: [fact_1, fact_2, fact_3, fact_4, fact_5] (5 entries about same topic)
After:  [merged_fact] (1 comprehensive entry)
```

| Step | Action |
|:---|:---|
| 1 | Embed all memory entries |
| 2 | Cluster by cosine similarity (threshold: 0.85) |
| 3 | For each cluster, merge entries into one comprehensive entry |
| 4 | Replace original entries with merged entries |

### Summarization

**How it works**: Use LLM to condense verbose entries into essential content.

```
Before: "On February 15, the user reported a critical authentication bug
         affecting the login module. The user explained that passwords were
         not being hashed correctly, leading to security vulnerabilities..."
After:  "2/15: Critical auth bug - password hashing failure in login module"
```

| Step | Action |
|:---|:---|
| 1 | Select entries exceeding length threshold (e.g., > 200 tokens) |
| 2 | Summarize each using LLM with compression prompt |
| 3 | Replace original with summary + pointer to full version |

### Hybrid (Clustering + Summarization)

Best approach for large memory stores:

1. **Cluster** related entries (reduce count)
2. **Summarize** verbose merged entries (reduce size)
3. **Re-index** compressed entries in vector store
4. **Archive** original entries (optional, for audit trail)

---

## Implementation Patterns with LangChain

### Basic RAG Setup

```python
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import TokenTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

# 1. Load documents
loader = PyPDFLoader("knowledge_base.pdf")
docs = loader.load()

# 2. Split into chunks
splitter = TokenTextSplitter(chunk_size=512, chunk_overlap=50)
chunks = splitter.split_documents(docs)

# 3. Create embeddings and store
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = Chroma.from_documents(chunks, embeddings)

# 4. Query
results = vectorstore.similarity_search("How to configure auth?", k=5)
```

### Memory with LangChain

```python
from langchain.memory import ConversationBufferMemory
from langchain.memory import ConversationSummaryMemory

# Buffer memory (short-term)
buffer_memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True,
    max_token_limit=2000
)

# Summary memory (long-term)
summary_memory = ConversationSummaryMemory(
    llm=llm,
    memory_key="chat_summary"
)
```

---

## Design Checklist

- [ ] Determined if Knowledge (RAG) is needed
- [ ] If RAG: selected chunking strategy, embedding model, and vector DB
- [ ] If RAG: defined Top-K and score threshold parameters
- [ ] Determined which memory types are needed (Semantic/Episodic/Procedural/Buffer/Summary)
- [ ] Defined memory lifetime and persistence strategy
- [ ] Evaluated compression needs (expected entry count > 1000?)
- [ ] If compression needed: selected strategy (Clustering/Summarization/Hybrid)
- [ ] Verified that memory design aligns with agent's autonomy level and application type
