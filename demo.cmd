@echo off
rem The relation gate demo, in a browser on this PC. Needs Python 3 with sympy; the "ask" buttons need Ollama running.
start "" http://localhost:8765
python "%~dp0demo\server.py"
