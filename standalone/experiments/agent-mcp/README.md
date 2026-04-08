## Serena MCP
### 実施方法
1. プロジェクトを有効化する

```json
POST http:/localhost:8001/serena/activate-project
Content-Type: application/json

{
    "project_path": "your local absolute path"
}

```
2. プロジェクトをオンボーディングする（指定したフォルダに.serenaフォルダが生成）
```json
POST http:/localhost:8001/serena/query
Content-Type: application/json

{
    "query": "このプロジェクトのオンボーディングを実行してください"
}

```
3. コードの修正、テストなどをqueryで指定