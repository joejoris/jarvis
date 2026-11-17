"""Live translation via the LLM you're already paying zero for."""


def translate(text: str, target_lang: str, source_lang: str = "auto") -> str:
    from backend.brain import llm  # lazy: avoids tools <-> brain import cycle
    src = f"from {source_lang}" if source_lang != "auto" else "auto-detect the source language and"
    prompt = (f"Translate the following {src} into {target_lang}. "
              f"Reply with ONLY the translation — no explanations, no quotes, no notes.\n\n{text}")
    result = llm._chat([{"role": "user", "content": prompt}])
    return (result.get("content") or "").strip() or "Translation failed."
