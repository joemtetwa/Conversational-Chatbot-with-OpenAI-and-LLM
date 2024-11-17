from datetime import datetime
from profile_manager import ProfileManager
from typing import Dict, Optional
import uuid

class SessionManager:
    def __init__(self):
        self.sessions = {}
        self.current_session = None

    def create_session(self) -> str:
        """Create a new chat session."""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            'created_at': datetime.now().isoformat(),
            'profile_manager': ProfileManager(),
            'messages': []
        }
        self.current_session = self.sessions[session_id]
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session by ID."""
        return self.sessions.get(session_id)

    def end_session(self, session_id: str) -> None:
        """End a chat session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            if self.current_session and session_id == list(self.sessions.keys())[-1]:
                self.current_session = None

    def add_message(self, session_id: str, role: str, content: str) -> None:
        """Add a message to the session history."""
        if session_id in self.sessions:
            self.sessions[session_id]['messages'].append({
                'role': role,
                'content': content,
                'timestamp': datetime.now().isoformat()
            })
