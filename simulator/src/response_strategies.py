"""Response generation strategies for simulating user behavior.

Provides pluggable strategies for generating user responses based on persona
and conversation context.
"""

import logging
import random
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from litellm import completion

from simulator.src.persona import PersonaDefinition
from simulator.src.api_client import Goal

logger = logging.getLogger(__name__)


class ResponseStrategy(ABC):
    """Abstract base class for response generation strategies."""

    @abstractmethod
    def generate_response(
        self,
        persona: PersonaDefinition, 
        conversation_history: List[Dict[str, str]],
        agent_utterance: str,
        goal: Goal,
    ) -> str:
        """Generate a response based on the persona and conversation context.

        Args:
            persona: PersonaDefinition describing the user
            conversation_history: List of previous messages in the conversation
            agent_utterance: The most recent message from the agent
            scenario_id: Optional scenario identifier for context

        Returns:
            Generated response text
        """
        pass


class RandomStrategy(ResponseStrategy):
    """Generates random responses from a predefined pool.

    Useful for testing and development. Ignores persona and context.
    """

    # Predefined response templates
    RESPONSE_POOL = [
        "That's interesting. Can you tell me more?",
        "I see. What else do you have?",
        "That makes sense. Could you elaborate?",
        "Interesting. Are there other options?",
        "Got it. What about other approaches and resources?",
        "I understand. Could you compare that to other methods?",
        "Okay. Do you have any examples?",
        "I see where you're going. What's the general scope?",
        "That's helpful. Are there any limitations?",
        "Good to know. What are the next steps?",
        "I appreciate that. Can you clarify one thing?",
        "Makes sense. How does that compare to other solutions?",
        "Understood. What would you recommend?",
        "That's valuable. Do you have any case studies?",
        "I see. What's the main advantage there?",
    ]

    def generate_response(
        self,
        persona: PersonaDefinition = None, 
        conversation_history: List[Dict[str, str]] = None,
        agent_utterance: str = None,
        goal: Goal = None,
    ) -> str:
        """Generate a random response.

        Args:
            persona: PersonaDefinition (unused in random strategy)
            conversation_history: Conversation history (unused)
            agent_utterance: Agent message (unused)
            scenario_id: Optional scenario ID (unused)

        Returns:
            Random response from the pool
        """
        response = random.choice(self.RESPONSE_POOL)
        logger.debug(f"Generated random response: {response}")
        return response


class LLMStrategy(ResponseStrategy):
    """Generates responses using a Large Language Model via litellm.

    Uses the persona and conversation context to generate natural user responses.
    Maintains conversation state per conversation by building message history.
    Resets context for each new conversation.
    """

    def __init__(
        self,
        model: str = "ollama/qwen3:0.6b",
        api_base: str = "http://localhost:11434",
        **kwargs: Any
    ):
        """Initialize the LLM strategy.

        Args:
            model: The LLM model to use (e.g., "ollama/qwen3:0.6b")
            api_base: Base URL for the LLM API
            **kwargs: Additional arguments to pass to litellm completion
        """
        self.model = model
        self.api_base = api_base
        self.kwargs = kwargs
        logger.info(f"Initialized LLMStrategy with model: {model}")

    def generate_response(
        self,
        persona: PersonaDefinition,
        conversation_history: List[Dict[str, str]],
        agent_utterance: str,
        goal: Goal,
    ) -> str:
        """Generate a response using the LLM based on persona and context.

        Args:
            persona: PersonaDefinition describing the user
            conversation_history: List of previous messages in the conversation
            agent_utterance: The most recent message from the agent
            goal: The conversation goal

        Returns:
            Generated response text
        """
        # Build system prompt with persona information
        system_prompt = (
            f"You are simulating a user with the following persona: {persona.name}.\n"
            f"General info: {persona.general_info}\n"
            f"AI experience: {persona.ai_experience}\n"
            f"Traits: {persona.traits}\n"
            "Respond naturally as this persona in the conversation. "
            "Keep responses conversational and appropriate to the persona's characteristics."
        )

        # Add goal information for context
        if goal:
            system_prompt += (
                f"\n\nThe goal of this conversation is:\n"
                f"Context: {goal.context}\n"
                f"Target: {goal.target}\n"
                f"Discipline: {goal.discipline or 'N/A'}"
            )

        # Initialize messages with system prompt
        messages = [{"role": "system", "content": system_prompt}]

        # Add conversation history
        for msg in conversation_history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            # Map to LLM roles: user messages stay as user, agent messages as assistant
            llm_role = "user" if role == "user" else "assistant"
            messages.append({"role": llm_role, "content": content})

        # Add the current agent utterance if provided
        if agent_utterance:
            messages.append({"role": "assistant", "content": agent_utterance})
        else:
            # If no agent utterance (initial response), add a prompt to start the conversation
            messages.append({
                "role": "user",
                "content": "Please start the conversation based on the goal and your persona."
            })

        # Call the LLM
        try:
            response = completion(
                model=self.model,
                messages=messages,
                api_base=self.api_base,
                **self.kwargs
            )
            generated_response = response.choices[0].message.content
            logger.debug(f"Generated LLM response: {generated_response}")
            return generated_response
        except Exception as e:
            logger.error(f"Error generating response with LLM: {e}")
            # Fallback to a simple response
            return "I'm sorry, I couldn't generate a response right now."
