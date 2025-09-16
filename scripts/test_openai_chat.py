import os
import sys
from pathlib import Path


# Ensure project root for `src` imports
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from openai import OpenAI
from src.config.settings import settings


def main() -> None:
    api_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        print("OPENAI_API_KEY not found in settings or env.")
        sys.exit(1)

    client = OpenAI(api_key=api_key)
    q = "Say 'hello' in one short sentence."
    print(f"Asking: {q}")
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": q}],
            temperature=0.2,
            max_tokens=20,
        )
        print("Response:", resp.choices[0].message.content)
    except Exception as e:
        print("OpenAI request failed:", e)
        sys.exit(2)


if __name__ == "__main__":
    main()


