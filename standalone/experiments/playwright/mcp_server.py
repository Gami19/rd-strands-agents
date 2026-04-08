import os
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import uvicorn
from typing import Dict, Optional, List, Any
import logging
import time
import traceback
import json
import subprocess
import sys
import re
from pathlib import Path
from enum import Enum
import requests
from urllib.parse import quote_plus
from dotenv import load_dotenv
load_dotenv()
# OpenAI APIを使用するためのインポート
import openai

## ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("mcp-server")

app = FastAPI(title="NLP-Enhanced Playwright MCP Server API", 
             description="自然言語クエリでPlaywrightを操作するためのサーバー", 
             version="1.0.0")

# 環境変数からAPIキーを取得 (Azure OpenAI用に修正)
AZURE_OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4")

if AZURE_OPENAI_API_KEY:
    # Azure OpenAI用の設定
    client = openai.AzureOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        api_version="2024-02-01",
        azure_endpoint=AZURE_OPENAI_ENDPOINT
    )
    logger.info("Azure OpenAI APIの設定が完了しました")
else:
    client = None
    logger.warning("AZURE OPENAI クライアントが設定されていません。自然言語処理機能は利用できません。")

# ブラウザタイプ
class BrowserType(str, Enum):
    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"

# リクエスト/レスポンスモデル
class BrowserOptions(BaseModel):
    headless: Optional[bool] = False
    browser_type: Optional[BrowserType] = BrowserType.CHROMIUM
    viewport: Optional[Dict[str, int]] = {"width": 1280, "height": 720}
    timeout: Optional[int] = 30000  # ミリ秒
    vision: Optional[bool] = False

class QueryRequest(BaseModel):
    url: Optional[str] = None
    selector: Optional[str] = None
    action: Optional[str] = None
    value: Optional[str] = None
    wait_for: Optional[str] = None
    script: Optional[str] = None
    timeout: Optional[int] = None

# 自然言語クエリのリクエストモデル
class NLPQueryRequest(BaseModel):
    query: str
    take_screenshot: Optional[bool] = True
    max_steps: Optional[int] = 5  # 最大ステップ数を制限

class ServerStatusResponse(BaseModel):
    is_running: bool
    browser_type: str
    headless: bool
    current_url: Optional[str] = None
    last_error: Optional[str] = None

