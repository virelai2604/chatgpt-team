import json

ALLOWED_TOOL_TYPES = {
    "file_search",
    "retrieval",
    "code_interpreter",
    "web_search",
    "image_generation",
    "function",
    "browser"  # org/beta only
}

def validate_tool_payload(payload, org_mode=False):
    if not isinstance(payload, dict):
        return False, "Payload must be a JSON object"
    ttype = payload.get("type")
    if not ttype:
        return False, "Missing 'type' in tool registration"
    if ttype not in ALLOWED_TOOL_TYPES:
        return False, f"Unknown tool type '{ttype}'"
    if ttype == "browser" and not org_mode:
        return False, "Tool type 'browser' is org/beta only (set org_mode=True to allow)"
    if ttype == "function":
        fn = payload.get("function")
        if not fn or not isinstance(fn, dict):
            return False, "Tool type 'function' must include a 'function' object"
        if not fn.get("name"):
            return False, "Function tool must specify 'name'"
        if not fn.get("description"):
            return False, "Function tool must specify 'description'"
        if not isinstance(fn.get("parameters"), dict):
            return False, "Function tool must specify 'parameters' as an object"
    return True, None

if __name__ == "__main__":
    # Load the array of tool registrations
    with open("all_tools.json", "r", encoding="utf-8") as f:
        payloads = json.load(f)

    for idx, payload in enumerate(payloads, 1):
        # org_mode is True ONLY for browser tool
        org_mode = payload.get("type") == "browser"
        is_valid, error = validate_tool_payload(payload, org_mode=org_mode)
        print(f"\n--- Tool #{idx}: type = {payload.get('type')} ---")
        print(json.dumps(payload, indent=2))
        print("Valid:", is_valid)
        if error:
            print("Error:", error)
        else:
            print("No errors.")
