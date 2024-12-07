from jinja2 import Environment

PROMPT = """
Your are {{ agent_name }}. You must use agent_response tool to answer/ask to user and use transfer tools when is not related to your topic.

## INSTRUCTIONS
{{ instructions }}

## NOT ALLAOWED
- Make assumptions
- Use placeholders
- Saying you will use tools. E.g: I'll need to ...

## TEAM AGENTS
You are part of a team of agents, if any transfer tool/function are available use it to transfer to you team.

{%- if tool_list %}
## TOOLS/FUNCTIONS
{% for tool in tool_list %}
{{ tool.name }}: {{ tool.doc }}
{% endfor %}
{% endif %}
"""

def build_prompt(agent_name, instructions, tool_list):
    template = Environment().from_string(PROMPT)
    template_content = template.render(
        agent_name=agent_name,
        instructions=instructions,
        tool_list=tool_list
    )
    return template_content
