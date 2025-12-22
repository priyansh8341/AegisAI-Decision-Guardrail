README.TXT
AegisAI – Decision Guardrail Agent

==================================================
OVERVIEW
==================================================
AegisAI is an autonomous AI Decision Guardrail Agent designed to evaluate
proposed business or technical decisions BEFORE execution and predict risks,
second-order effects, and mitigation strategies.

This project demonstrates how Large Language Models (LLMs) can be used as
reasoning engines for decision safety and governance, not just chat or
summarization.

==================================================
PREREQUISITES
==================================================
1. Python 3.9 or higher
2. Ollama installed
3. Internet access (for first-time model download)

==================================================
INSTALL DEPENDENCIES
==================================================
Open a terminal in the project folder and run:

python -m pip install fastapi uvicorn requests

==================================================
START THE LLM (OLLAMA)
==================================================
Start the local LLM runtime:

ollama run llama3

Keep this terminal running in the background.

==================================================
START THE SERVER
==================================================
In a new terminal window, navigate to the project directory and run:

python -m uvicorn server:app --reload

You should see:
Uvicorn running on http://127.0.0.1:8000

==================================================
OPEN THE WEB INTERFACE
==================================================
Open your browser and go to:

http://127.0.0.1:8000

==================================================
USING THE APPLICATION
==================================================
1. Load one of the preset decision scenarios or paste your own decision.
2. Click "Assess Risk".
3. Review the risk level, score, recommendation, and guardrails.
4. Use the control panel to simulate decision outcomes.

==================================================
STOPPING THE APPLICATION
==================================================
- Stop the server: Ctrl + C
- Stop Ollama: Ctrl + C in the Ollama terminal

==================================================
TROUBLESHOOTING
==================================================
- If the page loads but no output appears, ensure Ollama is running.
- If imports fail, re-run the pip install command.
- If port 8000 is busy, stop other servers or change the port.

==================================================
DISCLAIMER
==================================================
This project is for demonstration and educational purposes only.
It does not provide financial, legal, or operational advice.
