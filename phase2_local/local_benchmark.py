import time
import os
from llama_cpp import Llama

# 1. Model Configuration
MODEL_PATH = os.path.join("models", "qwen2.5-1.5b-instruct-q4_k_m.gguf")

print(f"Loading GGUF model from: {MODEL_PATH}")
start_load = time.perf_counter()

# n_threads=8 leverages the performance cores of your i7-12700
llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=2048,
    n_threads=8,
    verbose=False
)

load_time = time.perf_counter() - start_load
print(f"Model loaded into RAM in {load_time:.2f} seconds.\n")

# 2. Test Input: Actionable Ticket #1 from your test set
PROMPT = """<|im_start|>system
You are the Tier-0 Ticket Classifier and Quality Bouncer for COMPANY XYZ.
Evaluate this ticket: 'Unable to post Goods Receipt in SAP S/4HANA. Transaction MIGO returns error Deficit of stock in transit. PO 4500187421 affected.'
Output a concise JSON summary indicating actionable status, target system, and queue.<|im_end|>
<|im_start|>assistant
"""

# 3. Execution & Performance Timing
print("Running local CPU inference benchmark...")
start_eval = time.perf_counter()

output = llm(
    PROMPT,
    max_tokens=128,
    temperature=0.0,
    stop=["<|im_end|>"]
)

eval_time = time.perf_counter() - start_eval

# 4. Extract Performance Metrics
generated_text = output["choices"][0]["text"].strip()
prompt_tokens = output["usage"]["prompt_tokens"]
completion_tokens = output["usage"]["completion_tokens"]
tokens_per_second = completion_tokens / eval_time

print("-" * 60)
print(f"Generated Response:\n{generated_text}")
print("-" * 60)
print(f"Latency (Time to Complete): {eval_time:.2f} seconds")
print(f"Prompt Tokens:              {prompt_tokens}")
print(f"Completion Tokens:          {completion_tokens}")
print(f"Throughput (Speed):         {tokens_per_second:.2f} tokens/second")
print("-" * 60)