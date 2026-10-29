import sys
from pathlib import Path
import sys
from pathlib import Path
import os
import csv
import time
from llama_cpp import Llama

# -------------------------------------------------------------------------
# Architectural Anchoring: Resolve Paths Relative to this Script File
# -------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent          # C:\AI-Powered-Helpdesk-GateKeeper\phase2_local
PROJECT_ROOT = SCRIPT_DIR.parent                      # C:\AI-Powered-Helpdesk-GateKeeper
DATA_PATH = PROJECT_ROOT / "data" / "evaluation_tickets.csv"
MODEL_PATH = PROJECT_ROOT / "models" / "qwen2.5-1.5b-instruct-q4_k_m.gguf"

# Add repository root to sys.path so 'schema.py' can be imported cleanly
sys.path.append(str(PROJECT_ROOT))

from schema import TicketEvaluation

# 1. Hardware & Engine Setup (Using Fully Resolved String Path for C++)
print(f"Loading GGUF engine on CPU: {MODEL_PATH}")
t_start_load = time.perf_counter()
llm = Llama(
    model_path=str(MODEL_PATH),   # str() ensures safe conversion for C++ ctypes
    n_ctx=2048,
    n_threads=8,
    verbose=False
)
print(f"Engine ready in {time.perf_counter() - t_start_load:.2f}s.\n")


# Alias mapping between CSV test labels and our strict Pydantic Enums
SYSTEM_ALIAS_MAP = {
    "Entra ID": "Active Directory / Entra ID",
    "OpenText EDI": "EDI Gateway (OpenText)"
}


# 2. Calibrated Bouncer Instructions with Few-Shot Negative Anchors
SYSTEM_INSTRUCTION = (
    "You are the Enterprise Tier-0 Ticket Classifier and Quality Bouncer for COMPANY XYZ.\n\n"
    "CRITICAL BOUNCER CRITERIA:\n"
    "A ticket is ONLY actionable (is_actionable=True) if it explicitly specifies BOTH:\n"
    "1. A named enterprise application or identifiable technical component.\n"
    "2. A concrete error message, transaction code, or technical artifact (e.g., PO number, user ID, error code).\n\n"
    "If a ticket only contains emotions, complaints, generic statements ('system broken', 'everything blocked', 'cannot work'), "
    "or does not name the exact system: You MUST set is_actionable=False, target_system='UNKNOWN', and assigned_queue='BOUNCE_QUEUE'.\n\n"
    "Examples of NON-ACTIONABLE tickets:\n"
    "- 'URGENT!!! Everything is blocked. Call me ASAP.' -> is_actionable: false, target_system: UNKNOWN, assigned_queue: BOUNCE_QUEUE\n"
    "- 'Error message on screen. Cannot continue.' -> is_actionable: false, target_system: UNKNOWN, assigned_queue: BOUNCE_QUEUE\n"
    "- 'System broken again. Same as last time.' -> is_actionable: false, target_system: UNKNOWN, assigned_queue: BOUNCE_QUEUE\n"
    "- 'Purchase request approved yesterday but supplier cannot see order.' -> is_actionable: false, target_system: UNKNOWN, assigned_queue: BOUNCE_QUEUE\n\n"
    "Routing Catalog (ONLY when is_actionable=True):\n"
    "- SAP S/4HANA (MIGO, FI-CO, MM, SD) -> target_system: 'SAP S/4HANA', assigned_queue: 'L2_SAP_FINANCE'\n"
    "- SAP SuccessFactors (Payroll, HR) -> target_system: 'SAP SuccessFactors', assigned_queue: 'L2_HR_SERVICES'\n"
    "- Entra ID / Active Directory / Passwords -> target_system: 'Active Directory / Entra ID', assigned_queue: 'L1_ACCESS'\n"
    "- Microsoft 365 (Outlook, Teams, Excel) -> target_system: 'Microsoft 365', assigned_queue: 'L3_MICROSOFT_INCIDENTS'\n"
    "- ServiceNow catalog items -> target_system: 'ServiceNow', assigned_queue: 'L2_ITSM_SUPPORT'\n"
    "- Siemens Teamcenter (PLM/CAD) -> target_system: 'Siemens Teamcenter', assigned_queue: 'L2_PLM_SUPPORT'\n"
    "- CATIA V6 -> target_system: 'CATIA V6', assigned_queue: 'L2_CATIA_SUPPORT'\n"
    "- Polarion ALM -> target_system: 'Polarion ALM', assigned_queue: 'L2_ALM_SUPPORT'\n"
    "- Opcenter MES -> target_system: 'Opcenter MES', assigned_queue: 'L2_MES_SERVICE'\n"
    "- Ignition SCADA -> target_system: 'Ignition SCADA', assigned_queue: 'L2_MES_SERVICE'\n"
    "- Power BI -> target_system: 'Power BI', assigned_queue: 'L2_DATA_HUB'\n"
    "- EDI Gateway (OpenText / IDocs) -> target_system: 'EDI Gateway (OpenText)', assigned_queue: 'L2_EDI'\n\n"
    "Invariants:\n"
    "- If is_actionable is False: target_system MUST be 'UNKNOWN' and assigned_queue MUST be 'BOUNCE_QUEUE'.\n"
    "- If is_actionable is True: assigned_queue MUST NOT be 'BOUNCE_QUEUE'."
)


