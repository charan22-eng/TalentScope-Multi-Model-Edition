# TalentScope Multi-Model Edition: Performance & Latency Telemetry

## 1. Inference Latency & SLAs

All measurements taken on the locked holdout test evaluation (N = 2,381) and single-row micro-benchmarks on Python 3.11 / FastAPI.
The service SLA limit is **p95 latency < 800 ms** for multi-model consensus prediction.

| Model Key | Architecture | Single-Row p50 (ms) | Single-Row p95 (ms) | 5,000-Row Batch (s) | Model Artifact Size (KB) | Memory Footprint (RAM) |
|---|---|---|---|---|---|---|
| `linreg` | Linear Regression (ScoreToBand) | 3.2 | **13.2** | 0.08 | 45 | ~12 MB |
| `dt` | Decision Tree (CART) | 4.1 | **16.3** | 0.11 | 85 | ~14 MB |
| `knn` | K-Nearest Neighbours ($k=15$) | 5.8 | **16.9** | 2.45 | 1,420 | ~48 MB |
| `logreg` | Multinomial Logistic Regression | 5.2 | **22.6** | 0.14 | 52 | ~15 MB |
| `svm` | Support Vector Machine (RBF) | 8.5 | **23.5** | 3.12 | 890 | ~62 MB |
| `rf` | Random Forest (Champion) | 24.1 | **99.4** | 1.85 | 2,450 | ~95 MB |
| `boost` | Histogram Gradient Boosting | 28.5 | **105.8** | 1.20 | 680 | ~45 MB |

### Multi-Model Consensus Route (`POST /api/v2/predict/all`)
- **Combined Sequential Runtime**: ~297 ms (well below 800 ms requirement)
- **Bottlenecks**: Random Forest ensemble tree traversal and Histogram Boosting trees contribute ~68% of the total inference budget.

---

## 2. 3D WebGL Telemetry & Resource Disposal (Stage K)

- **3D Engine**: Three.js v0.186.1 with React-Three-Fiber v9.8.1 and Drei v10.7.9.
- **Client Frame Rate**:
  - `tier="high"`: 60 FPS steady; vertex count capped at 900 for decision landscape mesh (30x30 plane) and 80 spheres for neighbour point cloud.
  - `tier="off"`: 0 FPS (plain HTML/SVG 2D fallback engaged with zero WebGL draw calls).
- **Reduced Motion**: Automatically detects `prefers-reduced-motion: reduce` and renders 2D SVG heatmap fallback to prevent vestibular discomfort.
- **Resource Disposal**: WebGL renderers, geometry buffers, and shader materials are disposed in `SceneFrame.tsx` on component unmount, preventing context loss leaks during route transitions.

---

## 3. Training & Preprocessing Budgets

- **Development Split Training (Fast Profile, Seed 42)**:
  - Linear models (`linreg`, `logreg`): < 2 seconds
  - Tree models (`dt`): < 2 seconds
  - KNN (`knn`): < 1 second (lazy fitting)
  - Ensemble models (`rf`, `boost`): ~8-12 seconds
  - Kernel models (`svm`): ~14 seconds
- **Memory During Preprocessing**: Peak RSS during train Winsorization and imputation is < 180 MB.
