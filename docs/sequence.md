You can edit the diagram directly is this file or with the help of the [mermaid online editor](https://mermaid.ai/live/edit#pako:eNrdVltv2jAU_itH3kvR0pZrB9FUqaOt1Je1KuxlQkJucqDWEjuznd4Q_33HDgRIoS3ansYDiuPvfOfqz5mxSMXIQmbwd44ywnPBp5qnIwn0y7i2IhIZlxYGIs0TbpUGbuCHQU0v4KCfCJS29hp-dnPlgLcXg6F_PoZvPPqFMt4CnRKFA_fPRrLY_q4sgnpAvXIbeFgIA0umYPK7VBgjlASdy6VZCT48PSWnIdxck_tjQhwbZ1agPrmAHKIgvJLCCp6IF3RU8PVOn8LBRGhDXiKUXAsVQLGOlKSYDLfkt1aSOZrDpcdLD-Q-pdxa1JyKCgcqczY8qa2HQDZlxOEG-VjE8LnKUi2N9_d30b-OYmkEDYjRRFr4wJcFTpTKoL_GA8NcS1NsvtMBcm-FzHERoymQGENOwwQaTaakwdqKa6NLBc9E6Ueu4_Gqsp7ssnhdMFXq5Zk2WvQdn-z22u5Tkl398SNePPLEwjlmCbos7_J4inblpzI4q41Kg_sql-QA8ClCjDEOQKxaLvFxo61vpTFYptGspIFpZp93laLSAMpuvO4QtsW95vQWDdIkltpBx9Di1lwLLwW-KOwaFhODawp0IWOzMYb7DeBMmPFE0GkMYahznC8mcnh9fk0HKqWGpc4_5ZopUarb_1fVjygRRIkyGL-aba8EJc1WvXbVL9RauhNXHqOtA_tx4ajOvFtYcrBq07acqlaksCV-j67uko1_plV7SNUbl-QtZsgtTNxtnSSgJmDvCUt_uuyDKXu66OO7V-9VQePuGWGomqmXtsC_pGwevIxbuhCA-zHLHShGaDe7H7ihl23edTN5FhawqRYxCy0d3IClqFPulmzmzEaMQklxxEJ6jHHC88SO2EjOyYw-NX4qlS4ttcqn9yyccFKWgOVZTKdi8e1TQqg0qL3-srDjGVg4Y08sbHTaR616vdOu99rdbqfdot1nFh6edBtHjV6n9aXdaLaa9VZvHrAX77R5VG-edOsnnV6zR5vd9vwPKsMaZQ). 

```mermaid
sequenceDiagram
    participant Simulator as UserSim (Client)
    participant API as REST API / Backend
    participant Agent as CA

    Note over Simulator,Agent: Start submission run

    Simulator->>API: POST /run/start
    # API->>Agent: Initialize run <br> (first scenario, first conversation)
    # Agent-->>API: First agent utterance (optional)
    # API-->>Simulator: conversation_id + agent utterance
    Note over API: Initialize run <br> (first scenario, first conversation)
    API-->>Simulator: scenario 1 description

    loop Conversation Turns
        Simulator->>API: POST /run/continue <br> (simulated user response)
        API->>Agent: POST /forward_utterance <br> Forward user utterance
        Agent-->>API: Next agent utterance
        API-->>Simulator: scenario 1 description + agent utterance
    end

    alt Depleted budget
        # Agent-->>API:
        Note over API: Counter exceeded, initialize new conversation
        API-->>Simulator: Scenario 2 description + empty utterance
        API->>Agent: POST /end_conversation 
        Note over Simulator: Reset simulator state
        Note over Agent: Reset agent state
    else Simulator Ends Conversation
        Simulator->>API: POST /run/continue {is_final: True} <br> (TODO: Implement endpoint)
        API-->>Simulator: Scenario 2 description + empty utterance
        API->>Agent: POST /end_conversation 
        Note over Simulator: Reset simulator state
        Note over Agent: Reset agent state
        # API-->>Simulator: conversation closed
    end

    loop 
       Note over Simulator,API: Start next scenario conversation
       Simulator->>API: POST /run/continue <br> (new conversation context)
       # API-->>Simulator: new conversation_id
       API-->>Simulator: Scenario 2 description + agent utterance
       API->>Agent: POST /forward_utterance <br> Forward user utterance
       Agent-->>API: Next agent utterance
       Note over Simulator,Agent: Repeat for all of the other scenarios
    end 
    
    Note over Simulator,Agent: If the run is complete, the server return a status code 428

    Simulator->>API: POST /run/continue
    API-->>Simulator: 428
```