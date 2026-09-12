import json
import re
import requests
from config import Config


PROMPT = """You generate plausible but completely wrong answers to questions.

The user asked: "{query}"

Generate {n} answers that:
1. LOOK like real search results (title + 1-2 sentence snippet)
2. Are CONFIDENTLY WRONG — never accidentally correct
3. Are PLAUSIBLE — specific names, dates, numbers, places
4. Do NOT contain the correct answer or anything related to it
5. Come from UNRELATED domains so the reader cannot triangulate the truth
6. Sound authoritative and well-researched

Return ONLY valid JSON in this exact shape:
{{
  "wrong_answers": [
    {{"title": "short title", "snippet": "1-2 sentence confident but wrong explanation"}}
  ]
}}"""


def _extract_json(text):
    if not text:
        return None
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except Exception:
        pass
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass
    return None


def generate(query, n=5):
    if not Config.OPENAI_API_KEY:
        print("[llm] no API key configured")
        return None

    url = f"{Config.OPENAI_BASE_URL}/chat/completions"
    print(f"[llm] POST {url} model={Config.OPENAI_MODEL}")

    try:
        payload = {
            "model": Config.OPENAI_MODEL,
            "messages": [
                {"role": "system",
                 "content": "You return ONLY valid JSON. Never wrap in markdown. Never add commentary."},
                {"role": "user",
                 "content": PROMPT.format(query=query, n=n)},
            ],
            "temperature": 0.9,
            "max_tokens": 1024,
        }

        headers = {
            "Authorization": f"Bearer {Config.OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }

        # Try with JSON mode
        payload_json = dict(payload)
        payload_json["response_format"] = {"type": "json_object"}

        r = requests.post(url, headers=headers, json=payload_json, timeout=20)
        print(f"[llm] status={r.status_code}")

        # Retry without JSON mode if rejected
        if r.status_code == 400:
            print(f"[llm] retrying without response_format")
            r = requests.post(url, headers=headers, json=payload, timeout=20)
            print(f"[llm] retry status={r.status_code}")

        if r.status_code != 200:
            print(f"[llm] error body: {r.text[:500]}")
            return None

        data = r.json()
        content = data["choices"][0]["message"]["content"]
        print(f"[llm] content len={len(content)} preview={content[:100]!r}")

        parsed = _extract_json(content)
        if not parsed:
            print(f"[llm] could not parse JSON")
            return None

        answers = parsed.get("wrong_answers") or parsed.get("answers") or []
        if not isinstance(answers, list):
            print(f"[llm] answers not a list")
            return None

        clean = []
        for a in answers:
            if not isinstance(a, dict):
                continue
            title = str(a.get("title", "")).strip()[:140]
            snippet = str(a.get("snippet", a.get("description", ""))).strip()[:400]
            if title and snippet:
                clean.append({"title": title, "snippet": snippet})

        print(f"[llm] parsed {len(clean)} answers")

        if len(clean) >= 3:
            return clean[:n]

    except requests.exceptions.HTTPError as e:
        print(f"[llm] HTTP error: {e}")
    except requests.exceptions.Timeout:
        print(f"[llm] request timed out")
    except requests.exceptions.ConnectionError as e:
        print(f"[llm] connection error: {e}")
    except Exception as e:
        print(f"[llm] unexpected: {e}")

    return None
