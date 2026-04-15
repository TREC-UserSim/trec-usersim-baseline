# TREC UserSim Baseline Simulator

> [!WARNING]
> This project is in early stage. Expect changes and improvements as development continues.

**Setup.**  
1. Create virtual environment and install the required packages in `simulator/requirements.txt`

2. Create a `.env` file (adapt `.env.example` in this repository). Specifically, add `BASE_URL` (address of the backend infrastructure) and assign your team name to `TEAM_NAME`. Upon registration, you receive an authentication token, make sure to include it in `AUTH_TOKEN`.

**Example #1.** 
Run a single conversation with `single_conversation.py`.
```
python -m simulator.examples.single_conversation
```

Before running the script, make sure you have access to an LLM and update the variables `LLM_MODEL` and `LLM_API_BASE` in `.env` accordingly. Alternatively, implement your own LLMStrategy.

**Example #2.**
Complete a run submission with `complete_run.py`.
```
python -m simulator.examples.complete_run
```
This example will make use of a simulator with predefined utterances.

> [!NOTE]
> The documentation features:
> - [a sequence diagram of a run submission](./docs/sequence.md)
> - [the conceptual model of the user simulator](./docs/user_simulator.md).
