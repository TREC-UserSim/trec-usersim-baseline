# TREC UserSim Baseline Simulator

> [!WARNING]
> This project is in early stage. Expect changes and improvements as development continues.

**Setup.**  
1. Create virtual environment and install the required packages in `simulator/requirements.txt`

2. Create a `.env` file (adapt `.env.example` in this repository). Specifically, make sure that `ADMIN_NAME` and `ADMIN_PASSWORD` are valid (i.e., registered on the backend infrastructure), and add `BASE_URL` (address of the backend infrastructure) and assign a team name to `TEAM_NAME`.
 
3. Issue an authentication token and write it to the `.env` file with `issue_token.py` (`AUTH_TOKEN` will be added to `.env`). 
```
python -m simulator.examples.issue_token
```
In case you have a valid authentication token available, you do not have to issue another one. However, you should make sure that it is included in the `.env` file.

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
