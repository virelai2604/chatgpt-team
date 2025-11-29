from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from openai import OpenAI, BadRequestError  # openai==2.8.1


# ---------------------------------------------------------------------------
# Model selection and chained call helper
# ---------------------------------------------------------------------------

def choose_test_model(all_models: List[str]) -> str:
    """
    Select a reasonable default chat/reasoning model for capability tests.
    Priority:
      1) OPENAI_TEST_MODEL env var (if present and available)
      2) gpt-4.1-mini
      3) gpt-4.1
      4) gpt-4o
      5) gpt-5.1-chat-latest
      6) gpt-5-chat-latest
      7) first model starting with "gpt-4"
      8) first model in the list
    """
    env_model = os.getenv("OPENAI_TEST_MODEL")
    if env_model and env_model in all_models:
        return env_model

    preferred = [
        "gpt-4.1-mini",
        "gpt-4.1",
        "gpt-4o",
        "gpt-5.1-chat-latest",
        "gpt-5-chat-latest",
    ]
    for m in preferred:
        if m in all_models:
            return m

    for m in all_models:
        if m.startswith("gpt-4"):
            return m

    return all_models[0]


def create_chained_response(
    client: OpenAI,
    *,
    model: str,
    input_text: str,
    tools: Optional[List[Dict[str, Any]]] = None,
    tool_choice: Optional[Any] = "auto",
    previous_response_id: Optional[str] = None,
    max_output_tokens: Optional[int] = None,
) -> Any:
    """
    Helper that wraps client.responses.create and automatically
    passes previous_response_id when provided.
    """
    payload: Dict[str, Any] = {
        "model": model,
        "input": input_text,
    }
    if previous_response_id:
        payload["previous_response_id"] = previous_response_id
    if tools is not None:
        payload["tools"] = tools
        if tool_choice is not None:
            payload["tool_choice"] = tool_choice
    if max_output_tokens is not None:
        payload["max_output_tokens"] = max_output_tokens

    return client.responses.create(**payload)


# ---------------------------------------------------------------------------
# Capability detection with sequential chained Responses
# ---------------------------------------------------------------------------

def detect_capabilities(client: OpenAI) -> Dict[str, Any]:
    """
    Probe OpenAI capabilities for this key, chaining tests via previous_response_id:

      - models list
      - base Responses
      - function tools (schema only, tool_choice="none")
      - web_search tool
      - code_interpreter tool
      - file_search tool (if vector store id provided)
    """
    report: Dict[str, Any] = {}
    chain_sequence: List[Dict[str, Any]] = []
    last_response_id: Optional[str] = None

    # 1) List models
    models_obj = client.models.list()
    all_ids = [m.id for m in models_obj.data]
    report["models"] = all_ids

    test_model = choose_test_model(all_ids)
    report["test_model"] = test_model

    # 2) Base Responses (start of the chain)
    try:
        resp = create_chained_response(
            client,
            model=test_model,
            input_text="Say 'hello' and nothing else.",
            previous_response_id=None,
        )
        last_response_id = resp.id
        report["responses"] = {"status": "ok", "response_id": resp.id}
        chain_sequence.append({"step": "base", "response_id": resp.id})
    except Exception as e:
        report["responses"] = {"status": "error", "error": repr(e)}

    # 3) Function tool (schema test only, tool_choice='none' to avoid unresolved tool calls)
    tools_function = [
        {
            "type": "function",
            "name": "echo",
            "description": "Echo a provided string exactly.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to echo.",
                    }
                },
                "required": ["text"],
            },
        }
    ]
    try:
        resp = create_chained_response(
            client,
            model=test_model,
            input_text="You have an 'echo' tool defined; reply with 'ok'.",
            tools=tools_function,
            tool_choice="none",  # IMPORTANT: do not actually call the function
            previous_response_id=last_response_id,
        )
        last_response_id = resp.id
        report["tools:function"] = {"status": "ok", "response_id": resp.id}
        chain_sequence.append({"step": "function", "response_id": resp.id})
    except BadRequestError as e:
        report["tools:function"] = {"status": "bad_request", "error": str(e)}
    except Exception as e:
        report["tools:function"] = {"status": "error", "error": repr(e)}

    # 4) web_search (chained)
    tools_web_search = [{"type": "web_search"}]
    try:
        resp = create_chained_response(
            client,
            model=test_model,
            input_text=(
                "If web_search is available, use it to answer: capital of France? "
                "Answer in one word only."
            ),
            tools=tools_web_search,
            tool_choice="auto",
            previous_response_id=last_response_id,
            max_output_tokens=32,
        )
        last_response_id = resp.id
        report["tools:web_search"] = {"status": "ok", "response_id": resp.id}
        chain_sequence.append({"step": "web_search", "response_id": resp.id})
    except BadRequestError as e:
        report["tools:web_search"] = {"status": "bad_request", "error": str(e)}
    except Exception as e:
        report["tools:web_search"] = {"status": "error", "error": repr(e)}

    # 5) code_interpreter (chained)
    tools_code_interpreter = [
        {
            "type": "code_interpreter",
            "container": {
                # Minimal container per current docs; adjust if API complains.
                "type": "auto",
            },
        }
    ]
    try:
        resp = create_chained_response(
            client,
            model=test_model,
            input_text=(
                "If you can, use the code_interpreter tool to compute 6*7, "
                "then answer with just the number."
            ),
            tools=tools_code_interpreter,
            tool_choice="auto",
            previous_response_id=last_response_id,
            max_output_tokens=32,
        )
        last_response_id = resp.id
        report["tools:code_interpreter"] = {
            "status": "ok",
            "response_id": resp.id,
        }
        chain_sequence.append({"step": "code_interpreter", "response_id": resp.id})
    except BadRequestError as e:
        report["tools:code_interpreter"] = {
            "status": "bad_request",
            "error": str(e),
        }
    except Exception as e:
        report["tools:code_interpreter"] = {
            "status": "error",
            "error": repr(e),
        }

    # 6) file_search (chained if vector store id present)
    vs_id = os.getenv("OPENAI_TEST_VECTOR_STORE_ID")
    if not vs_id:
        report["tools:file_search"] = {
            "status": "skipped",
            "reason": "OPENAI_TEST_VECTOR_STORE_ID not set",
        }
    else:
        tools_file_search = [
            {
                "type": "file_search",
                "vector_store_ids": [vs_id],
            }
        ]
        try:
            resp = create_chained_response(
                client,
                model=test_model,
                input_text=(
                    "If you can, use file_search to look up any document, then "
                    "answer with a short sentence."
                ),
                tools=tools_file_search,
                tool_choice="auto",
                previous_response_id=last_response_id,
                max_output_tokens=128,
            )
            last_response_id = resp.id
            report["tools:file_search"] = {
                "status": "ok",
                "response_id": resp.id,
            }
            chain_sequence.append({"step": "file_search", "response_id": resp.id})
        except BadRequestError as e:
            report["tools:file_search"] = {
                "status": "bad_request",
                "error": str(e),
            }
        except Exception as e:
            report["tools:file_search"] = {
                "status": "error",
                "error": repr(e),
            }

    report["chain"] = chain_sequence
    return report


