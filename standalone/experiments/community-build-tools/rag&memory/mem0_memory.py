import os
import logging
from dotenv import load_dotenv

from strands import Agent
from strands_tools import memory, use_llm

logger = logging.getLogger(__name__)

# Load environment variables from .env file if it exists
load_dotenv()

# Set AWS credentials and configuration
# os.environ["AWS_REGION"] = "us-west-2"
# os.environ['OPENSEARCH_HOST'] = "your-opensearch-host.us-west-2.aoss.amazonaws.com"
# os.environ['AWS_ACCESS_KEY_ID'] = "your-aws-access-key-id"
# os.environ['AWS_SECRET_ACCESS_KEY'] = "your-aws-secret-access-key"
USER_ID = "kumamon"

# System prompt for the memory agent
MEMORY_SYSTEM_PROMPT = f"""You are a personal assistant that maintains context by remembering user details.

Capabilities:
- Store new information using mem0_memory tool (action="store")
- Retrieve relevant memories (action="retrieve")
- List all memories (action="list")
- Provide personalized responses

Key Rules:
- Always include user_id={USER_ID} in tool calls
- Be conversational and natural in responses
- Format output clearly
- Acknowledge stored information
- Only share relevant information
- Politely indicate when information is unavailable
"""

# Create an agent with memory capabilities
memory_agent = Agent(
    system_prompt=MEMORY_SYSTEM_PROMPT,
    tools=[memory, use_llm],
)

# Initialize some demo memories
def initialize_demo_memories():
    content = "俺の名前は渋井丸拓男。略してシブタク（自称）。清潔感のない服装に出っ歯にケツアゴとお世辞にもかっこいいと言えないチンピラ。仲間からは『タク』と呼ばれている。Death Noteの作中での登場ページ数は僅か5ページ（8コマ）、アニメではたったの50秒にもかかわらず、その強烈な名前とキャラクター、作中での扱いから一部の読者にカルト的な人気があり、13巻のキャラ別性格判断チャートにも選ばれている他、アンサイクロペディアやアニヲタwikiに個別記事まであり、原作者大場つぐみも好きなキャラの一人に挙げている程である。"  # noqa
    memory_agent.tool.memory(action="store", content=content, user_id=USER_ID)

# Example usage
if __name__ == "__main__":
    print("\n🧠 Memory Agent 🧠\n")
    print("情報の記憶と取得")
    print("\nOptions:")
    print("渋井丸拓男とは？")
    print("渋井丸拓男のニックネームは？")
    print("渋井丸拓男は何巻で死亡しますか？")

    # Interactive loop
    while True:
        try:
            user_input = input("\n> ")

            if user_input.lower() == "exit":
                print("\nGoodbye! 👋")
                break
            elif user_input.lower() == "demo":
                initialize_demo_memories()
                print("\nDemo memories initialized!")
                continue

            # Call the memory agent
            memory_agent(user_input)

        except KeyboardInterrupt:
            print("\n\nExecution interrupted. Exiting...")
            break
        except Exception as e:
            print(f"\nAn error occurred: {str(e)}")
            print("Please try a different request.")