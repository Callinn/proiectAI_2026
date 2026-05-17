# Ollama local setup (Windows) — recommended for Clinical Trial Radar

Scop: folosește Ollama local runtime cu modelul `mistral` pentru a genera planuri JSON deterministe. Agentul rămâne planner/orchestrator; calculele și analytics se fac în Python.

## 1) Install Ollama
- Instalează aplicația Ollama pentru Windows.
- Verifică că serviciul rulează local la `http://localhost:11434`.

## 2) Pull model

```powershell
ollama pull mistral
ollama list
```

## 3) Python integration

Install client:

```bash
pip install ollama
```

Example:

```python
import ollama

response = ollama.chat(
    model='mistral',
    messages=[
        {
            'role': 'system',
            'content': 'Return valid JSON only.'
        },
        {
            'role': 'user',
            'content': 'Analyze phase 3 diabetes trials'
        }
    ],
    options={
        'temperature': 0.0,
        'top_p': 1.0
    },
    format='json'
)

print(response['message']['content'])
```

## 4) Agent usage
- The project agent uses Ollama as a local planner when `use_llm=True`.
- Set `OLLAMA_MODEL=mistral` if you want to override the default.

```python
from ct_radar import Agent

agent = Agent(llm_provider='ollama', model='mistral')
report = agent.run('Analyze phase 3 diabetes trials and produce a snapshot', use_llm=True)
print(report)
```

## 5) Notes
- Keep `temperature=0.0` or `0.1` for deterministic JSON plans.
- If JSON is malformed, the agent falls back to rule-based planning.
- Do not manually compile `llama.cpp`; use Ollama instead.
