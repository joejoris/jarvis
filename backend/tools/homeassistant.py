"""Home Assistant control via the REST API (optional; needs config.yaml url+token)."""
import requests
from backend import config

CFG = config.CONFIG


def _ha():
    ha = CFG.get("homeassistant", {})
    url, token = ha.get("url", "").rstrip("/"), ha.get("token", "")
    if not url or not token:
        return None, None
    return url, {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _domain_service(entity_id: str) -> str:
    return entity_id.split(".", 1)[0] if "." in entity_id else "homeassistant"


def ha_turn_on(entity_id: str) -> str:
    url, headers = _ha()
    if not url:
        return "Home Assistant is not configured. Set homeassistant.url and homeassistant.token in config.yaml."
    domain = _domain_service(entity_id)
    try:
        r = requests.post(f"{url}/api/services/{domain}/turn_on",
                          json={"entity_id": entity_id}, headers=headers, timeout=10)
        return f"Turned on {entity_id}." if r.status_code < 300 else f"HA error {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return f"Home Assistant unreachable: {e}"


def ha_turn_off(entity_id: str) -> str:
    url, headers = _ha()
    if not url:
        return "Home Assistant is not configured. Set homeassistant.url and homeassistant.token in config.yaml."
    domain = _domain_service(entity_id)
    try:
        r = requests.post(f"{url}/api/services/{domain}/turn_off",
                          json={"entity_id": entity_id}, headers=headers, timeout=10)
        return f"Turned off {entity_id}." if r.status_code < 300 else f"HA error {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return f"Home Assistant unreachable: {e}"


def ha_get_state(entity_id: str) -> str:
    url, headers = _ha()
    if not url:
        return "Home Assistant is not configured. Set homeassistant.url and homeassistant.token in config.yaml."
    try:
        r = requests.get(f"{url}/api/states/{entity_id}", headers=headers, timeout=10)
        if r.status_code == 200:
            d = r.json()
            attrs = d.get("attributes", {})
            name = attrs.get("friendly_name", entity_id)
            return f"{name} is {d.get('state')}."
        return f"HA error {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return f"Home Assistant unreachable: {e}"
