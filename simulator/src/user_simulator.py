"""Main user simulator module.

Orchestrates conversation between a simulated user and a conversational agent.
"""

import json
import logging
import uuid
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from simulator.src.api_client import SimulatorAPIClient, APIResponse, Source, Utterance, Goal
from simulator.src.persona import PersonaDefinition
from simulator.src.response_strategies import ResponseStrategy, RandomStrategy

logger = logging.getLogger(__name__)


@dataclass
class ConversationState:
    """Tracks the state of an ongoing conversation.

    Attributes:
        run_id: ID of the current run
        conversation_id: ID of the conversation
        goal: Current Goal being pursued
        chat_history: List of messages exchanged in the conversation
        last_agent_utterance: The last Utterance from the agent
        turn_count: Number of turns in the conversation
    """

    run_id: str
    conversation_id: str
    goal: Goal
    chat_history: List[Dict[str, str]] = field(default_factory=list)
    last_agent_utterance: Optional[Utterance] = None
    turn_count: int = 0

    def add_agent_message(self, utterance: Utterance) -> None:
        """Add an agent utterance to the chat history.

        Args:
            utterance: Agent Utterance object
        """
        self.chat_history.append({"role": "assistant", "content": utterance.text})
        self.last_agent_utterance = utterance
        self.conversation_id = utterance.conversation_id

    def add_user_message(self, message: str) -> None:
        """Add a user message to the chat history.

        Args:
            message: User message text
        """
        self.chat_history.append({"role": "user", "content": message})

    def is_conversation_active(self) -> bool:
        """Check if the conversation is still active.

        Returns:
            True if conversation has not ended with is_final
        """
        return self.last_agent_utterance is None or not self.last_agent_utterance.is_final
    

