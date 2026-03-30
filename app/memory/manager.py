class MemoryManager:
    def __init__(self):
        self.sessions = {}

    def get_recent(self, session_id):
        return self.sessions.get(session_id, [])[-5:]

    def store(self, session_id, message):
        self.sessions.setdefault(session_id, []).append(message)