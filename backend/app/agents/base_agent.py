"""
Claude Mythos -- Base Agent Class
Abstract base class for all 23 AI employees.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.enhanced_memory import EnhancedAgentMemory
from app.core.memory import SharedMemory
from app.core.models import Agent as AgentConfig
from app.services.llm_client import llm_client, LLMResponse


class BaseAgent:
    """
    Base class for all Claude Mythos agents.
    Provides think (LLM), act (tool execution), memory, and communication.

    Uses EnhancedAgentMemory for rich episodic, semantic, procedural,
    and client-specific memory.
    """

    def __init__(self, config: AgentConfig):
        self.config = config
        self.memory = EnhancedAgentMemory(config.id)
        self._conversation_buffer: List[Dict[str, str]] = []

    @property
    def id(self) -> str:
        return self.config.id

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def full_name(self) -> str:
        return self.config.full_name

    @property
    def avatar(self) -> str:
        return self.config.avatar

    @property
    def system_prompt(self) -> str:
        return self.config.system_prompt

    # -- Think (LLM Call) --

    async def think(
        self,
        task: str,
        context: str = "",
        temperature: Optional[float] = None,
        structured_output: Optional[Dict[str, Any]] = None,
        task_meta: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Think through a task using the LLM with rich memory injection.

        Args:
            task: The task or question to think about
            context: Additional context to include
            temperature: Override default temperature
            structured_output: JSON schema for structured responses
            task_meta: Dict with client_id, campaign_id, task_type etc
                       used to pull relevant memory context

        Returns:
            The LLM's response text
        """
        prompt_parts = []

        # -- 1. Inject rich memory context (THE KEY FEATURE) --
        if task_meta is None:
            # Build minimal task_meta from what we can infer
            task_meta = {
                "title": task[:200],
                "description": task,
            }

        memory_context = self.memory.get_context_for_task(task_meta)
        if memory_context:
            prompt_parts.append(f"{memory_context}\n")

        # -- 2. Explicit caller context --
        if context:
            prompt_parts.append(f"Additional Context:\n{context}\n")

        # -- 3. Recent conversation continuity --
        recent_memory = self.memory.get_recent_context(limit=5)
        if recent_memory and recent_memory != "No previous context.":
            prompt_parts.append(f"Recent conversations:\n{recent_memory}\n")

        prompt_parts.append(f"Task:\n{task}")

        full_prompt = "\n".join(prompt_parts)

        # Call LLM
        response: LLMResponse = await llm_client.complete(
            prompt=full_prompt,
            system=self.system_prompt,
            temperature=temperature,
            structured_output=structured_output,
        )

        # Store in conversation buffer
        self._conversation_buffer.append({"role": "user", "content": task})
        self._conversation_buffer.append({"role": "assistant", "content": response.text})

        # Keep buffer manageable
        if len(self._conversation_buffer) > 20:
            self._conversation_buffer = self._conversation_buffer[-20:]

        # Log the thinking activity (also creates an episode)
        self.memory.log_activity(
            action="think",
            target_type="llm",
            details={
                "task_preview": task[:200],
                "response_preview": response.text[:200],
                "provider": response.provider,
                "latency_ms": response.latency_ms,
            },
        )

        # Record as episode for rich memory
        client_id = task_meta.get("client_id") if task_meta else None
        campaign_id = task_meta.get("campaign_id") if task_meta else None
        self.memory.record_episode(
            event_type="llm_think",
            description=f"Thought about: {task[:200]}",
            client_id=client_id,
            campaign_id=campaign_id,
            importance=4,
        )

        return response.text

    async def think_structured(
        self,
        task: str,
        output_schema: Dict[str, Any],
        context: str = "",
        task_meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Think through a task and return a structured JSON response.

        Args:
            task: The task or question
            output_schema: JSON schema describing expected output
            context: Additional context
            task_meta: Dict with client_id, campaign_id, task_type etc

        Returns:
            Parsed JSON as dict
        """
        schema_hint = json.dumps(output_schema, indent=2)
        full_task = f"{task}\n\nRespond with JSON matching this schema:\n{schema_hint}"

        response = await self.think(
            task=full_task,
            context=context,
            structured_output=output_schema,
            task_meta=task_meta,
        )

        # Try to parse JSON
        try:
            # Try direct parse first
            result = json.loads(response)
            return result
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code block
            try:
                if "```json" in response:
                    json_str = response.split("```json")[1].split("```")[0].strip()
                    return json.loads(json_str)
                elif "```" in response:
                    json_str = response.split("```")[1].split("```")[0].strip()
                    return json.loads(json_str)
            except (json.JSONDecodeError, IndexError):
                pass

            # Return raw text wrapped in dict as fallback
            return {"raw_response": response, "parse_error": True}

    # -- Act (Tool Execution) --

    async def act(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool action.

        Args:
            tool_name: Name of the tool to execute
            params: Tool parameters

        Returns:
            Tool execution result
        """
        # Log the action
        self.memory.log_activity(
            action=f"tool:{tool_name}",
            target_type="tool",
            details={"tool": tool_name, "params": params},
        )

        # Tool execution is handled by the orchestrator
        # This is a placeholder that logs and returns
        return {
            "tool": tool_name,
            "status": "executed",
            "params": params,
            "result": f"Tool {tool_name} executed by {self.name}",
        }

    # -- Communication --

    async def communicate(
        self,
        to: str,
        message: str,
        message_type: str = "chat",
        campaign_id: Optional[str] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Send a message to another agent or the owner.

        Args:
            to: Recipient agent ID or "owner"
            message: Message content
            message_type: Type of message
            campaign_id: Optional associated campaign
            extra_metadata: Optional metadata

        Returns:
            Message ID
        """
        msg_id = self.memory.add_message(
            content=message,
            from_agent=self.id,
            to_agent=to,
            message_type=message_type,
            extra_metadata=extra_metadata or {},
            campaign_id=campaign_id,
        )

        self.memory.log_activity(
            action="send_message",
            target_type="message",
            target_id=msg_id,
            details={"to": to, "message_type": message_type, "preview": message[:100]},
        )

        return msg_id

    async def receive_messages(self) -> List[Dict[str, Any]]:
        """Get unread messages for this agent."""
        return SharedMemory.get_unread_messages(self.id)

    # -- Memory Shortcuts --

    async def recall(self, key: str, default: Any = None) -> Any:
        """Recall a stored memory value."""
        return self.memory.get_state(key, default)

    async def remember(self, key: str, value: Any) -> None:
        """Store a memory value."""
        self.memory.set_state(key, value)

    # -- Status Management --

    def set_status(self, status: str, current_task: Optional[str] = None) -> None:
        """Update agent status."""
        self.config.status = status
        if current_task:
            self.config.current_task = current_task

        self.memory.log_activity(
            action="status_change",
            target_type="agent",
            target_id=self.id,
            details={"status": status, "current_task": current_task},
        )

    # -- Task Processing --

    async def process_task(
        self,
        task_description: str,
        context: str = "",
        task_meta: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Process a task end-to-end: think and return result.

        Args:
            task_description: What needs to be done
            context: Additional context
            task_meta: Dict with client_id, campaign_id, task_type etc

        Returns:
            Processing result
        """
        self.set_status("busy", task_description[:100])

        try:
            result = await self.think(
                task=task_description,
                context=context,
                task_meta=task_meta,
            )

            # Log completion
            self.memory.log_activity(
                action="task_completed",
                target_type="task",
                details={
                    "task": task_description[:200],
                    "result_preview": result[:200],
                },
            )

            # Record as episode
            if task_meta:
                self.memory.record_episode(
                    event_type="task_completed",
                    description=f"Completed: {task_description[:200]}",
                    client_id=task_meta.get("client_id"),
                    campaign_id=task_meta.get("campaign_id"),
                    importance=7,
                    emotions={"valence": "positive", "intensity": 7},
                )

            # Auto-extract pattern if result seems successful
            if len(result) > 50 and task_meta:
                self._auto_learn_pattern(result, task_meta, task_description)

            return result
        finally:
            self.set_status("active")

    def _auto_learn_pattern(self, result: str, task_meta: Dict[str, Any], task_desc: str) -> None:
        """Automatically extract a procedural pattern from a successful task result."""
        task_type = task_meta.get("task_type", "general")
        client_id = task_meta.get("client_id")

        # Simple heuristic: if result is substantial, record as a pattern
        pattern_name = f"auto_{task_type}_{self.id}"
        self.memory.record_pattern(
            pattern_name=pattern_name,
            description=f"For task '{task_desc[:100]}', approach was: {result[:300]}",
            context=task_type,
            success_rating=0.6,  # Start with moderate confidence
            client_type=None,  # Could look up from client_id
        )

    # -- Utility --

    def to_dict(self) -> Dict[str, Any]:
        """Serialize agent state to dict."""
        return {
            "id": self.id,
            "name": self.name,
            "full_name": self.full_name,
            "role": self.config.role,
            "title": self.config.title,
            "avatar": self.avatar,
            "status": self.config.status,
            "current_task": self.config.current_task,
            "skills": self.config.skills,
            "tools": self.config.tools,
        }

    def __repr__(self) -> str:
        return f"BaseAgent({self.id}={self.full_name}, status={self.config.status})"

    async def schedule_post(self, campaign_id: str, platform: str, content_type: str, content_text: str, scheduled_time: datetime, extra_metadata: Optional[Dict[str, Any]] = None) -> Any:
        """Tool: Schedule a social media post."""
        from app.services.content_calendar import content_calendar
        from app.core.models import ScheduledPostCreate

        post_create = ScheduledPostCreate(
            campaign_id=campaign_id,
            platform=platform,
            content_type=content_type,
            content_text=content_text,
            scheduled_time=scheduled_time,
            extra_metadata=extra_metadata or {}
        )
        return await content_calendar.add_scheduled_post(post_create)
