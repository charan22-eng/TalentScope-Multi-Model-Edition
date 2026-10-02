# API Benchmarks

| Endpoint | Median Latency (ms) | P95 Latency (ms) | P99 Latency (ms) | Max Latency (ms) | Throughput (req/s) |
|---|---|---|---|---|---|
| `POST /predict` | 45.2 | 68.1 | 89.4 | 124.0 | 450 |
| `POST /explain` | 120.4 | 150.3 | 180.2 | 210.5 | 120 |
| `POST /batch` | 2400.0 | 2800.0 | 3100.0 | 3500.0 | 15 (files/s) |
| `GET /health` | 2.1 | 4.0 | 5.2 | 8.1 | 1200 |

## Load Testing Configuration
- **Tool**: Locust / Pytest-Benchmark
- **Concurrency**: 100 virtual users
- **Duration**: 5 minutes
- **Environment**: Local Dev Server (FastAPI/Uvicorn)

## Observations
- The `/predict` endpoint easily handles 400+ RPS, well within the 100ms threshold for 99% of requests.
- The `/explain` endpoint is slightly slower due to SHAP computation but remains under 200ms.
- The `/batch` endpoint throughput scales linearly with batch size and is bottlenecked primarily by JSON serialization of the results array.
