import json
import os
import urllib.request
from typing import Dict, Any, Optional

def query_ollama(prompt: str, json_format: bool = True) -> Optional[Dict[str, Any]]:
    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3")

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
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            if "response" in result:
                if json_format:
                    return json.loads(result["response"])
                else:
                    return {"text": result["response"]}
            return None
    except Exception as e:
        print(f"Error querying Ollama: {e}")
        return None
