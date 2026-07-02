import argparse
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

from simulator.src.api_client import SimulatorAPIClient
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

if not base_url or not team_name or not auth_token:
    raise ValueError(
        "BASE_URL, TEAM_NAME, and AUTH_TOKEN must be set in the environment or .env file."
    )

def main(
    debug: bool = False,
    run_id: str = run_id,
    description: str = description,
    task_name: str = "task2",
):
    api_client = SimulatorAPIClient(
        base_url=base_url,
        team_id=team_name,
        auth_token=auth_token,
    )

    response_strategy = RandomStrategy()

    # Initialize simulator without a persona; it will be set from the API response
    user_simulator = UserSimulator(
        api_client=api_client,
        response_strategy=response_strategy,
    )

    try:
        metrics = user_simulator.complete_run(
            run_id=run_id,
            description=description,
            task_name=task_name,
            run_path=Path("runs") if not debug else None, # do not dump runs in debug mode
            debug=debug,
        )
        logging.info(f"Run completed. Metrics: {metrics}")
    finally:
        user_simulator.end_conversation()
        api_client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--task",
        default="task2",
        choices=["task1", "task2"],
        help="Task name (task1 for next utterance prediction, task2 for full conversation)",
    )
    parser.add_argument("-d", "--debug", action="store_true")
    parser.add_argument("--run-id", default=run_id, help="Run identifier")
    parser.add_argument(
        "--description",
        default=description,
        help="Description for the run",
    )
    args = parser.parse_args()

    main(debug=args.debug, run_id=args.run_id, description=args.description, task_name=args.task)
