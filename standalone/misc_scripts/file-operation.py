from strands import Agent
from strands_tools import file_read, file_write, editor

agent = Agent(tools=[file_read, file_write, editor])

agent.tool.file_read(path="config.json")
agent.tool.file_write(path="./samples/outputs/output.txt", content="Hello, world!")
agent.tool.editor(command="view", path="./outputs/script.py")