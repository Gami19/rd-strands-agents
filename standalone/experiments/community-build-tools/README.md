# [Strands Agents Community Build Tools](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/tools/tools_overview/) の検証
> Strands Agents SDKに既存で備わっているtoolsの検証を行う

# Quick Start 一括、依存関係のインストール
```bash
pip install -r requirements
```

# ツール一覧
> * ... Windowsで作動しない</br>
|ツール名|	概要|	主な用途|
|-------|-----|----------|
|a2a_client|	A2A準拠のエージェントを発見・接続し、エージェント間でメッセージ送信	エージェント間通信|
|file_read|	ファイルを読み込む	設定ファイルやコード解析、データセット読み込み|
|file_write	|ファイルに書き込む	処理結果保存、新規ファイル生成|
|editor|	高度なファイル編集	シンタックスハイライト、パターン置換、複数ファイル編集|
|shell *|	OSのシェルコマンド実行	ファイル操作、スクリプト実行|
|http_request|	HTTPリクエスト送信	API呼び出し、外部サービス通信|
|tavily_search|	高度なWeb検索	AI最適化型リアルタイム検索|
|tavily_extract|	Webページから構造化コンテンツ抽出	ノイズ除去後の情報取得|
|tavily_crawl	|Webサイトをクロール	APIドキュメント探索など|
|tavily_map|	Webサイト構造マッピング	URL一覧取得|
|python_repl *|	Pythonコード実行	データ分析、ロジック検証|
|calculator	|数学計算	数式解析、方程式解|
|code_interpreter|	サンドボックス環境で複数言語コード実行	長時間セッションやファイル操作|
|use_aws	|AWSサービス操作	S3バケット一覧取得など|
|retrieve	|Amazon Bedrock KBから情報検索	ナレッジ検索|
|nova_reels|	高品質動画生成	プロンプトから映像制作|
|agent_core_memory|	Amazon Bedrock エージェントメモリ操作	記憶の記録・取得|
|mem0_memory	|エージェント間でユーザー記憶保持	パーソナライズ応答|
|memory	|Amazon Bedrock KB文書管理	文書保存・取得|
|environment|	環境変数操作	設定管理|
|generate_image_stability|	Stability AIで画像生成	高品質画像生成|
|generate_image	|汎用AI画像生成	アプリ用画像作成|
|image_reader	|画像ファイル解析	AI画像処理|
|journal|	構造化ログ作成	ドキュメント管理|
|think	|高度な推論処理	複雑な問題分析|
|load_tool	|カスタムツール読み込み	機能拡張|
|swarm	|複数AIエージェント協調制御	集団知能による問題解決|
|current_time|	指定タイムゾーンの現在時刻取得	時刻管理|
|sleep	|実行一時停止	処理遅延制御|
|agent_graph	|エージェント間の関係図作成	複雑なエージェント構造可視化|
|cron *	|定期タスク登録・管理	自動実行スケジュール設定|
|slack	|Slackと連携	メッセージ送信・監視|
|speak	|状態メッセージ出力＋音声	実行結果通知|
|stop	|エージェント実行停止	安全終了|
|handoff_to_user	|処理をユーザーに渡す	確認や手動対応|
|use_llm	|LLM呼び出し	カスタムAI応答生成|
|workflow	|ワークフロー構築・実行	複数ステップ処理|
|mcp_client|	外部MCPサーバー接続（要注意）	リモートツール利用|
|batch	|複数ツールの並列実行	一括処理|
|browser	|Chromiumブラウザ操作	自動テスト、スクレイピング|
|diagram	|各種構造図生成	AWS構成図、UMLなど|
|rss	|RSSフィード管理	記事購読・取得|
|use_computer|	デスクトップ操作自動化	マウス・キーボード操作、スクショ|

# 検証結果
## コード実行（ /code-executor）
### python_repl
Windowsでは正常に動作しない [issues](https://github.com/strands-agents/tools/issues/15)
```bash 
    Traceback (most recent call last):
    File "C:\Users\admin\Desktop\k-ikegami\rd-strands-agents\community-build-tools\code-executior\python_repl.py", line 2, in <module>
        from strands_tools import python_repl
    File "C:\Users\admin\anaconda3\envs\py311\Lib\site-packages\strands_tools\python_repl.py", line 35, in <module>
        import fcntl
    ModuleNotFoundError: No module named 'fcntl'
```
