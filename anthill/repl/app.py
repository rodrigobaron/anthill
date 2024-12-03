import os
import sys
import subprocess
import json
from pathlib import Path

def serialize_agent(agent, seen=None):
    """
    Serialize an Agent object to a JSON string, handling circular references.
    
    Args:
        agent: The agent to serialize
        seen: Set of agent names already processed to avoid cycles
    """
    if seen is None:
        seen = set()
        
    # If we've seen this agent before, just return its name
    if agent.name in seen:
        return agent.name
        
    # Add this agent to seen set
    seen.add(agent.name)
    
    # Create serializable dict
    agent_dict = {
        'name': agent.name,
        'model': agent.model,
        'instructions': agent.instructions,
        'functions': [f.__name__ for f in agent.functions],
        'transfers': [serialize_agent(a, seen) for a in agent.transfers],
        'model_params': agent.model_params
    }
    
    return json.dumps(agent_dict)

def run_demo_app(starting_agent, client=None, context_variables=None, debug=False):
    """
    Launches the Streamlit chat application in a separate process.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(current_dir, "streamlit_chat_app.py")
    
    # Serialize the agent to JSON
    agent_json = serialize_agent(starting_agent)
    
    cmd = [
        sys.executable,
        "-m", "streamlit",
        "run",
        app_path,
        "--",
        "--agent", agent_json,
        "--debug", str(debug).lower()
    ]
    
    if client is not None:
        cmd.extend(["--client", str(client)])
    if context_variables is not None:
        cmd.extend(["--context", json.dumps(context_variables)])
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nShutting down Anthill Chat...")
    except Exception as e:
        print(f"Error starting Anthill Chat: {e}")
        sys.exit(1)