import os
import sys
import subprocess
import json
from pathlib import Path
import inspect
import base64
import dill

def serialize_agent(agent, seen=None):
    if seen is None:
        seen = set()
        
    if agent.name in seen:
        return agent.name
        
    # Serialize functions using dill
    serialized_functions = []
    for func in agent.functions:
        func_code = inspect.getsource(func)
        serialized_func = base64.b64encode(dill.dumps(func)).decode('utf-8')
        serialized_functions.append({
            'name': func.__name__,
            'source': func_code,
            'serialized': serialized_func
        })
    
    agent_dict = {
        'name': agent.name,
        'model': agent.model,
        'instructions': agent.instructions,
        'functions': serialized_functions,
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