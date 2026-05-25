from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


AgentStatus = Literal["completed", "fallback", "skipped", "failed"]


class AgentStep(BaseModel):
    agent: str
    status: AgentStatus
    summary: str
    provider: str = ""
    output: Dict[str, Any] = Field(default_factory=dict)


class AgentTrace(BaseModel):
    provider: str = ""
    model: str = ""
    steps: List[AgentStep] = Field(default_factory=list)

