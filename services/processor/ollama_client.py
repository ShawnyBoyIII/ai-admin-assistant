import json
import os
import urllib.error
import urllib.request
from typing import Dict, Any, Optional

def query_ollama(prompt: str, json_format: bool = True) -> Optional[Dict[str, Any]]:
    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3")
    timeout_seconds = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "20"))

    data = {
        "model": ollama_model,
        "prompt": prompt,
        "stream": False,
        "options": {
             "temperature": 0.2
        }
    }

    if json_format:
        data["format"] = "json"

    req = urllib.request.Request(
        ollama_url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as response:
            result = json.loads(response.read().decode("utf-8"))
            if "response" in result:
                if json_format:
                    return json.loads(result["response"])
                else:
                    return {"text": result["response"]}
            return None
    except urllib.error.HTTPError as exc:
        print(f"Error querying Ollama (HTTP {exc.code}): {exc}")
        return None
    except urllib.error.URLError as exc:
        print(f"Error querying Ollama (network): {exc}")
        return None
    except Exception as exc:
        print(f"Error querying Ollama: {exc}")
        return None
