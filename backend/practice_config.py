from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "config"


def load_practice(practice_id: str) -> dict:
    path = CONFIG_DIR / f"{practice_id.replace('_demo', '')}.yaml"
    if practice_id == "spine_demo":
        path = CONFIG_DIR / "spine.yaml"
    elif practice_id == "primary_care_demo":
        path = CONFIG_DIR / "primary_care.yaml"
    if not path.exists():
        for f in CONFIG_DIR.glob("*.yaml"):
            data = yaml.safe_load(f.read_text(encoding="utf-8"))
            if data.get("practice_id") == practice_id:
                return data
        raise KeyError(f"Unknown practice: {practice_id}")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def list_practices() -> list[str]:
    ids = []
    for f in CONFIG_DIR.glob("*.yaml"):
        data = yaml.safe_load(f.read_text(encoding="utf-8"))
        ids.append(data["practice_id"])
    return ids