# ---------------------------------------------------------------------------
# Tools manifest validation (aligned with app/api/tools_api.py)
# ---------------------------------------------------------------------------

def load_tools_manifest(path: Path) -> List[Dict[str, Any]]:
    """
    Load tools manifest, mirroring app/api/tools_api.py behavior:

      - {"object":"list","data":[...]}
      - {"tools":[...]}
      - [ ... ]
    """
    if not path.is_file():
        raise FileNotFoundError(f"Tools manifest not found at {path}")

    raw = json.loads(path.read_text(encoding="utf-8"))

    if isinstance(raw, dict):
        if "tools" in raw:
            tools = raw["tools"]
        elif raw.get("object") == "list" and "data" in raw:
            tools = raw["data"]
        else:
            tools = raw
    else:
        tools = raw

    if not isinstance(tools, list):
        raise RuntimeError("Invalid tools manifest format; expected list or list-like dict")

    return tools


def extract_model_defaults(tools: List[Dict[str, Any]]) -> set[str]:
    """
    Scan tools for parameters.properties.model.default.
    Collect all default model names referenced by tools.
    """
    models: set[str] = set()
    for tool in tools:
        params = tool.get("parameters", {})
        props = params.get("properties", {})
        model_prop = props.get("model")
        if isinstance(model_prop, dict):
            default_model = model_prop.get("default")
            if isinstance(default_model, str):
                models.add(default_model)
    return models


def validate_tools_manifest(
    models_available: set[str],
    manifest_path: Path,
) -> Dict[str, Any]:
    """
    Compare all default models referenced in tools_manifest.json
    against the actual models available for this API key.
    """
    tools = load_tools_manifest(manifest_path)
    referenced_models = extract_model_defaults(tools)

    checks: Dict[str, str] = {}
    for mid in sorted(referenced_models):
        checks[mid] = "ok" if mid in models_available else "missing"

    return {
        "manifest_path": str(manifest_path),
        "referenced_models": sorted(referenced_models),
        "checks": checks,
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set in environment or .env")

    # IMPORTANT: we test directly against api.openai.com, so we do NOT pass base_url.
    client = OpenAI(api_key=api_key)

    capabilities = detect_capabilities(client)
    models_available = set(capabilities.get("models", []))

    manifest_env = os.getenv("TOOLS_MANIFEST") or os.getenv("TOOLS_MANIFEST_PATH")
    manifest_path = Path(manifest_env) if manifest_env else Path("app/manifests/tools_manifest.json")

    try:
        manifest_validation = validate_tools_manifest(models_available, manifest_path)
    except FileNotFoundError as e:
        manifest_validation = {
            "error": str(e),
            "hint": "Set TOOLS_MANIFEST or TOOLS_MANIFEST_PATH, "
                    "or ensure app/manifests/tools_manifest.json exists.",
        }

    from pprint import pprint

    print("=== FULL CAPABILITIES REPORT (CHAINED) ===")
    pprint(capabilities)

    print("\n=== TOOLS MANIFEST VALIDATION ===")
    pprint(manifest_validation)


if __name__ == "__main__":
    main()
