from strands import Agent
from strands_tools import diagram
import os
from dotenv import load_dotenv

load_dotenv()

agent = Agent(tools=[diagram])

# 簡単なテスト
try:
    result = agent.tool.diagram(
        diagram_type="cloud",
        nodes=[{"id": "test", "type": "Test", "label": "Test Node"}],
        edges=[],
        title="Test Diagram"
    )
    print("✅ ツールが正常に動作しました")
    print(f"結果: {result}")
except Exception as e:
    print(f"❌ エラーが発生しました: {e}")

result = agent.tool.diagram(
    diagram_type="class",
    elements=[
        {
            "name": "User",
            "attributes": ["+id: int", "-name: string", "#email: string"],
            "methods": ["+login(): bool", "+logout(): void"]
        },
        {
            "name": "Order",
            "attributes": ["+id: int", "-items: List", "-total: float"],
            "methods": ["+addItem(item): void", "+calculateTotal(): float"]
        }
    ],
    relationships=[
        {"from": "User", "to": "Order", "type": "association", "multiplicity": "1..*"}
    ],
    title="E-commerce Domain Model"
)