"""JARVIS brain. Backends: groq (fast cloud, OpenAI-compatible) or ollama (local)."""
import json
import requests
from backend import config
from backend.memory import store
from backend.tools import TOOLS, dispatch
from backend.brain import router as kw_router

CFG = config.CONFIG
LLM = CFG["llm"]
PERSONA = CFG["assistant"]["persona"]


def _is_groq() -> bool:
    return LLM.get("provider") == "groq"


def _groq_cfg():
    return LLM.get("groq", {})


def _system_prompt() -> str:
    from datetime import datetime
    facts = store.all_facts()
    mem = ("\nKnown facts about the user:\n" + "\n".join(f"- {f}" for f in facts)) if facts else ""
    now = datetime.now().strftime("It is %A, %d %B %Y, %H:%M local time.")
    return (PERSONA +
            f"\nCurrent date and time: {now}. Use this exact date/time whenever asked.\n" +
            mem)


def _parse_args(args):
    if isinstance(args, str):
        try:
            return json.loads(args)
        except json.JSONDecodeError:
            return {}
    return args or {}


# ---------- backend primitives ----------

def _ollama_chat(messages, tools=None):
    payload = {"model": LLM["model"], "messages": messages, "stream": False,
               "options": {"temperature": LLM.get("temperature", 0.7),
                           "num_ctx": LLM.get("num_ctx", 4096)}}
    if tools:
        payload["tools"] = tools
    r = requests.post(f"{LLM['host']}/api/chat", json=payload, timeout=300)
    r.raise_for_status()
    return r.json()["message"]


def _groq_chat(messages, tools=None):
    g = _groq_cfg()
    payload = {"model": g["model"], "messages": messages,
               "temperature": LLM.get("temperature", 0.7),
               "max_tokens": LLM.get("max_tokens", 400)}
    if tools:
        payload["tools"] = tools
    r = requests.post(f"{g['base_url']}/chat/completions", json=payload,
                      headers={"Authorization": f"Bearer {g['api_key']}"}, timeout=120)
    if r.status_code != 200:
        raise RuntimeError(f"Groq {r.status_code}: {r.text[:300]}")
    return r.json()["choices"][0]["message"]


def _chat(messages, tools=None):
    if _is_groq():
        try:
            return _groq_chat(messages, tools)
        except Exception as e:
            print(f"Groq failed ({e}); falling back to local Ollama")
            return _ollama_chat(messages, None)  # strip tools: exceeds small ctx/window
    return _ollama_chat(messages, None)


def _groq_stream(messages, tools=None):
    g = _groq_cfg()
    payload = {"model": g["model"], "messages": messages, "stream": True,
               "temperature": LLM.get("temperature", 0.7),
               "max_tokens": LLM.get("max_tokens", 400)}
    if tools:
        payload["tools"] = tools
    with requests.post(f"{g['base_url']}/chat/completions", json=payload,
                       headers={"Authorization": f"Bearer {g['api_key']}"},
                       stream=True, timeout=120) as r:
        if r.status_code != 200:
            raise RuntimeError(f"Groq {r.status_code}: {r.text[:300]}")
        tool_calls = []
        for raw in r.iter_lines():
            if not raw:
                continue
            line = raw.decode("utf-8") if isinstance(raw, bytes) else raw
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                break
            chunk = json.loads(data)
            delta = (chunk.get("choices") or [{}])[0].get("delta", {})
            if delta.get("content"):
                yield delta["content"], None
            for tc in delta.get("tool_calls") or []:
                idx = tc.get("index", 0)
                fn = tc.get("function", {})
                if idx >= len(tool_calls):
                    tool_calls.append({"id": "", "type": "function",
                                       "function": {"name": "", "arguments": ""}})
                if tc.get("id"):
                    tool_calls[idx]["id"] = tc["id"]
                if fn.get("name"):
                    tool_calls[idx]["function"]["name"] += fn["name"]
                if fn.get("arguments"):
                    tool_calls[idx]["function"]["arguments"] += fn["arguments"]
        if tool_calls:
            yield "", tool_calls