# 3. CSV Dataset Ingestion
def load_dataset(file_path):
    with open(file_path, mode="r", encoding="utf-8-sig") as f:
        sample = f.read(2048)
        delimiter = ";" if ";" in sample else ","
        f.seek(0)
        reader = csv.DictReader(f, delimiter=delimiter)
        return list(reader)

records = load_dataset(DATA_PATH)
print(f"Loaded {len(records)} test tickets from {DATA_PATH.name}.\n")


# 4. Evaluation Loop
results = []
total_tokens = 0
total_infer_time = 0.0
correct_actionable = 0
correct_system = 0

print("=" * 80)
print(f"{'#':<3} | {'Archetype':<12} | {'Act (Pred/Exp)':<15} | {'System (Pred/Exp)':<32} | {'Status'}")
print("=" * 80)

for idx, row in enumerate(records, start=1):
    ticket_text = row["raw_ticket_text"]
    archetype = row["archetype"]
        
    expected_act_str = str(row["expected_actionable"]).strip().upper()
    expected_actionable = expected_act_str in ["WAAR", "TRUE", "1", "YES"]
    
    expected_system_raw = row.get("expected_target_system", "").strip()
    clean_expected_system = SYSTEM_ALIAS_MAP.get(expected_system_raw, expected_system_raw)

    # 1. Run local SLM inference
    t0 = time.perf_counter()
    response = llm.create_chat_completion(
        messages=[
            {"role": "system", "content": SYSTEM_INSTRUCTION},
            {"role": "user", "content": ticket_text}
        ],
        response_format={
            "type": "json_object",
            "schema": TicketEvaluation.model_json_schema()
        },
        temperature=0.0,
        max_tokens=256
    )
    dt = time.perf_counter() - t0

    usage = response["usage"]
    completion_tokens = usage["completion_tokens"]
    total_tokens += completion_tokens
    total_infer_time += dt

    # 2. Pydantic validation (Instantiates 'pred')
    raw_json = response["choices"][0]["message"]["content"]
    pred = TicketEvaluation.model_validate_json(raw_json)

    # 3. Ground truth evaluation (Now 'pred' is available!)
    act_match = (pred.is_actionable == expected_actionable)
    sys_match = (pred.target_system.value == clean_expected_system)

    if act_match:
        correct_actionable += 1
    if sys_match:
        correct_system += 1

    status = "OK" if (act_match and sys_match) else "MISMATCH"
    
    pred_act_str = f"{pred.is_actionable}/{expected_actionable}"
    pred_sys_str = f"{pred.target_system.value[:14]}/{clean_expected_system[:14]}"
    print(f"[{idx:02d}] {archetype:<12} | {pred_act_str:<15} | {pred_sys_str:<32} | {status} ({dt:.2f}s)")

# 5. Summary Metrics
print("=" * 80)
print("PHASE 2 LOCAL EVALUATION SUMMARY")
print("-" * 80)
print(f"Total Tickets:            {len(records)}")
print(f"Actionable Gate Accuracy: {correct_actionable}/{len(records)} ({correct_actionable/len(records)*100:.1f}%)")
print(f"System Match Accuracy:    {correct_system}/{len(records)} ({correct_system/len(records)*100:.1f}%)")
print(f"Total Infer Time:         {total_infer_time:.2f} seconds")
print(f"Avg Latency per Ticket:   {total_infer_time/len(records):.2f} seconds")
print(f"Avg Throughput:           {total_tokens/total_infer_time:.2f} tokens/second")
print("=" * 80)