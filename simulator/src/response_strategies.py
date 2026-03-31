"""Response generation strategies for simulating user behavior.

Provides pluggable strategies for generating user responses based on persona
and conversation context.
"""

import logging
import random
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

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
