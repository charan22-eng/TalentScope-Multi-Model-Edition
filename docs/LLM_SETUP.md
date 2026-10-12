# Local LLM Setup Guide: TalentScope Multi-Model Edition

This document details configuration, supported runtimes, recommended models, hardware requirements, and troubleshooting for the TalentScope Local LLM Verdict Engine.

---

## 1. Architecture & Operating Principle

> **Core Principle: "Code Decides, LLM Narrates" (ADR-009 / Pack §5)**
> - The champion model and decision strength are determined strictly by deterministic Python rules and Multi-Criteria Decision Analysis (MCDA).
> - The LLM receives an **evidence packet** containing only pre-computed, verified facts and numbers.
> - An invariant validator (Guard G9) parses every word and citation in the LLM response before presentation.
> - If the LLM is unreachable, timed out, or produces unfaithful numbers, the system **automatically falls back to a deterministic certified template**.

---

## 2. Supported Runtimes

The engine supports any runtime accessible on `localhost` or private subnet:

### A. Ollama (Default & Recommended)
- **URL**: `http://localhost:11434`
- **Protocol**: Native Ollama API (`/api/chat` with structured schema enforcement via `format`)
- **Download**: [https://ollama.ai](https://ollama.ai)
- **Quick Start**:
  ```bash
  # Install and pull recommended 8B model
  ollama pull llama3.1:8b
  # Or lightweight 3B model for CPU-only machines
  ollama pull llama3.2:3b
  ```

### B. OpenAI-Compatible Local Servers
Compatible with any server exposing standard `/v1/chat/completions` with JSON schema / JSON mode:
- **LM Studio**: `http://localhost:1234`
- **llama.cpp server**: `http://localhost:8080`
- **vLLM / LocalAI**: `http://localhost:8000`

---

## 3. Environment Configuration (`.env`)

Configure the following variables in `.env` or system environment:

| Variable | Default | Description |
|---|---|---|
| `LLM_ENABLED` | `true` | Feature flag. If `false`, engine always uses certified template fallback. |
| `LLM_PROVIDER` | `ollama` | Provider: `ollama` or `openai_compat`. |
| `LLM_BASE_URL` | `http://localhost:11434` | Base URL of local server (no trailing `/v1`). |
| `LLM_MODEL` | `""` | Target model. If empty, the engine auto-discovers available models. |
| `LLM_TEMPERATURE` | `0.0` | Sampling temperature (`0.0` strictly enforced for determinism). |
| `LLM_SEED` | `42` | Random seed for reproducible completions. |
| `LLM_NUM_CTX` | `8192` | Context window size. |
| `LLM_TIMEOUT_S` | `120.0` | Request timeout in seconds. |
| `LLM_MAX_RETRIES` | `2` | Number of validation retry loops feeding back errors. |
| `LLM_ALLOW_REMOTE` | `false` | SSRF Guard (G10). Refuses public IP addresses unless explicitly `true`. |

---

## 4. Hardware Sizing & Recommended Models

| Tier | Model | Quantization | RAM / VRAM | Inference Speed |
|---|---|---|---|---|
| **Optimal** | `llama3.1:8b` | Q4_K_M | 8 GB VRAM or 16 GB RAM | ~25–45 tokens/sec |
| **Alternative** | `mistral:7b` / `qwen2.5:7b` | Q4_K_M | 8 GB VRAM or 16 GB RAM | ~30–50 tokens/sec |
| **CPU / Low-Memory** | `llama3.2:3b` | Q4_K_M | 4 GB RAM | ~15–25 tokens/sec |

*Note: On CPU-only environments, generation may take 20–60 seconds per verdict. Results are persisted to disk cache (`artifacts/v2/verdicts/`) using SHA-256 hashes of the packet and prompt version.*

---

## 5. Security & Isolation Guards

1. **Guard G10 (`assert_local`)**:
   - Outbound requests to public hosts (e.g. `api.openai.com`, public IPs) are blocked at the socket level to prevent SSRF and employee-data egress.
2. **Guard G9 / VM6.3 (Employee Data Isolation)**:
   - Formatted prompts are scanned for employee-level identifiers (`employee_id`, `salary`, `employee_name`, etc.). Prompts contain aggregate benchmark statistics only.
3. **Adversarial Injection Resistance (VM6.7)**:
   - Packets are bounded as structured JSON data between boundary tokens; injected system override instructions are rejected by the validator.

---

## 6. Troubleshooting

- **Server unreachable (HTTPConnectionError)**:
  Ensure Ollama is running (`ollama serve`). Check `curl http://localhost:11434/api/tags`.
- **Validation retries exhausted**:
  The orchestrator will seamlessly present the deterministic template fallback with a badge indicating the retry violations.
- **Out of Memory (OOM)**:
  Switch to a smaller quantized model (e.g., `llama3.2:3b`) or reduce `LLM_NUM_CTX` to `4096`.
