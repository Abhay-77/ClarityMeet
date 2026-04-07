import os
import requests

CF_API_BASE = "https://api.cloudflare.com/client/v4/accounts"


def _get_headers():
    token = os.getenv("CF_API_TOKEN", "")
    if not token:
        raise RuntimeError("CF_API_TOKEN is not set")
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def _run_model(model: str, payload: dict):
    account_id = os.getenv("CF_ACCOUNT_ID", "")
    if not account_id:
        raise RuntimeError("CF_ACCOUNT_ID is not set")

    url = f"{CF_API_BASE}/{account_id}/ai/run/{model}"
    response = requests.post(url, headers=_get_headers(), json=payload, timeout=60)
    response.raise_for_status()
    data = response.json()

    if not data.get("success", True):
        raise RuntimeError(f"Cloudflare AI error: {data}")

    return data.get("result", {})


def chat(messages: list[dict], model: str):
    result = _run_model(model, {"messages": messages})
    if isinstance(result, dict) and "response" in result:
        return result["response"]
    return ""


def embed(text: str, model: str) -> list[float]:
    result = _run_model(model, {"text": text})
    if "data" in result and result["data"]:
        return result["data"][0].get("embedding", [])
    if "embedding" in result:
        return result["embedding"]
    return []
