#!/usr/bin/env python3
"""
Delega una tarea "pesada" (mucho texto/tokens) a la API de DeepSeek en vez de
gastar tokens del asistente principal. Uso:

    python scripts/deepseek_delegate.py "resume este log" < archivo_grande.log
    python scripts/deepseek_delegate.py --file entrada.txt "explica este codigo"
    echo "texto largo..." | python scripts/deepseek_delegate.py "traduce al ingles"

Lee la API key de DEEPSEEK_API_KEY (variable de entorno o archivo .env en la
raiz del proyecto). No requiere dependencias externas (solo stdlib).
"""
import argparse
import json
import os
import sys
import urllib.request
import urllib.error


def load_env_file(path):
    if not os.path.isfile(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


def main():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    load_env_file(os.path.join(project_root, ".env"))

    parser = argparse.ArgumentParser(description="Delegar una tarea a DeepSeek")
    parser.add_argument("prompt", help="Instruccion para DeepSeek")
    parser.add_argument("--file", help="Archivo con contenido a adjuntar (si no, se lee stdin si hay pipe)")
    parser.add_argument("--model", default="deepseek-chat", help="deepseek-chat o deepseek-reasoner")
    parser.add_argument("--max-tokens", type=int, default=8192)
    args = parser.parse_args()

    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print("ERROR: falta DEEPSEEK_API_KEY (variable de entorno o .env)", file=sys.stderr)
        sys.exit(1)
    base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

    content = args.prompt
    payload_text = None
    if args.file:
        with open(args.file, "r", encoding="utf-8", errors="replace") as f:
            payload_text = f.read()
    elif not sys.stdin.isatty():
        payload_text = sys.stdin.read()

    if payload_text:
        content = f"{args.prompt}\n\n---\n{payload_text}"

    body = json.dumps({
        "model": args.model,
        "messages": [{"role": "user", "content": content}],
        "max_tokens": args.max_tokens,
        "stream": False,
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"ERROR HTTP {e.code}: {e.read().decode('utf-8', errors='replace')}", file=sys.stderr)
        sys.exit(1)

    print(result["choices"][0]["message"]["content"])


if __name__ == "__main__":
    main()