# Playwright MCP サーバーマネージャー
class PlaywrightManager:
    def __init__(self):
        self.process = None
        self.is_running = False
        self.current_url = None
        self.last_error = None
        self.browser_agent = None
        self.options = {
            "headless": False,
            "browser_type": BrowserType.CHROMIUM,
            "viewport": {"width": 1280, "height": 720},
            "timeout": 30000,
            "vision": False
        }
        self.mcp_port = 8931  # MCPサーバーのポート
        self.history = []  # 操作履歴
        
        # 出力ディレクトリを作成
        self.output_dir = os.path.join(os.getcwd(), "mcp_output")
        os.makedirs(self.output_dir, exist_ok=True)  # existでのエラーを避けるためにexist_ok=Trueを設定
        
    def start(self):
        if self.is_running:
            logger.info("Playwright サーバーは既に実行中です")
            return True
            
        try:
            logger.info("Playwright MCP サーバーを起動しています...")
            
            # 引数リストを作成
            args = ["npx", "-y", "@playwright/mcp@latest", "--port", str(self.mcp_port)]
            if self.options["headless"]:
                args.append("--headless")
            if self.options["vision"]:
                args.append("--vision")
                
            # ブラウザタイプを指定
            args.extend(["--browser", self.options["browser_type"]])
            
            # 出力ディレクトリを指定
            args.extend(["--output-dir", self.output_dir])
            
            # サブプロセスとして起動
            env = os.environ.copy()
            self.process = subprocess.Popen(
                args,
                shell=True if sys.platform == 'win32' else False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env
            )
            
            # 初期化の待機
            time.sleep(5)  # サーバーの起動を待つ
            
            # 起動チェック
            if self.process.poll() is None:  # None は実行中を意味します
                self.is_running = True
                self.last_error = None
                logger.info(f"Playwright MCP サーバーが起動しました (PID: {self.process.pid})")
                return True
            else:
                stderr = self.process.stderr.read() if self.process.stderr else "N/A"
                self.last_error = f"サーバーの起動に失敗しました: {stderr}"
                logger.error(self.last_error)
                return False
                
        except Exception as e:
            self.last_error = f"サーバー起動中にエラーが発生しました: {str(e)}"
            logger.error(self.last_error)
            traceback.print_exc()
            return False
    
    def stop(self):
        if not self.is_running or self.process is None:
            logger.info("Playwright サーバーは既に停止しています")
            return True
            
        try:
            logger.info("Playwright MCP サーバーを停止しています...")
            
            # ブラウザを閉じる
            self._execute_mcp_command("browser_close", {})
            
            # プロセスを終了
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                
            self.process = None
            self.is_running = False
            self.current_url = None
            logger.info("Playwright MCP サーバーが停止しました")
            return True
            
        except Exception as e:
            self.last_error = f"サーバー停止中にエラーが発生しました: {str(e)}"
            logger.error(self.last_error)
            traceback.print_exc()
            return False
    
    def restart(self):
        logger.info("Playwright MCP サーバーを再起動しています...")
        self.stop()
        return self.start()
    
    def update_options(self, options):
        """オプションを更新し、必要に応じてサーバーを再起動"""
        needs_restart = False
        
        # 設定を更新
        if options.headless is not None:
            if self.options["headless"] != options.headless:
                self.options["headless"] = options.headless
                needs_restart = True
                
        if options.browser_type:
            if self.options["browser_type"] != options.browser_type:
                self.options["browser_type"] = options.browser_type
                needs_restart = True
                
        if options.viewport:
            self.options["viewport"] = options.viewport
            if self.is_running:
                # ブラウザのサイズを変更
                self._execute_mcp_command("browser_resize", {
                    "width": options.viewport["width"],
                    "height": options.viewport["height"]
                })
            
        if options.timeout:
            self.options["timeout"] = options.timeout
            
        if options.vision is not None:
            if self.options["vision"] != options.vision:
                self.options["vision"] = options.vision
                needs_restart = True
        
        # 再起動が必要な場合は実施
        if needs_restart and self.is_running:
            return self.restart()
        
        return True
    
    def _execute_mcp_command(self, command, params):
        """MCPサーバーにコマンドを送信する"""
        try:
            url = f"http://localhost:{self.mcp_port}/sse/call"
            data = {
                "method": command,
                "params": params
            }
            
            logger.info(f"MCP Command: {command} - Params: {json.dumps(params)}")
            
            response = requests.post(url, json=data)
            response.raise_for_status()
            result = response.json()
            
            # 履歴に追加
            self.history.append({
                "command": command,
                "params": params,
                "result": result,
                "timestamp": time.time()
            })
            
            # 現在のURLを更新（可能な場合）
            if command == "browser_navigate" and "url" in params:
                self.current_url = params["url"]
            
            logger.info(f"MCP Response: {json.dumps(result)[:200]}...")
            return result
        except Exception as e:
            logger.error(f"MCP Command execution error: {str(e)}")
            self.last_error = str(e)
            raise
    
    def get_snapshot(self):
        """現在のページのスナップショットを取得"""
        try:
            return self._execute_mcp_command("browser_snapshot", {})
        except Exception as e:
            logger.error(f"スナップショット取得エラー: {str(e)}")
            return None
    
    def navigate_to(self, url):
        """指定URLに移動"""
        if not url.startswith(('http://', 'https://')):
            url = f"https://{url}"
        
        return self._execute_mcp_command("browser_navigate", {"url": url})
    
    def take_screenshot(self):
        """スクリーンショットを撮影"""
        timestamp = int(time.time())
        filename = f"screenshot_{timestamp}.png"
        
        result = self._execute_mcp_command("browser_take_screenshot", {
            "filename": filename
        })
        
        return result
    
    def click_element(self, element_desc, ref):
        """要素をクリック"""
        return self._execute_mcp_command("browser_click", {
            "element": element_desc,
            "ref": ref
        })
    
    def type_text(self, element_desc, ref, text, submit=False):
        """テキストを入力"""
        return self._execute_mcp_command("browser_type", {
            "element": element_desc,
            "ref": ref,
            "text": text,
            "submit": submit
        })
    
    def search_google(self, query):
        """Googleで検索を実行"""
        # Googleに移動
        self.navigate_to("https://www.google.com")
        time.sleep(1)
        
        # スナップショットを取得して検索ボックスを探す
        snapshot = self.get_snapshot()
        
        # 検索ボックスを見つける
        search_box = None
        for node in snapshot.get("content", {}).get("children", []):
            if node.get("role") == "textbox" and ("search" in (node.get("name", "") or "").lower() or "検索" in (node.get("name", "") or "")):
                search_box = node
                break
        
        if not search_box:
            logger.error("検索ボックスが見つかりませんでした")
            return False
        
        # 検索ボックスに入力
        self.type_text("検索ボックス", search_box.get("ref"), query, submit=True)
        time.sleep(1)
        
        return True
    
    def process_nlp_query(self, query, take_screenshot=True, max_steps=5):
        """自然言語クエリを処理"""
        if not self.is_running:
            logger.error("MCPサーバーが起動していません")
            return {"error": "MCPサーバーが起動していません"}
        
        if not client:
            logger.error("Azure OpenAI クライアントが設定されていません")
            return {"error": "Azure OpenAI クライアントが設定されていません"}
        
        try:
            # クエリを解析
            steps = self.analyze_query(query, max_steps)
            
            results = []
            screenshots = []
            
            # ステップを実行
            for i, step in enumerate(steps):
                logger.info(f"実行ステップ {i+1}/{len(steps)}: {step['action']} - {step.get('description', '')}")
                
                # アクションに基づいて処理
                action_result = self.execute_action(step)
                results.append({
                    "step": i+1,
                    "action": step["action"],
                    "description": step.get("description", ""),
                    "result": action_result
                })
                
                # スクリーンショットを撮影
                if take_screenshot:
                    try:
                        screenshot = self.take_screenshot()
                        if "filename" in screenshot:
                            screenshots.append(screenshot["filename"])
                    except Exception as e:
                        logger.error(f"スクリーンショット取得エラー: {str(e)}")
                
                # 次のステップに移る前に少し待機
                time.sleep(1)
            
            return {
                "success": True,
                "steps_executed": len(results),
                "results": results,
                "screenshots": screenshots,
                "final_url": self.current_url
            }
            
        except Exception as e:
            logger.error(f"自然言語クエリ処理エラー: {str(e)}")
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "current_url": self.current_url
            }
    
    def analyze_query(self, query, max_steps=5):
        """自然言語クエリを分析し、実行ステップに変換"""
        try:
            system_prompt = """
            あなたはウェブブラウザを操作するためのアシスタントです。
            ユーザーの自然言語クエリをブラウザ操作のステップに分解してください。
            以下の操作タイプが利用可能です:
            1. navigate - URLに移動します
            2. search_google - Googleで検索を実行します
            3. click - 要素をクリックします
            4. type - フォームにテキストを入力します
            5. screenshot - スクリーンショットを撮影します
            6. wait - 指定した秒数待機します
            
            出力はJSONフォーマットで、以下の形式の操作のリストを返してください:
            [
                {
                    "action": "操作タイプ",
                    "description": "この操作の説明",
                    "params": { 操作に必要なパラメータ }
                }
            ]
            
            例えば、「Googleでpythonについて検索して、最初のリンクをクリックして、スクリーンショットを撮影」というリクエストに対しては:
            [
                {
                    "action": "search_google",
                    "description": "Googleでpythonについて検索する",
                    "params": {"query": "python"}
                },
                {
                    "action": "wait",
                    "description": "検索結果の読み込みを待つ",
                    "params": {"seconds": 2}
                },
                {
                    "action": "click",
                    "description": "最初の検索結果をクリック",
                    "params": {"selector_description": "最初の検索結果リンク"}
                },
                {
                    "action": "wait",
                    "description": "ページの読み込みを待つ",
                    "params": {"seconds": 3}
                },
                {
                    "action": "screenshot",
                    "description": "現在のページのスクリーンショットを撮影",
                    "params": {}
                }
            ]
            
            リスト内のステップ数が{max_steps}を超えないようにしてください。
            """
            
            system_prompt = system_prompt.format(max_steps=max_steps)
            
            if not client:
                logger.error("Azure OpenAIクライアントが構成されていません")
                return [{"action": "search_google", "params": {"query": query}}]
            
            # Azure OpenAI APIを呼び出して解析
            response = client.chat.completions.create(
                model=AZURE_OPENAI_DEPLOYMENT,  # Azure Deploymentのモデル名
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            # レスポンスからJSONを抽出
            result = response.choices[0].message.content
            try:
                steps = json.loads(result).get("steps", [])
                if not steps:
                    steps = json.loads(result)
                if not isinstance(steps, list):
                    steps = [steps]
                return steps[:max_steps]  # 最大ステップ数を制限
            except json.JSONDecodeError:
                # JSONが正しくない場合、パースを試みる
                match = re.search(r'\[\s*{(.+)}\s*\]', result, re.DOTALL)
                if match:
                    try:
                        steps = json.loads(f'[{{{match.group(1)}}}]')
                        return steps[:max_steps]
                    except:
                        pass
                
                logger.error(f"応答のJSONパースに失敗: {result}")
                return [{"action": "search_google", "params": {"query": query}}]
        except Exception as e:
            logger.error(f"自然言語クエリ解析エラー: {str(e)}")
            traceback.print_exc()
            # エラー時はクエリを直接Googleで検索
            return [{"action": "search_google", "params": {"query": query}}]
    
    def execute_action(self, step):
        """アクションステップを実行"""
        action = step["action"]
        params = step.get("params", {})
        
        try:
            if action == "navigate":
                url = params.get("url", "")
                return self.navigate_to(url)
            
            elif action == "search_google":
                query = params.get("query", "")
                return self.search_google(query)
            
            elif action == "click":
                # スナップショットを取得して要素を検索
                snapshot = self.get_snapshot()
                selector_desc = params.get("selector_description", "")
                
                # 適切な要素を見つける処理
                ref = self.find_element_ref(snapshot, selector_desc)
                if ref:
                    return self.click_element(selector_desc, ref)
                else:
                    return {"error": f"要素が見つかりませんでした: {selector_desc}"}
            
            elif action == "type":
                # スナップショットを取得して要素を検索
                snapshot = self.get_snapshot()
                selector_desc = params.get("selector_description", "")
                text = params.get("text", "")
                submit = params.get("submit", False)
                
                # 適切な要素を見つける処理
                ref = self.find_element_ref(snapshot, selector_desc)
                if ref:
                    return self.type_text(selector_desc, ref, text, submit)
                else:
                    return {"error": f"要素が見つかりませんでした: {selector_desc}"}
            
            elif action == "screenshot":
                return self.take_screenshot()
            
            elif action == "wait":
                seconds = params.get("seconds", 1)
                time.sleep(seconds)
                return {"waited": f"{seconds} 秒"}
            
            else:
                return {"error": f"サポートされていないアクション: {action}"}
        
        except Exception as e:
            logger.error(f"アクション実行エラー ({action}): {str(e)}")
            return {"error": str(e)}
    
    def find_element_ref(self, snapshot, description):
        """スナップショット内で説明に最も一致する要素のrefを見つける"""
        if not snapshot or not description:
            return None
            
        # 簡単な検索ロジック
        def search_nodes(nodes, description, path=""):
            matches = []
            
            for i, node in enumerate(nodes):
                current_path = f"{path}/{i}"
                
                # 名前やロールで一致するか確認
                name = node.get("name", "").lower()
                role = node.get("role", "").lower()
                
                score = 0
                desc_lower = description.lower()
                
                # 名前が完全に一致
                if name == desc_lower:
                    score += 10
                # 名前が部分一致
                elif desc_lower in name:
                    score += 5
                # 部分的に一致する単語がある
                else:
                    for word in desc_lower.split():
                        if len(word) > 2 and word in name:
                            score += 2
                
                # roleの評価（リンク、ボタン、テキスト入力など）
                if "リンク" in description and role == "link":
                    score += 3
                if "ボタン" in description and role == "button":
                    score += 3
                if ("入力" in description or "テキスト" in description) and role in ["textbox", "searchbox"]:
                    score += 3
                
                if score > 0:
                    matches.append((node.get("ref"), score, current_path))
                
                # 子ノードを再帰的に検索
                if "children" in node and isinstance(node["children"], list):
                    child_matches = search_nodes(node["children"], description, current_path)
                    matches.extend(child_matches)
            
            return matches
        
        # ノードを検索
        content = snapshot.get("content", {})
        if content:
            matches = search_nodes(content.get("children", []), description)
            
            # スコア順にソート
            matches.sort(key=lambda x: x[1], reverse=True)
            
            if matches:
                logger.info(f"要素マッチング: '{description}' => {matches[0][0]} (スコア: {matches[0][1]}, パス: {matches[0][2]})")
                return matches[0][0]
        
        return None
    
    def get_status(self):
        """現在のサーバー状態を取得"""
        return {
            "is_running": self.is_running,
            "browser_type": self.options["browser_type"],
            "headless": self.options["headless"],
            "current_url": self.current_url,
            "last_error": self.last_error
        }

# Playwrightマネージャーのインスタンスを作成
playwright_manager = PlaywrightManager()

# API エンドポイント
@app.get("/status", response_model=ServerStatusResponse)
async def get_status():
    """サーバーの現在の状態を返します"""
    return playwright_manager.get_status()

@app.post("/start")
async def start_server(options: Optional[BrowserOptions] = None):
    """サーバーを起動し、Playwright ブラウザを開始します"""
    if options:
        playwright_manager.update_options(options)
    
    if playwright_manager.start():
        return {"message": "サーバーが正常に起動しました"}
    else:
        raise HTTPException(
            status_code=500, 
            detail=f"サーバーの起動に失敗しました: {playwright_manager.last_error}"
        )

@app.post("/stop")
async def stop_server():
    """サーバーを停止し、Playwright ブラウザを閉じます"""
    if playwright_manager.stop():
        return {"message": "サーバーが正常に停止しました"}
    else:
        raise HTTPException(
            status_code=500, 
            detail=f"サーバーの停止に失敗しました: {playwright_manager.last_error}"
        )

@app.post("/restart")
async def restart_server(options: Optional[BrowserOptions] = None):
    """サーバーを再起動します"""
    if options:
        playwright_manager.update_options(options)
    
    if playwright_manager.restart():
        return {"message": "サーバーが正常に再起動しました"}
    else:
        raise HTTPException(
            status_code=500, 
            detail=f"サーバーの再起動に失敗しました: {playwright_manager.last_error}"
        )

@app.post("/query")
async def execute_query(query: QueryRequest):
    """Playwright を使用してクエリを実行します"""
    if not playwright_manager.is_running:
        raise HTTPException(
            status_code=400, 
            detail="サーバーが起動していません。先に /start を呼び出してください"
        )
    
    try:
        query_dict = query.dict(exclude_none=True)
        action = query.action
        
        if action == "navigate" and query.url:
            result = playwright_manager.navigate_to(query.url)
        elif action == "search_google" and query.value:
            result = playwright_manager.search_google(query.value)
        elif action == "take_screenshot":
            result = playwright_manager.take_screenshot()
        elif action == "get_snapshot":
            result = playwright_manager.get_snapshot()
        else:
            # 他の直接的なMCPコマンドの場合
            result = playwright_manager._execute_mcp_command(f"browser_{action}", query_dict)
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"クエリの実行に失敗しました: {str(e)}"
        )

