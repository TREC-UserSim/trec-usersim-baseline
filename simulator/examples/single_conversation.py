"""Single conversation example using LLM-based response strategy."""

import argparse
from dotenv import load_dotenv
import os
import logging

from simulator.src.api_client import SimulatorAPIClient
from simulator.src.persona import PersonaDefinition, PersonaRegistry
from simulator.src.user_simulator import UserSimulator
from simulator.src.response_strategies import LLMStrategy

load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

base_url = os.getenv("BASE_URL") 
team_name = os.getenv("TEAM_NAME")
auth_token = os.getenv("AUTH_TOKEN")
llm_model = os.getenv("LLM_MODEL")
llm_api_base = os.getenv("LLM_API_BASE")

def main(debug: bool = False):
    """Run a single conversation using LLM strategy."""

    api_client = SimulatorAPIClient(
        base_url= base_url,
        team_id=team_name,
        auth_token=auth_token,
    )

    persona_registry = PersonaRegistry()
    persona_registry.load_from_file("simulator/personas.example.json")
    persona = persona_registry.get_persona("persona_001")

    response_strategy = LLMStrategy(
        model=llm_model,
        api_base=llm_api_base
        )

    user_simulator = UserSimulator(
        api_client=api_client,
        persona=persona,
        response_strategy=response_strategy,
    )

    logger.info("Initialized user simulator with LLM strategy")

    try:
        # Initiate run
        logger.info("Starting run...")
        response = user_simulator.initiate_run(
            run_id="example_run_llm_001",
            description="Example conversation with LLM-based user simulator",
            debug=debug,
        )

        logger.info(f"Agent: {response.utterance.text if response.utterance else 'No initial utterance'}")
        turn_count = 0

        # Continue conversation until completion
        while user_simulator.is_conversation_active() and turn_count < 10:
            # Generate user user_simulator using LLM
            user_response = user_simulator.respond()
            logger.info(f"User: {user_response}")

            # Send to agent and get next response
            response = user_simulator.continue_conversation(user_response, debug=debug)
            logger.info(f"Agent: {response.utterance.text if response.utterance else 'No response'}")

            turn_count += 1

            # Check if conversation should end
            if response.is_complete or (response.utterance and response.utterance.is_final):
                logger.info("Conversation completed")
                break

        # Print conversation summary
        history = user_simulator.get_conversation_history()
        logger.info(f"\nConversation Summary:")
        logger.info(f"  Total turns: {turn_count}")
        logger.info(f"  History length: {len(history)}")
        logger.info(f"  Status: {'Completed' if not user_simulator.is_conversation_active() else 'In Progress'}")

        # Print full history
        logger.info(f"\nConversation History:")
        for i, msg in enumerate(history):
            logger.info(f"  [{i}] {msg['role']}: {msg['content'][:100]}...")

    except Exception as e:
        logger.error(f"Error during conversation: {e}", exc_info=True)
    finally:
        # Cleanup
        user_simulator.end_conversation()
        api_client.close()
        logger.info("Conversation ended and resources cleaned up")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", action="store_true")
    args = parser.parse_args()

    main(debug=args.debug)