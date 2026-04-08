from strands import Agent
from strands_tools import python_repl
import os

# ツールの同意をバイパスする
os.environ["BYPASS_TOOL_CONSENT"] = "true"

agent = Agent(tools=[python_repl ])

agent("""\
Pythonで1〜100までの数字の合計を計算するプログラムを作成して。
そしてそれを実行して。\
""")