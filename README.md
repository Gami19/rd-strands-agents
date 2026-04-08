## 依存関係 各フォルダで行う
```bash 
pip install -r requirements.txt
```

## フォルダ
### standalone
> Strands Agent ドキュメントを参考にして、実行コードを作成
### strands-py
> Backend(Fast API + Strands Agents SDK)、Frontend(Vite)を利用した、マルチエージェントWebアプリケーション
#### 実行環境(開発者環境)
|実行環境|Version|
|------|-------|
|Python（サーバサイド）|3.13|
|node（フロントエンド）|22.20.0|
#### 実行手順
backend 
```bash
cd backend
pip install -r requirements.txt
python main.py
```
frontend
```bash
cd frontend
npm install
npm run dev
```
### strands-ts
> Backend(Express + TS)、Frontend(Vite)を利用した、マルチエージェントWebアプリケーション
#### 実行環境
|実行環境|Version|
|-------|-------|
|node|22.20.0|
|Express（サーバーサイド）|v4.18|
|React + Vite + Typescript（フロントエンド）|React: v19 Vite: v7.2.4|

#### 実行手順
backend 
```bash
cd backend
npm install 
npm run dev
```
frontend
```bash
cd frontend
npm install 
npm run dev
```
## 注意事項
- AWS Diagram MCPは、Windowsでは動作しない可能性があります。<br>
    > 6/30 : Windowsでの動作確認はできていません。<br>
- Web Search（アカウント名：pskill9）, Web Research（アカウント名：mzxrai） MCPは、Windowsでは動作しない可能性があります。<br>
    > 6/30 : Windowsでの動作確認はできていません。<br>
