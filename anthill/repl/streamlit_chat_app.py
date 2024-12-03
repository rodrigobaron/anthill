import streamlit as st
import json
import argparse
from anthill import Anthill
from anthill.types import Message, Agent

class AgentRegistry:
    """Keep track of all agents to handle circular references"""
    def __init__(self):
        self.agents = {}
    
    def register(self, agent):
        self.agents[agent.name] = agent
        return agent
    
    def get(self, name):
        return self.agents.get(name)

def deserialize_agent(agent_json, registry=None):
    """
    Deserialize a JSON string back to an Agent object, handling circular references.
    
    Args:
        agent_json: JSON string or agent name
        registry: AgentRegistry instance to track created agents
    """
    if registry is None:
        registry = AgentRegistry()
    
    # If it's just a name, return the registered agent
    try:
        data = json.loads(agent_json)
    except json.JSONDecodeError:
        # This must be an agent name reference
        return registry.get(agent_json)
    
    # Check if we already created this agent
    if data['name'] in registry.agents:
        return registry.get(data['name'])
    
    # Create new Agent instance
    agent = Agent(
        name=data['name'],
        model=data['model'],
        instructions=data['instructions'],
        functions=[],  # Handle functions as needed
        transfers=[],  # We'll set transfers after creating the agent
        model_params=data['model_params']
    )
    
    # Register the agent before processing transfers to handle circular refs
    registry.register(agent)
    
    # Now process transfers
    agent.transfers = [deserialize_agent(a, registry) for a in data['transfers']]
    
    return agent

def parse_args():
    parser = argparse.ArgumentParser(description='Anthill Chat App')
    parser.add_argument('--agent', required=True, help='Starting agent as JSON')
    parser.add_argument('--client', help='Custom client')
    parser.add_argument('--context', help='Context variables as JSON')
    parser.add_argument('--debug', type=bool, default=False, help='Enable debug mode')
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "agent" not in st.session_state:
        st.session_state.agent = deserialize_agent(args.agent)
    if "ant_client" not in st.session_state:
        st.session_state.ant_client = Anthill(client=args.client)

    st.title("Anthill Chat 🐜")

    # Display existing messages
    for message in st.session_state.messages:
        if message["role"] == "user":
            with st.chat_message("user"):
                st.write(message["content"])
        elif message["role"] == "assistant":
            with st.chat_message("assistant"):
                if message.get("content"):
                    st.write(f"{message["sender"]}: {message["content"]}")
                for tool_call in message.get("tool_calls", []) or []:
                    name, tool_args = tool_call["name"], tool_call["arguments"]
                    arg_str = json.dumps(tool_args).replace(":", "=")
                    st.info(f"{name}({arg_str[1:-1]})")

    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        # Add and display user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        # Parse context variables if provided
        context_vars = {}
        if args.context:
            context_vars = json.loads(args.context)
        
        # Get response from Anthill
        response = st.session_state.ant_client.run(
            agent=st.session_state.agent,
            messages=st.session_state.messages,
            context_variables=context_vars,
            stream=True,
            debug=args.debug
        )
        
        
        # Process streaming response
        content = ""
        response_data = None
        for chunk in response:
            if isinstance(chunk, Message):
                if chunk.sender and content == "":
                    content = f"{chunk.sender}: "
                if chunk.content:
                    content += chunk.content
                    with st.chat_message("assistant"):
                        st.write(content)
                
                for tool_call in chunk.tool_calls or []:
                    with st.chat_message("assistant"):
                        name, tool_args = tool_call["name"], tool_call["arguments"]
                        arg_str = tool_args.model_dump_json().replace(":", "=")
                        st.info(f"{name}({arg_str[1:-1]})")
                        if name == "TransferToAgent":
                            content = ""
            
            if "response" in chunk:
                response_data = chunk["response"]
                break
        
        if response_data:
            st.session_state.messages.extend(response_data.messages)
            st.session_state.agent = response_data.agent

if __name__ == "__main__":
    main()