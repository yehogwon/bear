from __future__ import annotations

from pydantic import BaseModel, Field

from bear.domain.enums import PermissionLevel


class PermissionDecision(BaseModel):
    tool_name: str
    level: PermissionLevel
    reason: str


class PermissionPolicy(BaseModel):
    defaults: dict[str, PermissionLevel] = Field(default_factory=dict)
    context_overrides: dict[str, dict[str, PermissionLevel]] = Field(default_factory=dict)

    def resolve(self, tool_name: str, context: str | None = None) -> PermissionDecision:
        if (
            context
            and context in self.context_overrides
            and tool_name in self.context_overrides[context]
        ):
            return PermissionDecision(
                tool_name=tool_name,
                level=self.context_overrides[context][tool_name],
                reason=f'context override for {context}',
            )
        level = self.defaults.get(tool_name, PermissionLevel.REQUEST)
        return PermissionDecision(tool_name=tool_name, level=level, reason='default policy')