@app.post("/nlp")
async def process_nlp_query(request: NLPQueryRequest):
    """自然言語クエリを処理します"""
    if not playwright_manager.is_running:
        raise HTTPException(
            status_code=400, 
            detail="サーバーが起動していません。先に /start を呼び出してください"
        )
    
    if not client:
        raise HTTPException(
            status_code=500, 
            detail="Azure OpenAI クライアントが設定されていません"
        )
    
    try:
        result = playwright_manager.process_nlp_query(
            request.query, 
            take_screenshot=request.take_screenshot,
            max_steps=request.max_steps
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"自然言語クエリの処理に失敗しました: {str(e)}"
        )

@app.post("/options")
async def update_options(options: BrowserOptions):
    """ブラウザオプションを更新します"""
    if playwright_manager.update_options(options):
        return {
            "message": "オプションを更新しました", 
            "current_options": playwright_manager.options,
            "restart_required": False  # 既に必要であれば再起動されています
        }
    else:
        raise HTTPException(
            status_code=500, 
            detail=f"オプションの更新に失敗しました: {playwright_manager.last_error}"
        )

@app.post("/screenshot")
async def take_screenshot():
    """現在のページのスクリーンショットを取得します"""
    if not playwright_manager.is_running:
        raise HTTPException(
            status_code=400, 
            detail="サーバーが起動していません。先に /start を呼び出してください"
        )
    
    try:
        result = playwright_manager.take_screenshot()
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"スクリーンショット取得に失敗しました: {str(e)}"
        )

@app.get("/history")
async def get_history(limit: int = 10):
    """操作履歴を取得します"""
    history = playwright_manager.history[-limit:] if limit > 0 else playwright_manager.history
    return {"history": history}

# サーバー起動時の処理
@app.on_event("startup")
async def startup_event():
    logger.info("NLP-Enhanced Playwright MCP サーバー API を起動中...")
    # 自動起動する場合はコメントを外す
    # playwright_manager.start()

# サーバー終了時の処理
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("NLP-Enhanced Playwright MCP サーバー API をシャットダウン中...")
    playwright_manager.stop()

# メイン実行部分
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("mcp_server:app", host="0.0.0.0", port=port, reload=True)