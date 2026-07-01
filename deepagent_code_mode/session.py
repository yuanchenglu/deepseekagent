"""
Code Mode Session Manager

管理与内置 OpenCode 的隔离会话。
每个 Code 模式任务拥有独立的会话上下文。
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from datetime import datetime


@dataclass
class CodeModeSession:
    session_id: str
    created_at: datetime = field(default_factory=datetime.now)
    instructions: List[str] = field(default_factory=list)
    results: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "active"


class CodeModeSessionManager:
    def __init__(self):
        self.sessions: Dict[str, CodeModeSession] = {}

    def create_session(self) -> CodeModeSession:
        import uuid
        sid = str(uuid.uuid4())[:8]
        session = CodeModeSession(session_id=sid)
        self.sessions[sid] = session
        return session

    def get_session(self, session_id: str) -> CodeModeSession | None:
        return self.sessions.get(session_id)

    def append_instruction(self, session_id: str, instruction: str):
        if session := self.sessions.get(session_id):
            session.instructions.append(instruction)
