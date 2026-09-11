import json
import requests
from config import Config


PROMPT = """You generate plausible but completely wrong answers to questions.

The user asked: "{query}"

Generate {n} answers that:
1. LOOK like real search results (bold-looking title + 1-2 sentence snippet)
2. Are CONFIDENTLY WRONG - never accidentally correct
3. Are PLAUSIBLE - include specific names, dates, numbers, places
4. Do NOT contain the correct answer
5. Do NOT reference, hint at, or allude to the correct answer
6. Come from UNRELATED domains so the reader can't triangulate the truth
7. Sound authoritative and well-researched

Return ONLY this exact JSON, no markdown fences:
{{
  "wrong_answers": [
    {{"title": "short title", "snippet": "1-2 sentence confident but wrong explanation"}}
  ]
}}"""


def generate(query, n=5):
    if not Config.OPENAI_API_KEY:
        return None
    try:
        r = requests.post(
            f"{Config.OPENAI_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {Config.OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": Config.OPENAI_MODEL,
                "messages": [
                    {"role": "system",
                     "content": "You return only valid JSON. Never wrap it in markdown."},
                    {"role": "user",
                     "content": PROMPT.format(query=query, n=n)},
                ],
                "temperature": 0.9,
                "response_format": {"type": "json_object"},
            },
            timeout=15,
        )
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        answers = parsed.get("wrong_answers", [])
        if len(answers) >= 3:
            return answers[:n]
    except Exception as e:
        print(f"[llm] failed: {e}")
    return None
