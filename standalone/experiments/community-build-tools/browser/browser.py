import os

from strands import Agent
from strands_tools.browser import AgentCoreBrowser

browser_tool = AgentCoreBrowser()

def create_agent() -> Agent:
    os.getenv("BYPASS_TOOL_CONSENT")

    return Agent(
        model=os.getenv("us.anthropic.claude-sonnet-4-20250514-v1:0"),
        tools=[browser_tool.browser],
        system_prompt=(
            "You are a helpful assistant. Prefer using tools when they make tasks "
            "more reliable or reproducible."
        ),
    )


def main() -> None:
    agent = create_agent()

    demo_query_web = (
        "ブラウザを使用して、最新のAWSニュースブログのタイトルを取得してください。"
    )
    result = agent(demo_query_web)
    print(result)


if __name__ == "__main__":
    main()