class UserSimulator:
    """Simulates a user interacting with a conversational agent.

    Orchestrates the conversation flow by:
    1. Initiating conversations via the API
    2. Generating responses using the configured strategy
    3. Sending responses and receiving agent replies
    4. Tracking conversation state
    """

    def __init__(
        self,
        persona: PersonaDefinition,
        api_client: SimulatorAPIClient,
        response_strategy: Optional[ResponseStrategy] = None,
    ):
        """Initialize the user simulator.

        Args:
            persona: PersonaDefinition describing the simulated user
            api_client: SimulatorAPIClient for API interactions
            response_strategy: ResponseStrategy for generating responses
                (defaults to RandomStrategy)
        """
        self.persona = persona
        self.api_client = api_client
        self.response_strategy = response_strategy or RandomStrategy()
        self.state: Optional[ConversationState] = None
        logger.info(
            f"Initialized UserSimulator for persona {persona.name} ({persona.id})"
        )

    def initiate_run(self, run_id: str, description: str) -> APIResponse:
        """Start a new conversation with the agent.

        Args:
            run_id: Unique identifier for the run
            description: Description of the run

        Returns:
            APIResponse containing the conversation goal and first agent utterance

        Raises:
            RuntimeError: If a conversation is already active
        """
        if self.state is not None:
            raise RuntimeError(
                "A conversation is already active. "
                "Call end_conversation() first."
            )

        logger.info(f"Initiating run: {run_id}")

        # Call API to start the run
        response = self.api_client.start_run(run_id, description)

        self.state = ConversationState(
            run_id=run_id,
            conversation_id=response.conversation_id,
            goal=response.goal,
            turn_count=0,
        )

        if response.utterance is not None:
            self.state.add_agent_message(response.utterance)

        return response

    def initiate_conversation(self, run_id: str, conversation_id: str, goal: Goal):
        """Start a new conversation with the agent.

        Args:
            run_id: Unique identifier for the run
            conversation_id: ID of the existing conversation

        Returns:
            APIResponse containing the conversation goal and first agent utterance

        Raises:
            RuntimeError: If a conversation is already active
        """
        if self.state is not None:
            raise RuntimeError(
                "A conversation is already active. "
                "Call end_conversation() first."
            )

        logger.info(f"Initiating conversation for run: {run_id}")

        # Initialize conversation state
        self.state = ConversationState(
            run_id=run_id,
            conversation_id=conversation_id,
            goal=goal,
            turn_count=0,
        )

    def respond(self, agent_utterance: Optional[str] = None) -> str:
        """Generate a response to the agent's message.

        Uses the configured response strategy to generate a contextual response
        based on the persona, conversation history, and current goal.

        Args:
            agent_utterance: Optional agent message to respond to
                (if None, uses the last received message)

        Returns:
            Generated response text

        Raises:
            RuntimeError: If no conversation is active
        """
        if self.state is None:
            raise RuntimeError(
                "No active conversation. Call initiate_conversation() first."
            )

        message = agent_utterance or (
            self.state.last_agent_utterance.text
            if self.state.last_agent_utterance
            else None
        )
        # if not message:
        #     raise ValueError("No agent message to respond to")

        logger.debug(f"Generating response for persona {self.persona.name}")

        response = self.response_strategy.generate_response(
            self.persona,
            self.state.chat_history,
            message,
            self.state.goal,
        )

        # Store the generated response temporarily
        self._pending_response = response
        return response

    def continue_conversation(
        self, response_text: Optional[str] = None, is_final: bool = False
    ) -> APIResponse:
        """Send a response and continue the conversation.

        This follows the run submission sequence:
        - Submit user utterance via POST /run/continue
        - Receive next agent utterance or signal of run completion
        - Update conversation state based on response

        Args:
            response_text: The user's response text
                (if None, uses the last generated response)
            is_final: Whether this is the final user utterance

        Returns:
            APIResponse with the next agent utterance

        Raises:
            RuntimeError: If no conversation is active
            ValueError: If no response is available
        """
        if self.state is None:
            raise RuntimeError(
                "No active conversation. Call initiate_conversation() first."
            )

        # Use provided response or the last generated one
        text = response_text or getattr(self, "_pending_response", None)
        if not text:
            raise ValueError(
                "No response text provided. Call respond() first or provide text."
            )

        logger.info(f"Continuing conversation for run: {self.state.run_id}")
        logger.debug(f"User response: {text}")

        # Add user response to history
        self.state.add_user_message(text)

        # Call API to continue
        try:
            response = self.api_client.continue_run(
                self.state.run_id,
                text,
                self.state.conversation_id,
                sources=None,
                annotations=None,
                is_final=is_final,
            )

            # Update state
            self.state.turn_count += 1
            
            # Add agent response to history if present
            if response.utterance is not None:
                self.state.add_agent_message(response.utterance)
                logger.debug(
                    f"Conversation continued. Agent response: {response.utterance.text[:100]}..."
                )

            # Clear pending response
            if hasattr(self, "_pending_response"):
                delattr(self, "_pending_response")

            return response

        except Exception as e:
            logger.error(f"Failed to continue conversation: {e}")
            raise

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Retrieve the chat history of the current conversation.

        Returns:
            List of message dictionaries with roles and content

        Raises:
            RuntimeError: If no conversation is active
        """
        if self.state is None:
            raise RuntimeError(
                "No active conversation. Call initiate_conversation() first."
            )

        return self.state.chat_history.copy()

    def get_full_session(self) -> List[Utterance]:
        """Retrieve complete session data from the API.

        Returns:
            List of Utterance objects for the entire session

        Raises:
            RuntimeError: If no conversation is active
        """
        if self.state is None:
            raise RuntimeError(
                "No active conversation. Call initiate_conversation() first."
            )

        return self.api_client.get_session(self.state.run_id)

    def get_run_dump(self) -> List[Dict[str, Any]]:
        """Retrieve full run data in JSON format.

        Returns:
            List of dictionaries containing run data

        Raises:
            RuntimeError: If no conversation is active
        """
        if self.state is None:
            raise RuntimeError(
                "No active conversation. Call initiate_conversation() first."
            )

        return self.api_client.get_run_dump(self.state.run_id)

    def is_conversation_active(self) -> bool:
        """Check if a conversation is currently active.

        Returns:
            True if a conversation is in progress
        """
        return self.state is not None and self.state.is_conversation_active()

    def end_conversation(self) -> None:
        """End the current conversation and clean up state.

        This can be called explicitly to close the conversation, or implicitly
        when the agent indicates the conversation is complete.
        """
        if self.state is not None:
            logger.info(
                f"Ending conversation for run: {self.state.run_id} "
                f"(turns: {self.state.turn_count})"
            )
            self.state = None
        if hasattr(self, "_pending_response"):
            delattr(self, "_pending_response")

    def get_state(self) -> Optional[ConversationState]:
        """Get the current conversation state (read-only).

        Returns:
            Current ConversationState or None if no active conversation
        """
        return self.state

    def complete_run(
        self, 
        run_id: str, 
        description: str,
        run_path: Optional[Path] = None,
        max_turns: int = 1000,
    ) -> Dict[str, Any]:
        """Execute a complete run from start to finish.

        This is a higher-level method that orchestrates the entire run workflow:
        1. Initiates the run with the given run_id and description
        2. Loops through conversation turns until completion
        3. Handles multiple conversations/goals if needed
        4. Cleans up and returns metrics

        Args:
            run_id: Unique identifier for the run
            description: Description of the run
            max_turns: Maximum number of turns to execute (default: 1000)

        Returns:
            Dictionary containing:
                - run_id: The run ID
                - total_conversations: Number of conversations/goals attempted
                - total_turns: Total number of turns completed
                - status: "success", "max_turns_exceeded", or "error"
                - errors: List of any errors encountered

        Raises:
            RuntimeError: If a conversation is already active
        """
        if self.state is not None:
            raise RuntimeError(
                "A conversation is already active. Call end_conversation() first."
            )

        logger.info(f"Starting complete run: {run_id}")

        # Track metrics
        metrics = {
            "run_id": run_id,
            "total_conversations": 0,
            "total_turns": 0,
            "status": "success",
            "errors": [],
        }

        try:
            # Step 1: Initialize the run
            logger.info(f"Initializing run: {run_id}")
            initial_response = self.initiate_run(run_id, description)
            logger.info(f"Run initialized. Goal: {initial_response.goal.target}")
            metrics["total_conversations"] = 1

            # Step 2: Conversation loop
            conversation_count = 1
            total_turns = 0
            conversation_active = True

            while conversation_active and total_turns < max_turns:
                try:
                    # Generate and send response
                    user_response = self.respond()
                    logger.debug(f"Generated response: {user_response[:100]}...")

                    # Continue the conversation
                    response = self.continue_conversation(
                        response_text=user_response,
                        is_final=False,
                    )

                    total_turns += 1
                    metrics["total_turns"] = total_turns

                    # Check conversation status
                    if response.is_complete:
                        # Run completed (428 status code received)
                        logger.info("Run completed (428 status received)")
                        conversation_active = False

                    elif response.is_new_conversation:
                        # New conversation started (201 status code received)
                        logger.info("New conversation started (201 status received)")
                        self.end_conversation()
                        conversation_count += 1
                        metrics["total_conversations"] = conversation_count

                        # Initialize new conversation state
                        self.initiate_conversation(run_id, response.conversation_id, response.goal)
                        
                        # Add agent message if present
                        if response.utterance is not None:
                            self.state.add_agent_message(response.utterance)

                    elif response.utterance is None:
                        # New goal/scenario starting
                        logger.info(
                            f"New goal initiated. Goal: {response.goal.target}"
                        )
                        self.end_conversation()
                        conversation_count += 1
                        metrics["total_conversations"] = conversation_count

                        response = self.initiate_conversation(run_id, response.conversation_id, response.goal)
                        
                        user_response = self.respond()
                        logger.debug(f"Generated response: {user_response[:100]}...")

                        # Continue the conversation
                        response = self.continue_conversation(
                            response_text=user_response,
                            is_final=False,
                        )

                    elif response.utterance.is_final:
                        # Agent indicates end of conversation
                        logger.info("Conversation ended by agent (is_final=True)")
                        conversation_active = False

                    else:
                        # Conversation continues normally
                        logger.debug(
                            f"Turn {total_turns}: Conversation active, "
                            f"{len(self.state.chat_history)} messages so far"
                        )

                except Exception as e:
                    logger.error(f"Error during conversation turn: {e}")
                    metrics["status"] = "error"
                    metrics["errors"].append(str(e))
                    break

            # Step 3: Check completion status
            if total_turns >= max_turns:
                logger.warning(
                    f"Run terminated: max turns ({max_turns}) exceeded"
                )
                metrics["status"] = "max_turns_exceeded"

            # Step 4: Clean up
            self.end_conversation()

            # Step 5: Write run dump to disk
            if run_path is not None:
                try:
                    run_path.mkdir(parents=True, exist_ok=True)
                    dump_path = run_path / f"{run_id}.json"
                    with open(dump_path, "w") as f:
                        json.dump(self.api_client.get_run_dump(run_id=run_id), f, indent=2)
                    logger.info(f"Run dump saved to {dump_path}")
                except Exception as e:
                    logger.warning(f"Could not save run dump: {e}")

            logger.info(
                f"Complete run finished: run_id={run_id}, "
                f"status={metrics['status']}, "
                f"conversations={conversation_count}, "
                f"total_turns={total_turns}"
            )

        except Exception as e:
            logger.error(f"Fatal error in complete_run: {e}")
            metrics["status"] = "error"
            metrics["errors"].append(str(e))
            self.end_conversation()

        return metrics