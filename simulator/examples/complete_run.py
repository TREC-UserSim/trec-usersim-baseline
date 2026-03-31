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

def main():
    api_client = SimulatorAPIClient(
        base_url= base_url,
        team_id=team_name,
        auth_token=auth_token,
    )

    persona_registry = PersonaRegistry()
    persona_registry.load_from_file("simulator/personas.example.json")
    persona = persona_registry.get_persona("persona_001")

    response_strategy = RandomStrategy()

    user_simulator = UserSimulator(
        api_client=api_client,
        persona=persona,
        response_strategy=response_strategy,
    )

    metrics = user_simulator.complete_run(run_id=run_id, description=description, run_path=Path("runs"))
    logging.info(f"Run completed. Metrics: {metrics}")

if __name__ == "__main__":
    main()
