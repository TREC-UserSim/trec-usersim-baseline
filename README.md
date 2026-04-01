# TREC UserSim - Baseline Simulator

> [!WARNING]
> This project is in early stage. Expect changes and improvements as development continues.

**Setup.**  
1. Clone and run the infrastructure. 
```
git clone https://github.com/irgroup/trec-usersim-infra
cd trec-usersim-infra/
docker compose up -d 
```

2. Prepare the `.env` (adapt the `.env.example` in `trec-usersim-infra/`). Specifically, add `HF_TOKEN`, `BASE_URL`, `TEAM_NAME` and update `ADMIN_NAME` and `ADMIN_PASSWORD` if needed.
 
3. Create virtual environment and install the required packages in `simulator/requirements.txt`

4. Issue an authentication token and write it to the .env file with `issue_token.py`.
```
python -m simulator.examples.issue_token.py
```

**Example #1.** 
Run a single conversation with `single_conversation.py`.
```
python -m simulator.examples.single_conversation
```

**Example #2.**
Complete a run submission with `complete_run.py`.
```
python -m simulator.examples.complete_run
```
> [!NOTE]
> The wiki features a [sequence diagram of a run submission](https://github.com/irgroup/trec-usersim-baseline/wiki/Workflow-of-a-run-submission).