def _ollama_stream(messages, tools=None):
    payload = {"model": LLM["model"], "messages": messages, "stream": True,
               "options": {"temperature": LLM.get("temperature", 0.7),
                           "num_ctx": LLM.get("num_ctx", 4096)}}
    if tools:
        payload["tools"] = tools
    with requests.post(f"{LLM['host']}/api/chat", json=payload,
                       stream=True, timeout=300) as r:
        r.raise_for_status()
        tool_calls = []
        for line in r.iter_lines():
            if not line:
                continue
            chunk = json.loads(line)
            msg = chunk.get("message", {})
            if msg.get("content"):
                yield msg["content"], None
            if msg.get("tool_calls"):
                tool_calls.extend(msg["tool_calls"])
            if chunk.get("done"):
                break
        if tool_calls:
            yield "", tool_calls


def _chat_stream(messages, tools=None):
    """Yields (delta_text, tool_calls_or_None). Falls back to local Ollama if Groq fails."""
    if _is_groq():
        try:
            yield from _groq_stream(messages, tools)
            return
        except Exception as e:
            print(f"Groq stream failed ({e}); falling back to local Ollama")
            yield from _ollama_stream(messages, None)  # strip tools on fallback
            return
    yield from _ollama_stream(messages, None)


# ---------- shared logic ----------

def _run_tools(messages, calls):
    out = []
    for call in calls:
        fn = call.get("function", {})
        result = dispatch(fn.get("name", ""), _parse_args(fn.get("arguments", {})))
        tool_msg = {"role": "tool", "content": result}
        if call.get("id"):
            tool_msg["tool_call_id"] = call["id"]
        messages.append(tool_msg)
        out.append(result)
    return "\n".join(out)


def _matched_messages(user_text, tool_result):
    return [
        {"role": "system", "content": PERSONA +
         "\nThe user's request was already handled by a local tool. Report the tool result "
         "naturally in one or two sentences, in character. Do not mention the tool."},
        {"role": "user", "content": f"My request: {user_text}\n\nTool result:\n{tool_result}\n\nReport this to me."},
    ]


def _tool_mode() -> str:
    return LLM.get("tool_mode", "keyword")


def _use_tools() -> bool:
    # Groq handles full LLM function-calling well; keep manual keyword mode optional.
    return _tool_mode() == "llm" or (_tool_mode() != "keyword" and _is_groq())


def think(user_text: str) -> str:
    store.add_message("user", user_text)
    if _tool_mode() == "keyword":
        hit = kw_router.match(user_text)
        if hit:
            name, args = hit
            result = dispatch(name, args)
            msg = _chat(_matched_messages(user_text, result))
            reply = (msg.get("content") or result or "").strip()
            store.add_message("assistant", reply)
            return reply

    messages = [{"role": "system", "content": _system_prompt()}]
    messages += store.recent_history(8)

    use_tools = _use_tools()
    msg = _chat(messages, tools=TOOLS if use_tools else None)
    for _ in range(4):
        calls = msg.get("tool_calls") or []
        if not calls:
            break
        messages.append(msg)
        _run_tools(messages, calls)
        msg = _chat(messages, tools=TOOLS if use_tools else None)

    reply = (msg.get("content") or "").strip() or "I'm not sure how to respond to that."
    store.add_message("assistant", reply)
    return reply


def think_stream(user_text: str):
    store.add_message("user", user_text)
    full = ""
    if _tool_mode() == "keyword":
        hit = kw_router.match(user_text)
        if hit:
            name, args = hit
            result = dispatch(name, args)
            for delta, _ in _chat_stream(_matched_messages(user_text, result)):
                full += delta
                yield delta
            store.add_message("assistant", full.strip() or result)
            return

    messages = [{"role": "system", "content": _system_prompt()}]
    messages += store.recent_history(8)
    use_tools = _use_tools()

    for _ in range(4):
        round_text = ""
        tool_calls = None
        for delta, calls in _chat_stream(messages, tools=TOOLS if use_tools else None):
            if calls:
                tool_calls = calls
                break
            full += delta
            round_text += delta
            yield delta
        if tool_calls:
            messages.append({"role": "assistant", "content": round_text, "tool_calls": tool_calls})
            _run_tools(messages, tool_calls)
            continue
        break

    store.add_message("assistant", full.strip() or "I'm not sure how to respond to that.")


def ollama_available() -> bool:
    if _is_groq():
        try:
            g = _groq_cfg()
            r = requests.get(f"{g['base_url']}/models",
                             headers={"Authorization": f"Bearer {g['api_key']}"}, timeout=5)
            return r.status_code == 200
        except Exception:
            return False
    try:
        requests.get(f"{LLM['host']}/api/version", timeout=3)
        return True
    except Exception:
        return False


def active_model() -> str:
    return _groq_cfg().get("model") if _is_groq() else LLM.get("model", "unknown")
