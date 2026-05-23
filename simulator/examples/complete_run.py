import argparse
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

from simulator.src.api_client import SimulatorAPIClient
from simulator.src.persona import PersonaRegistry
from simulator.src.response_strategies import RandomStrategy
from simulator.src.user_simulator import UserSimulator

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
base_url = os.getenv("BASE_URL")
team_name = os.getenv("TEAM_NAME")
auth_token = os.getenv("AUTH_TOKEN")
run_id = "test_run_001"
description = "this is a test run"

personas_path = Path(__file__).resolve().parents[1] / "personas.example.json"

if not base_url or not team_name or not auth_token:
    raise ValueError(
        "BASE_URL, TEAM_NAME, and AUTH_TOKEN must be set in the environment or .env file."
    )

def main(
    debug: bool = False,
    run_id: str = run_id,
    description: str = description,
):
    api_client = SimulatorAPIClient(
        base_url=base_url,
        team_id=team_name,
        auth_token=auth_token,
    )

    persona_registry = PersonaRegistry()
    persona_registry.load_from_file(personas_path)
    persona = persona_registry.get_persona("persona_001")

    response_strategy = RandomStrategy()

    user_simulator = UserSimulator(
        api_client=api_client,
        persona=persona,
        response_strategy=response_strategy,
    )

    try:
        metrics = user_simulator.complete_run(
            run_id=run_id,
            description=description,
            run_path=Path("runs"),
            debug=debug,
        )
        logging.info(f"Run completed. Metrics: {metrics}")
    finally:
        user_simulator.end_conversation()
        api_client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", action="store_true")
    parser.add_argument("--run-id", default=run_id, help="Run identifier")
    parser.add_argument(
        "--description",
        default=description,
        help="Description for the run",
    )
    args = parser.parse_args()

    main(debug=args.debug, run_id=args.run_id, description=args.description)
