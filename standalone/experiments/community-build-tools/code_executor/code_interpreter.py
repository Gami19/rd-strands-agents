from strands import Agent
from strands_tools.code_interpreter import AgentCoreCodeInterpreter

# Create the code interpreter tool
bedrock_agent_core_code_interpreter = AgentCoreCodeInterpreter(region="us-west-2")
agent = Agent(tools=[bedrock_agent_core_code_interpreter.code_interpreter])

# Create a session
agent.tool.code_interpreter({
    "action": {
        "type": "initSession",
        "description": "Data analysis session",
        "session_name": "analysis-session"
    }
})

# Execute Python code
agent.tool.code_interpreter({
    "action": {
        "type": "executeCode",
        "session_name": "analysis-session",
        "code": "print('Hello from sandbox!')",
        "language": "python"
    }
})