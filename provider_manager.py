import os
from core.engine import CoreEngine
from core.memory import MemoryStore
from identity.companion_identity import CompanionIdentity
from identity.safespace_identity import SafeSpaceIdentity

class ProviderManager:
    def __init__(self):
        self.engine = CoreEngine()

        # memory turns configurable (default 6 turns = 12 msgs)
        turns = os.getenv("SHINE_MEMORY_TURNS", "6").strip()
        try:
            turns = int(turns)
        except:
            turns = 6

        self.memory = MemoryStore(data_dir=os.path.join(os.path.dirname(__file__), "data"), max_turns=max(1, turns))

        self.identities = {
            "companion": CompanionIdentity(),
            "safespace": SafeSpaceIdentity(),
        }

    def chat(self, message, mode="companion"):
        mode = (mode or "companion").lower().strip()
        identity = self.identities.get(mode, self.identities["companion"])
        system_prompt = identity.get_prompt()

        history = self.memory.load_messages(mode)

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": message})

        reply = self.engine.generate_from_messages(messages)

        # Persist the turn to the mode-specific memory file
        self.memory.append(mode, "user", message)
        self.memory.append(mode, "assistant", reply)

        return reply

    def memory_status(self):
        return self.memory.status()

    def memory_clear(self, mode="companion"):
        mode = (mode or "companion").lower().strip()
        if mode not in ("companion", "safespace", "all"):
            mode = "companion"
        self.memory.clear(mode)

    def memory_peek(self, mode="companion", n=10):
        mode = (mode or "companion").lower().strip()
        if mode not in ("companion", "safespace"):
            mode = "companion"
        msgs = self.memory.load_messages(mode)
        return msgs[-max(1, int(n)):]
