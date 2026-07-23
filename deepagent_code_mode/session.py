"""
Code Mode Session Manager

管理与内置 OpenCode 的隔离会话。
每个 Code 模式任务拥有独立的会话上下文。
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
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

    def get_session(self, session_id: str) -> Optional[CodeModeSession]:
        return self.sessions.get(session_id)

    def append_instruction(self, session_id: str, instruction: str) -> bool:
        """向会话追加一条指令。

        B8 修复：原实现对不存在的 session_id 静默失败，调用方无法区分是否成功。
        现在返回 True/False 标识是否成功追加，便于上游做错误处理。
        """
        session = self.sessions.get(session_id)
        if session is None:
            return False
        if session.status != "active":
            return False
        session.instructions.append(instruction)
        return True

    def append_result(self, session_id: str, result: Dict[str, Any]) -> bool:
        """向会话追加一条任务执行结果。

        B8 新增：原 API 无法记录结果，无法追踪 session 中每个派发任务的产出。
        """
        session = self.sessions.get(session_id)
        if session is None:
            return False
        session.results.append({
            "at": datetime.now().isoformat(),
            **result,
        })
        return True

    def complete_session(self, session_id: str) -> bool:
        """标记会话为已完成。B8 新增。"""
        session = self.sessions.get(session_id)
        if session is None:
            return False
        session.status = "completed"
        return True

    def list_sessions(self, status: Optional[str] = None) -> List[CodeModeSession]:
        """列出会话，可按状态过滤。B8 新增。"""
        items = list(self.sessions.values())
        if status:
            items = [s for s in items if s.status == status]
        return items
