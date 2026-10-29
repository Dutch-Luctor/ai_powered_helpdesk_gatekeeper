# AI-Powered Helpdesk GateKeeper (Proof of Concept)

> **Deterministic, schema-governed intake and quality gatekeeping of IT support tickets.**
> *Comparative architecture: Frontier Cloud APIs (Phase 1) vs. Quantized Small Language Models (SLM) on Local CPU Hardware (Phase 2).*

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Pydantic v2](https://img.shields.io/badge/Pydantic-v2-green.svg)](https://docs.pydantic.dev/)
[![llama.cpp](https://img.shields.io/badge/Engine-llama.cpp%20(AVX2)-orange.svg)](https://github.com/ggerganov/llama.cpp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

- - -

# # 1. Executive Summary & Problem Statement

In enterprise IT and ERP operations, helpdesks suffer from severe intake friction. End-users regularly submit incomplete, ambiguous, or emotional tickets (e.g., *"System broken, fix ASAP"* or *"Scanner failed at station 6"*).

This friction creates two distinct operational cost centers:

* **(A) Technician Triage Friction:** IT engineers spend 15–30% of their day reviewing incomplete tickets and chasing users for basic diagnostic parameters.
* **(B) The Asynchronous Cost of Delay (CoD):** When an engineer asks a clarifying question, the ticket drops into an asynchronous waiting state. A 5-minute intake issue often stalls for **hours or days (1–40+ business hours)** before becoming actionable—stalling month-end closes, supply chain shipments, or invoice postings.

### The Solution: a Ticket Quality (Level-0) Gatekeeper
An automated pre-ingestion AI powered middleware layer that inspects tickets before they enter the queue:
* **Quality Gate:** If mandatory technical context (system name, error message, transaction code, PO/user ID) is missing, the ticket is rejected immediately at the UI layer with targeted disambiguation feedback.
* **Deterministic Routing:** Actionable tickets are classified and routed to the correct specialist queue via strict schema invariants.
* **Zero-Egress Local Option:** Can execute 100% air-gapped on commodity enterprise CPUs using quantized open-weight SLMs.

- - -

# # 2. Architecture & The Decoupled Data Contract

The pipeline enforces a strict **Single Source of Truth** using Pydantic v2:

```text
               [ Incoming User Ticket (Free Text) ]
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│    Pydantic Contract (schema.py): Enums & Invariants        │
│  - TargetSystem: SAP S/4HANA, ServiceNow, Entra ID, etc.    │
│  - SupportQueue: L1_ACCESS, L2_SAP_FINANCE, BOUNCE_QUEUE    │
└──────────────────────────────┬──────────────────────────────┘
                               │
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
┌────────────────────────┐           ┌────────────────────────┐
│  Phase 1: Cloud API    │           │  Phase 2: On-Prem SLM  │
│  (Gemini 3.6 Flash)    │           │  (Qwen 2.5 1.5B GGUF)  │
│  Server-side JSON-mode │           │  Native C++ GBNF Mask  │
└────────────────────────┘           └────────────────────────┘
```

By decoupling the data contract (schema.py) from the inference runtime, the underlying model can be swapped between managed cloud endpoints and local silicon without altering downstream business integrations.

- - -

# # 3. Empirical Benchmark Results (30 Enterprise Cases)
Evaluation was conducted against a golden dataset of 30 enterprise test tickets spanning three archetypes:
Actionable (12), Ambiguous (9), and Incomplete (9).

```text
Performance Metric          Phase 1: Cloud API (Gemini 3.6 Flash)   Phase 2: Local SLM (Qwen 2.5 1.5B Q4_K_M)
- -------------------------------------------------------------------------------------------------------------
Compute Hardware            Managed Cloud TPU                       Intel Core i7-12700 (8 Threads, AVX2)
Data Egress / Privacy       External API Payload                    100% On-Premise / Air-Gapped
Actionable Gate Accuracy    30 / 30 (100.0%)                        26 / 30 (86.7%)
System Match Accuracy       30 / 30 (100.0%)                        29 / 30 (96.7%)
Average Latency             ~0.90s (Network Dependent)              1.34s (Deterministic Local)
Inference Throughput        Managed Stream                          ~21–33 tokens/second
Marginal Compute Cost       Pay-per-token API tier                  $0.00 (Zero marginal compute OpEx)
```

Key Engineering Takeaways:
- Grammar Masking is Mandatory: Without GBNF grammar constraints, small models invent arbitrary, non-existent queue names.
- Calibrating Rejection: Small models exhibit "eager helpfulness"; negative few-shot anchors lifted accuracy from 50.0% to 86.7%.

- - -

# # 4. Repository Structure
```Plaintext
├── data/
│   └── evaluation_tickets.csv # 30-case validation dataset
├── phase1_cloud/
│   ├── run_eval.py            # Gemini 3.6 Flash evaluation harness (dotenv-enabled)
│   └── requirements.txt       # Cloud dependencies (google-genai, python-dotenv, pandas)
├── phase2_local/
│   ├── run_local_eval.py      # Local SLM evaluation harness (llama.cpp)
│   ├── local_benchmark.py     # Micro-benchmark for hardware CPU validation
│   └── requirements.txt       # Local dependencies (llama-cpp-python, pydantic)
├── docs/                      # Architectural deep dives & hardware logs
└── .gitignore                 # Excludes models/*.gguf, .venv/, .idea/, .env
```

- - -

# # 5. Quickstart
Use either the provided contract (`schema.py`), and the golden dataset of 30 enterprise ficticious test tickets.
Or, modify the schema to match your own applications and support queues, and use historic, archived helpdesk tickets.

### Prerequisites

Clone the repository and set up your virtual environment:
```bash
git clone https://github.com/Dutch-Luctor/AI-Powered-Helpdesk-GateKeeper.git

cd AI-Powered-Helpdesk-GateKeeper

python -m venv .venv
```

Activate the environment:
```text
Windows: .venv\Scripts\activate

Linux/macOS: source .venv/bin/activate
```

Option A: Run Phase 1 (Cloud API)
1. Install cloud requirements:
``` bash
pip install -r phase1_cloud/requirements.txt
```

2. Create a .env file in the root directory:
```text
GEMINI_API_KEY=your_actual_api_key_here
```

3. Run the evaluation harness:
```bash
python phase1_cloud/run_eval.py
```

Option B: Run Phase 2 (Local SLM on CPU)
1. Install local inference requirements:
```bash
pip install -r phase2_local/requirements.txt
```

Note: If installing on Windows without C++ compilers, requirements.txt 
automatically fetches pre-compiled CPU wheels with AVX2 support via the official wheels repository.

- - -

### Verification Step

1. Run the command in your terminal:
```cmd
pip install llama-cpp-python --prefer-binary --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
```

Once installed, test if Python can load the C-bindings cleanly:
```bash
python -c "import llama_cpp; print('llama-cpp-python loaded successfully!')"
```
- - -

2. Download the 4-bit quantized GGUF model (~1.12 GB):
Download the official 4-bit quantized GGUF model and place it directly into the `models/` directory:

* **Hugging Face Repository:** [Qwen/Qwen2.5-1.5B-Instruct-GGUF](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF)
* **Target File:** `qwen2.5-1.5b-instruct-q4_k_m.gguf`
* **Direct Path:** `models/qwen2.5-1.5b-instruct-q4_k_m.gguf`

**Quick Download via Terminal:**

*On Windows (PowerShell):*
```powershell
mkdir -p models
Invoke-WebRequest -Uri "[https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf)" -OutFile "models/qwen2.5-1.5b-instruct-q4_k_m.gguf"
```

*On Linux / macOS (curl):*
```bash
mkdir -p models
curl -L -o models/qwen2.5-1.5b-instruct-q4_k_m.gguf "[https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf)"
```

3. Run the local batch evaluation harness:
```bash
python phase2_local/run_local_eval.py
```

# # 6. Acknowledgments & License
Prototyping & Architecture: Developed and benchmarked with the assistance of Google Gemini (Gemini 3.6 Flash / Advanced).

License: Distributed under the MIT License. See LICENSE for details.





