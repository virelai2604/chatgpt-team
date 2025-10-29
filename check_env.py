import os

required = [
    "APP_MODE", "OPENAI_API_KEY", "OPENAI_BASE_URL",
    "RELAY_NAME", "DEFAULT_MODEL", "TOOLS_MANIFEST"
]

print("\n🔍 Environment Validation — ChatGPT Team Relay (Render)\n")

for key in required:
    val = os.getenv(key)
    if val is None:
        print(f"❌ {key}: MISSING")
    elif key == "OPENAI_API_KEY":
        print(f"✅ {key}: [hidden] ({len(val)} chars)")
    else:
        print(f"✅ {key}: {val}")

print("\nEnvironment check complete.\n")
