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
  # Start the local runtime and inspect models already installed
  ollama serve
  ollama list
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
| `DOCKER_OLLAMA_BASE_URL` | `http://host.docker.internal:11434` | Docker-container address for an Ollama server running on the host. |
| `LLM_MODEL` | `llama3.1:latest` | Target model. The demo setup selects the best installed local text model. |
| `LLM_TEMPERATURE` | `0.0` | Sampling temperature (`0.0` strictly enforced for determinism). |
| `LLM_SEED` | `42` | Random seed for reproducible completions. |
| `LLM_NUM_CTX` | `8192` | Context window size. |
| `LLM_TIMEOUT_S` | `120.0` | Request timeout in seconds. Backend verdict calls use this value. |
| `LLM_MAX_RETRIES` | `2` | Number of validation retry loops feeding back errors. |
| `LLM_ALLOW_REMOTE` | `false` | SSRF Guard (G10). Refuses public IP addresses unless explicitly `true`. |

---

## 4. Hardware Sizing & Recommended Models

| Tier | Model | Quantization | RAM / VRAM | Inference Speed |
|---|---|---|---|---|
| **Recommended for this demo** | `llama3.1:latest` | Local installed quantization | More memory; strongest structured-output result in the local benchmark | ~30 s mean verdict latency on the review machine |
| **Fast / low-memory** | `qwen2.5:3b` | Local installed quantization | Smaller memory footprint; more retries | ~14 s mean verdict latency on the review machine |
| **Not selected** | `qwen2.5:7b` | Local installed quantization | Larger and slower in this benchmark | Higher fallback rate in the local comparison |

*Note: On CPU-only environments, generation may take 20–60 seconds per verdict. Results are persisted to disk cache (`artifacts/v2/verdicts/`) using SHA-256 hashes of the packet and prompt version. The benchmark results above are hardware-dependent and are not a general model leaderboard.*

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
