# test_a2a.py
import asyncio
import httpx
import json
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import MessageSendParams, SendMessageRequest
from uuid import uuid4

async def test_a2a_discovery():
    """A2Aエージェントの発見テスト"""
    print("Testing A2A agent discovery...")
    
    async with httpx.AsyncClient() as client:
        # FAQエージェントの発見
        try:
            resolver = A2ACardResolver(
                httpx_client=client, 
                base_url="http://localhost:9002"
            )
            agent_card = await resolver.get_agent_card()
            print(f"✅ FAQ Agent discovered: {agent_card.name}")
            print(f"   Description: {agent_card.description}")
        except Exception as e:
            print(f"❌ FAQ Agent discovery failed: {e}")
        
        # Expertエージェントの発見
        try:
            resolver = A2ACardResolver(
                httpx_client=client, 
                base_url="http://localhost:9003"
            )
            agent_card = await resolver.get_agent_card()
            print(f"✅ Expert Agent discovered: {agent_card.name}")
            print(f"   Description: {agent_card.description}")
        except Exception as e:
            print(f"❌ Expert Agent discovery failed: {e}")
        
        # Generalエージェントの発見
        try:
            resolver = A2ACardResolver(
                httpx_client=client, 
                base_url="http://localhost:9004"
            )
            agent_card = await resolver.get_agent_card()
            print(f"✅ General Agent discovered: {agent_card.name}")
            print(f"   Description: {agent_card.description}")
        except Exception as e:
            print(f"❌ General Agent discovery failed: {e}")
        
        # Workflowコーディネーターの発見
        try:
            resolver = A2ACardResolver(
                httpx_client=client, 
                base_url="http://localhost:9005"
            )
            agent_card = await resolver.get_agent_card()
            print(f"✅ Workflow Coordinator discovered: {agent_card.name}")
            print(f"   Description: {agent_card.description}")
        except Exception as e:
            print(f"❌ Workflow Coordinator discovery failed: {e}")

async def test_a2a_communication():
    """A2Aエージェントとの通信テスト"""
    print("\nTesting A2A communication...")
    
    async with httpx.AsyncClient() as client:
        # FAQエージェントとの通信
        try:
            resolver = A2ACardResolver(
                httpx_client=client, 
                base_url="http://localhost:9002"
            )
            agent_card = await resolver.get_agent_card()
            
            a2a_client = A2AClient(httpx_client=client, agent_card=agent_card)
            
            # メッセージの送信
            payload = {
                "message": {
                    "role": "user",
                    "parts": [{"kind": "text", "text": "AIについて教えてください"}],
                    "messageId": str(uuid4()),
                }
            }
            
            request = SendMessageRequest(
                id=str(uuid4()), 
                params=MessageSendParams(**payload)
            )
            
            response = await a2a_client.send_message(request)
            print(f"✅ FAQ Agent response: {str(response)[:100]}...")
            
        except Exception as e:
            print(f"❌ FAQ Agent communication failed: {e}")
        
        # Expertエージェントとの通信
        try:
            resolver = A2ACardResolver(
                httpx_client=client, 
                base_url="http://localhost:9003"
            )
            agent_card = await resolver.get_agent_card()
            
            a2a_client = A2AClient(httpx_client=client, agent_card=agent_card)
            
            payload = {
                "message": {
                    "role": "user",
                    "parts": [{"kind": "text", "text": "機械学習の最新トレンドについて詳しく分析してください"}],
                    "messageId": str(uuid4()),
                }
            }
            
            request = SendMessageRequest(
                id=str(uuid4()), 
                params=MessageSendParams(**payload)
            )
            
            response = await a2a_client.send_message(request)
            print(f"✅ Expert Agent response: {str(response)[:100]}...")
            
        except Exception as e:
            print(f"❌ Expert Agent communication failed: {e}")

async def test_a2a_streaming():
    """A2Aエージェントとのストリーミング通信テスト"""
    print("\nTesting A2A streaming communication...")
    
    async with httpx.AsyncClient() as client:
        try:
            resolver = A2ACardResolver(
                httpx_client=client, 
                base_url="http://localhost:9002"
            )
            agent_card = await resolver.get_agent_card()
            
            a2a_client = A2AClient(httpx_client=client, agent_card=agent_card)
            
            payload = {
                "message": {
                    "role": "user",
                    "parts": [{"kind": "text", "text": "量子コンピューティングの基本概念を段階的に説明してください"}],
                    "messageId": str(uuid4()),
                }
            }
            
            from a2a.types import SendStreamingMessageRequest
            request = SendStreamingMessageRequest(
                id=str(uuid4()), 
                params=MessageSendParams(**payload)
            )
            
            print("Streaming response:")
            async for event in a2a_client.send_message_streaming(request):
                print(f"   {event.model_dump_json(exclude_none=True, indent=2)}")
                
        except Exception as e:
            print(f"❌ Streaming communication failed: {e}")

async def test_main_api_endpoints():
    """メインAPIエンドポイントのテスト"""
    print("\nTesting main API endpoints...")
    
    async with httpx.AsyncClient() as client:
        # ヘルスチェック
        try:
            response = await client.get("http://localhost:8000/health")
            print(f"✅ Health check: {response.json()}")
        except Exception as e:
            print(f"❌ Health check failed: {e}")
        
        # A2Aエージェント発見
        try:
            response = await client.get("http://localhost:8000/a2a/discover")
            print(f"✅ A2A discovery: {response.json()}")
        except Exception as e:
            print(f"❌ A2A discovery failed: {e}")
        
        # チャットエンドポイント
        try:
            chat_data = {
                "query": "AIの未来について教えてください",
                "use_a2a": True,
                "workflow_type": "workflow"
            }
            response = await client.post("http://localhost:8000/chat", json=chat_data)
            print(f"✅ Chat endpoint: {response.json()}")
        except Exception as e:
            print(f"❌ Chat endpoint failed: {e}")
        
        # Graphワークフロー
        try:
            graph_data = {
                "query": "量子コンピューティングの研究と分析を行ってください",
                "workflow_type": "sequential"
            }
            response = await client.post("http://localhost:8000/graph", json=graph_data)
            print(f"✅ Graph workflow: {response.json()}")
        except Exception as e:
            print(f"❌ Graph workflow failed: {e}")

async def main():
    """メインテスト関数"""
    print("�� Starting A2A Multi-Agent System Tests")
    print("=" * 50)
    
    # A2Aサーバーが起動するまで少し待機
    print("Waiting for A2A servers to start...")
    await asyncio.sleep(5)
    
    # テストの実行
    await test_a2a_discovery()
    await test_a2a_communication()
    await test_a2a_streaming()
    await test_main_api_endpoints()
    
    print("\n" + "=" * 50)
    print("✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
```

```

