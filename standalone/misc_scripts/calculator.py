from strands import Agent
from strands_tools import calculator

agent = Agent(tools=[calculator])
response = agent.tool.calculator(
    expression="sin(x)/cos(x)",
    mode="integrate",
    wrt="x"
)
for item in response['content']:
    print(item['text']) 

