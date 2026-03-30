# TALOS 0.2 Alpha

**TALOS** is a local-first agent console that converts user intent into structured execution plans, waits for approval, and performs safe, file-based actions with visible outputs and full logging.

This project represents an early-stage system focused on controlled agent behavior, not autonomous execution.

---

## 🚀 What TALOS Does

TALOS takes a goal like:

> "Analyze a README and create a summary report"

…and turns it into:

1. A structured execution plan  
2. A user approval checkpoint  
3. Step-by-step execution  
4. A real output file  
5. A full execution log  

---

## 🧠 Core Loop
Goal → Plan → Approve → Execute → Output → Log

This loop is the foundation of TALOS.

---

## ⚙️ Features (0.2 Alpha)

- 🧩 Structured planning (LLM-generated, normalized)  
- 🛑 Approval-gated execution (no auto-run)  
- 📂 Safe file tools (read / write / list)  
- 🧠 Local LLM integration (Ollama)  
- 📄 Output artifacts (written to disk)  
- 📜 Execution logs (step-by-step trace)  
- ⚠️ Honest failure handling (no hidden errors)  

---

## 🏗️ Project Structure
talos/
├── app/
│ ├── main.py
│ ├── agent.py
│ ├── planner.py
│ ├── tools.py
│ ├── models/
│ │ └── ollama_client.py
│ └── core/
│ └── plan_schema.py
├── data/
│ ├── plans/
│ ├── outputs/
│ └── logs/
└── README.md

---

## ▶️ Running TALOS

Activate your environment:

```bash
source venv/bin/activate
Start TALOS:
python3 -m app.main

💻 Example Usage
Generate a plan (no execution)
runplan analyze app/core/README.md and create a summary report --dry

Create and execute a plan
plantask analyze app/core/README.md and create a summary report
approveplan
View latest log
showlog
📁 Outputs

Generated files are saved to:

data/outputs/

Example:

data/outputs/summary_report.md
📜 Logs

Each run creates a timestamped log:

data/logs/run_<timestamp>.log

Logs include:

step-by-step execution
success/failure status
tool outputs
🔒 Safety Model

TALOS is intentionally constrained:

❌ No shell execution
❌ No file deletion
❌ No external system modification
❌ No autonomous looping
✅ Only safe, local file operations
✅ Explicit user approval required
✅ Clear failure reporting
⚠️ Alpha Status

This is TALOS 0.2 Alpha.

Current focus:

correctness
control
transparency

Not yet focused on:

performance
UI/UX polish
multi-agent orchestration
🧭 Roadmap Direction

Planned improvements:

smarter planning constraints
better output naming
plan archiving
richer toolset (still safe)
improved user prompts for missing data
multi-step context chaining
🧠 Philosophy

TALOS is not designed to be:

a fully autonomous agent

It is designed to be:

a controlled execution system that works with the user, not instead of them

🔥 Current State

TALOS 0.2 Alpha is capable of:

reading real files
analyzing real content
generating structured outputs
writing artifacts to disk
logging execution clearly
📌 Summary

TALOS is a foundation system.

It turns:

ideas

into:

structured, executable workflows

with safety, visibility, and control built in from the start.


---

## ✅ How to use it

1. Open your repo root:
   ```bash
   nano README.md
Paste everything above
Save (CTRL+O, ENTER, CTRL+X)
