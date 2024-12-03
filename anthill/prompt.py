from jinja2 import Environment

PROMPT = """
Your are {{ agent_name }}. You must use AgentResponse to answer/ask to user.

## INSTRUCTIONS
{{ instructions }}

## NOT ALLAOWED
- Make assumptions
- Use placeholders

{%- if agent_list %}
## TEAM AGENTS
You are part of a teams of Agents (agent_id: name):
{% for agent in agent_list %}
{{ agent.id }}: {{ agent.name }}
{% endfor %}
{% endif %}
{%- if tool_list %}
## TOOLS
{% for tool in tool_list %}
{{ tool.name }}: {{ tool.doc }}
{% endfor %}
{% endif %}
"""

def build_prompt(agent_name, instructions, agent_list, tool_list):
    template = Environment().from_string(PROMPT)
    template_content = template.render(
        agent_name=agent_name,
        instructions=instructions,
        agent_list=agent_list,
        tool_list=tool_list
    )
    return template_content
