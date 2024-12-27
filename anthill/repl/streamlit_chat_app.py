import streamlit as st
import json
import argparse
from anthill import Anthill
from anthill.types import Message, Agent
import base64
import dill

def deserialize_agent(agent_json):
    data = json.loads(agent_json)
    
    # Deserialize functions
    functions = []
    for func_data in data['functions']:
        func = dill.loads(base64.b64decode(func_data['serialized']))
        functions.append(func)
    
    agent = Agent(
        name=data['name'],
        model=data['model'],
        instructions=data['instructions'],
        functions=functions,
        model_params=data['model_params']
    )
    
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
        
        response_data = None
        with st.chat_message("assistant"):
            tool_placeholder = st.empty()
            content_placeholder = st.empty()
            tool_calls = []
            for chunk in response:
                if isinstance(chunk, Message):
                    if chunk.content:
                        content_placeholder.write(f"{chunk.sender}: {chunk.content}")
                    
                    for tool_call in chunk.tool_calls or []:
                        name, tool_args = tool_call["name"], tool_call["arguments"]
                        arg_str = json.dumps(tool_args).replace(":", "=")
                        tool_calls.append(f"{name}({arg_str[1:-1]})")
                        tool_placeholder.info(tool_calls)
                
                if "response" in chunk:
                    response_data = chunk["response"]
                    break
        
        if response_data:
            st.session_state.messages.extend(response_data.messages)
            st.session_state.agent = response_data.agent

if __name__ == "__main__":
    main()