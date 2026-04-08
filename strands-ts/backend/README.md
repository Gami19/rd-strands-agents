# Backend API

Express + TypeScript + Strands Agents SDK バックエンドAPI

## セットアップ

### 1. 依存関係のインストール

```bash
npm install
```

### 2. 環境変数の設定

`.env`ファイルを作成し、以下の環境変数を設定してください：

```env
PORT=3000
NODE_ENV=development

# AWS Credentials for Bedrock
AWS_ACCESS_KEY=your_access_key_id
AWS_SECRET_KEY=your_secret_access_key
AWS_REGION=us-east-1
```

または、`aws configure`コマンドを使用してAWS認証情報を設定することもできます。

### 3. Amazon Bedrockの設定

Strands Agents SDKはデフォルトでAmazon BedrockのClaude 4モデルを使用します。

- AWSコンソールでAmazon Bedrockにアクセス
- 使用するモデル（Claude 4 Sonnetなど）へのアクセスを有効化
- 必要なIAM権限を設定

## 開発

```bash
npm run dev
```

サーバーは `http://localhost:3000` で起動します。

## ビルド

```bash
npm run build
```

## 本番実行

```bash
npm start
```

## APIエンドポイント

### GET `/api/health`
ヘルスチェックエンドポイント

### POST `/api/agent/invoke`
エージェントを通常実行

リクエストボディ:
```json
{
  "message": "Tell me how many letter R's are in the word 'strawberry' 🍓"
}
```

レスポンス:
```json
{
  "response": "エージェントのレスポンス",
  "messages": [...]
}
```

### POST `/api/agent/stream`
エージェントをストリーミング実行（Server-Sent Events）

リクエストボディ:
```json
{
  "message": "Tell me how many letter R's are in the word 'strawberry' 🍓"
}
```

レスポンス: Server-Sent Events形式でストリーミング

