import os
import json
import time
from typing import List, Dict

class MemoryStore:
    def __init__(self, data_dir: str, max_turns: int = 6):
        self.data_dir = data_dir
        self.max_turns = max_turns  # turns = user+assistant pairs
        os.makedirs(self.data_dir, exist_ok=True)

    def _path(self, mode: str) -> str:
        safe = (mode or "companion").lower().strip()
        return os.path.join(self.data_dir, f"memory_{safe}.jsonl")

    def load_messages(self, mode: str) -> List[Dict[str, str]]:
        path = self._path(mode)
        if not os.path.exists(path):
            return []

        lines = []
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except:
            return []

        # Each "turn" is typically 2 entries (user + assistant)
        max_entries = max(2 * self.max_turns, 2)
        lines = lines[-max_entries:]

        msgs: List[Dict[str, str]] = []
        for ln in lines:
            ln = ln.strip()
            if not ln:
                continue
            try:
                obj = json.loads(ln)
                role = obj.get("role")
                content = obj.get("content")
                if role in ("user", "assistant") and isinstance(content, str) and content.strip():
                    msgs.append({"role": role, "content": content})
            except:
                continue
        return msgs

    def append(self, mode: str, role: str, content: str):
        if role not in ("user", "assistant"):
            return
        if not isinstance(content, str) or not content.strip():
            return

        path = self._path(mode)
        rec = {"ts": int(time.time()), "role": role, "content": content}

        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except:
            pass

    def clear(self, mode: str):
        if mode == "all":
            # clear all known files in data_dir matching memory_*.jsonl
            try:
                for name in os.listdir(self.data_dir):
                    if name.startswith("memory_") and name.endswith(".jsonl"):
                        try:
                            os.remove(os.path.join(self.data_dir, name))
                        except:
                            pass
            except:
                pass
            return

        path = self._path(mode)
        try:
            if os.path.exists(path):
                os.remove(path)
        except:
            pass

    def status(self) -> Dict[str, int]:
        out = {}
        try:
            for name in os.listdir(self.data_dir):
                if name.startswith("memory_") and name.endswith(".jsonl"):
                    mode = name[len("memory_"):-len(".jsonl")]
                    try:
                        with open(os.path.join(self.data_dir, name), "r", encoding="utf-8") as f:
                            out[mode] = sum(1 for _ in f)
                    except:
                        out[mode] = 0
        except:
            pass
        return out
