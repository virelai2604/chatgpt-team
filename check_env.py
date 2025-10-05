from dotenv import load_dotenv
import os

load_dotenv()
models = os.getenv("MODEL_ALLOWLIST", "").split(",")
print("✅ Loaded models:", models)
