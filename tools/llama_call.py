import subprocess
import json
import re
from typing import Optional
import shlex


def _extract_json(text: str) -> Optional[str]:
    # find first {...} balanced JSON substring
    # naive approach: find first { and last }
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        candidate = text[start:end+1]
        # try to balance braces more carefully
        # quick validation
        try:
            json.loads(candidate)
            return candidate
        except Exception:
            # fallback: try regex to find JSON-like blocks
            m = re.search(r'\{(?:[^{}]|(?R))*\}', text)
            if m:
                return m.group(0)
    return None


def call_llama_and_parse(binary_path: str, model_path: str, prompt: str, max_tokens: int = 512, threads: int = 4) -> dict:
    """Call llama.cpp binary and attempt to parse JSON from output.

    Returns dict parsed from JSON or raw text under key 'raw'.
    """
    cmd = f"{shlex.quote(binary_path)} -m {shlex.quote(model_path)} -p {shlex.quote(prompt)} -n {max_tokens} -t {threads}"
    try:
        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired:
        return {'error': 'timeout'}
    out = proc.stdout + '\n' + proc.stderr
    js = _extract_json(out)
    if js:
        try:
            return json.loads(js)
        except Exception as e:
            return {'error': 'json_parse_error', 'text': js, 'parse_error': str(e)}
    return {'raw': out}


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--binary', default='./main')
    p.add_argument('--model', required=True)
    p.add_argument('--prompt', required=True)
    p.add_argument('--tokens', type=int, default=512)
    p.add_argument('--threads', type=int, default=4)
    args = p.parse_args()
    res = call_llama_and_parse(args.binary, args.model, args.prompt, args.tokens, args.threads)
    print(json.dumps(res, indent=2, ensure_ascii=False))
