import sys
from pathlib import Path

# Explicitly add repository root to Python module search path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import os
import pandas as pd
from dotenv import load_dotenv

# -------------------------------------------------------------------------
# Architectural Anchoring: Resolve Paths Relative to this Script File
# -------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent          # C:\AI-Powered-Helpdesk-GateKeeper\phase1_cloud
PROJECT_ROOT = SCRIPT_DIR.parent                      # C:\AI-Powered-Helpdesk-GateKeeper
DATA_PATH = PROJECT_ROOT / "data" / "evaluation_tickets.csv"

# Add repository root to sys.path so 'schema.py' can be imported cleanly
sys.path.append(str(PROJECT_ROOT))


from google import genai
from google.genai import types
from schema import TicketEvaluation

# Automatically loads key-value pairs from .env into the runtime environment
load_dotenv()

# Client automatically reads GEMINI_API_KEY from environment variables
client = genai.Client()

SYSTEM_PROMPT = """
You are the Enterprise Tier-0 Ticket Classifier and Quality Bouncer for COMPANY XYZ.
Evaluate incoming raw user support tickets.

Rules:
1. If the ticket lacks sufficient technical context, application name, or reproduction steps, set is_actionable=False, assign target_system=UNKNOWN, assigned_queue=BOUNCE_QUEUE, and provide clear missing_fields and bounce_reason.
2. If actionable, identify the exact target_system and map to the correct assigned_queue based on whether it is an Access issue, Service Request, or Incident.
"""

# 2. Robust Ingestion: Handle Semicolon Delimiter & Locale Normalization
# sep=';' ensures clean parsing of European CSV exports
df = pd.read_csv(DATA_PATH, sep=";")

# Clean column headers
df.columns = df.columns.str.strip()

print(f"Successfully loaded {len(df)} test cases. Columns: {list(df.columns)}\n")

# 3. Execution & Evaluation Loop
correct_actionable_count = 0
total_cases = len(df)

for idx, row in df.iterrows():
    ticket_id = row["id"]
    archetype = row["archetype"]
    text = row["raw_ticket_text"]

    # Locale normalization: Handles TRUE/FALSE as well as WAAR/ONWAAR
    raw_expected_act = str(row["expected_actionable"]).strip().upper()
    expected_act = raw_expected_act in ["TRUE", "WAAR", "1"]

    expected_sys = str(row["expected_target_system"]).strip()

    # Call Current Gemini 3.6 Flash Endpoint
    response = client.models.generate_content(
        model="gemini-3.6-flash",  # <--- Update from gemini-2.5-flash
        contents=f"Incoming Ticket: {text}",
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=TicketEvaluation,
            temperature=0.0,
        ),
    )

    eval_result: TicketEvaluation = response.parsed

    # Benchmark against Ground Truth
    act_match = eval_result.is_actionable == expected_act
    if act_match:
        correct_actionable_count += 1

    print(
        f"[{ticket_id:02d}] {archetype.upper():<10} | Actionable: {str(eval_result.is_actionable):<5} "
        f"(Match: {'✓' if act_match else '✗'}) | Target: {eval_result.target_system.value} | Queue: {eval_result.assigned_queue.value}"
    )

    if not eval_result.is_actionable:
        print(f"     ↳ Bounce Reason: {eval_result.bounce_reason}")
        print(f"     ↳ Missing: {eval_result.missing_fields}")
    print("-" * 75)

print(
    f"\nBouncer Accuracy: {correct_actionable_count}/{total_cases} ({(correct_actionable_count/total_cases)*100:.1f}%)"
)