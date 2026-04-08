# GA4 推奨イベント設計パターン集

ビジネス種別ごとの推奨イベント設計、命名規則、データレイヤー定義、GTM 実装パターンをまとめたリファレンス。

---

## 目次
- イベント命名規則
- マーケティングサイト向けイベント
- プロダクト/アプリ向けイベント
- EC サイト向けイベント
- B2B SaaS 向けイベント
- データレイヤー設計パターン
- GTM タグ・トリガー・変数設計
- UTM パラメータ命名規則
- カスタムディメンション設計
- コンバージョン設定ガイド
- デバッグと検証手順
- プライバシー・コンセント対応

---

## イベント命名規則

### 基本フォーマット: object_action

```
signup_completed      # ○ 良い: 対象_動作
button_clicked        # ○ 良い
form_submitted        # ○ 良い

Signup Completed      # × スペース・大文字禁止
signup-completed      # × ハイフン禁止（GA4 非対応）
signupCompleted       # × キャメルケース非推奨
```

### ルール

| ルール | 説明 |
|:---|:---|
| 小文字 + アンダースコア | `signup_completed`（snake_case） |
| 具体的にする | `cta_hero_clicked` > `button_clicked` |
| 文脈はプロパティに | イベント名でなくパラメータで区別 |
| GA4 推奨イベント名を優先 | `login`, `sign_up`, `purchase` 等 |
| 40文字以内 | GA4 のイベント名上限 |

---

## マーケティングサイト向けイベント

### ナビゲーション・エンゲージメント

| イベント名 | 説明 | パラメータ |
|:---|:---|:---|
| `page_view` | ページ表示（自動） | page_title, page_location, content_group |
| `scroll_depth` | スクロール到達 | depth (25, 50, 75, 100) |
| `outbound_link_clicked` | 外部リンククリック | link_url, link_text |
| `video_played` | 動画再生開始 | video_id, video_title, duration |
| `video_completed` | 動画再生完了 | video_id, video_title |

### CTA・フォーム

| イベント名 | 説明 | パラメータ |
|:---|:---|:---|
| `cta_clicked` | CTA ボタンクリック | button_text, cta_location, page |
| `form_started` | フォーム入力開始 | form_name, form_location |
| `form_submitted` | フォーム送信完了 | form_name, form_location |
| `form_error` | フォームエラー | form_name, error_type |
| `resource_downloaded` | 資料ダウンロード | resource_name, resource_type |

### コンバージョン

| イベント名 | 説明 | パラメータ |
|:---|:---|:---|
| `signup_started` | サインアップ開始 | source, page |
| `signup_completed` | サインアップ完了 | method, plan, source |
| `demo_requested` | デモ申し込み | company_size, industry |
| `contact_submitted` | 問い合わせ送信 | inquiry_type |
| `newsletter_subscribed` | メルマガ登録 | source, list_name |
| `trial_started` | トライアル開始 | plan, source |

---

## プロダクト/アプリ向けイベント

### オンボーディング

| イベント名 | 説明 | パラメータ |
|:---|:---|:---|
| `onboarding_started` | オンボーディング開始 | - |
| `onboarding_step_completed` | ステップ完了 | step_number, step_name |
| `onboarding_completed` | 全ステップ完了 | steps_completed, time_to_complete |
| `onboarding_skipped` | スキップ | step_skipped_at |
| `first_key_action_completed` | Aha モーメント到達 | action_type |

### コア利用

| イベント名 | 説明 | パラメータ |
|:---|:---|:---|
| `feature_used` | 機能利用 | feature_name, feature_category |
| `content_created` | コンテンツ作成 | content_type |
| `search_performed` | アプリ内検索 | query, results_count |
| `invite_sent` | 招待送信 | invite_type, count |
| `error_occurred` | エラー発生 | error_type, error_message, page |

---

## EC サイト向けイベント

### ブラウジング

| イベント名 | 説明 | パラメータ |
|:---|:---|:---|
| `view_item` | 商品ページ表示 | items[] (item_id, item_name, price, category) |
| `view_item_list` | 一覧ページ表示 | item_list_name, items[] |
| `select_item` | 商品選択 | items[], item_list_name |

### カート・チェックアウト

| イベント名 | 説明 | パラメータ |
|:---|:---|:---|
| `add_to_cart` | カート追加 | items[], value, currency |
| `remove_from_cart` | カート削除 | items[], value, currency |
| `view_cart` | カート表示 | items[], value, currency |
| `begin_checkout` | チェックアウト開始 | items[], value, currency |
| `add_shipping_info` | 配送情報入力 | shipping_tier, items[] |
| `add_payment_info` | 支払い情報入力 | payment_type, items[] |
| `purchase` | 購入完了 | transaction_id, value, currency, items[] |

**重要**: EC イベントでは必ず `ecommerce` オブジェクト形式を使い、送信前に `dataLayer.push({ ecommerce: null })` でクリアする。

---

## B2B SaaS 向けイベント

### サブスクリプション

| イベント名 | 説明 | パラメータ |
|:---|:---|:---|
| `pricing_viewed` | 料金ページ表示 | source |
| `plan_selected` | プラン選択 | plan_name, billing_cycle |
| `checkout_started` | 決済開始 | plan, value |
| `purchase_completed` | 購入完了 | plan, value, currency, transaction_id |
| `subscription_upgraded` | プランアップグレード | from_plan, to_plan, value |
| `subscription_cancelled` | 解約 | plan, reason, tenure |

### チーム・コラボレーション

| イベント名 | 説明 | パラメータ |
|:---|:---|:---|
| `team_member_invited` | メンバー招待 | role, invite_method |
| `team_member_joined` | メンバー参加 | role |
| `integration_connected` | 連携接続 | integration_name |

---

## データレイヤー設計パターン

### 初期化（GTM コンテナより前に配置）

```javascript
window.dataLayer = window.dataLayer || [];
dataLayer.push({
  'pageType': 'product',
  'contentGroup': 'products',
  'user': {
    'loggedIn': true,
    'userId': 'USR-12345',
    'userType': 'premium'
  }
});
```

### カスタムイベント発火

```javascript
// フォーム送信
dataLayer.push({
  'event': 'form_submitted',
  'formName': 'contact',
  'formLocation': 'footer'
});

// CTA クリック
dataLayer.push({
  'event': 'cta_clicked',
  'ctaText': 'お試しください',
  'ctaLocation': 'hero'
});
```

### EC 購入イベント

```javascript
dataLayer.push({ ecommerce: null });
dataLayer.push({
  'event': 'purchase',
  'ecommerce': {
    'transaction_id': 'T-20260221-001',
    'value': 9800,
    'currency': 'JPY',
    'items': [{
      'item_id': 'SKU-001',
      'item_name': '商品名',
      'price': 9800,
      'quantity': 1,
      'item_category': 'カテゴリ'
    }]
  }
});
```

---

## GTM タグ・トリガー・変数設計

### 命名規則

```
タグ:     GA4 - Event - Signup Completed
          FB - Pixel - Page View
トリガー: Click - CTA Button
          Custom - form_submitted
変数:     DL - formName
          JS - Current Timestamp
```

### 基本構成

| コンポーネント | 設定 |
|:---|:---|
| GA4 設定タグ | Measurement ID: G-XXXXXXXX, 全ページトリガー |
| GA4 イベントタグ | 設定タグを参照 + カスタムイベントトリガー |
| カスタムイベントトリガー | dataLayer の event 名で発火 |
| データレイヤー変数 | パラメータの値を取得 |

---

## UTM パラメータ命名規則

| パラメータ | 規則 | 良い例 | 悪い例 |
|:---|:---|:---|:---|
| `utm_source` | 小文字、プラットフォーム名 | `google`, `newsletter` | `Google`, `NL` |
| `utm_medium` | 小文字、媒体種別 | `cpc`, `email`, `social` | `CPC`, `Email` |
| `utm_campaign` | 小文字、アンダースコア区切り | `spring_sale_2026` | `Spring Sale!` |
| `utm_content` | 小文字、要素説明 | `hero_cta`, `sidebar_banner` | `cta1`, `test` |
| `utm_term` | 検索キーワード | `project_management` | - |

---

## カスタムディメンション設計

| ディメンション名 | スコープ | パラメータ名 | 用途 |
|:---|:---|:---|:---|
| ユーザー種別 | ユーザー | `user_type` | free / trial / paid で分析 |
| プラン名 | ユーザー | `plan_type` | プラン別の行動分析 |
| コンテンツ著者 | イベント | `author` | 著者別のパフォーマンス |
| コンテンツグループ | イベント | `content_group` | セクション別分析 |
| 商品カテゴリ | アイテム | `item_category` | カテゴリ別EC分析 |

---

## コンバージョン設定ガイド

### 設定手順

1. GA4 管理画面 > イベント でイベントの発火を確認
2. イベントをコンバージョンとしてマーク
3. カウント方法を選択:
   - **セッションごとに1回**: リード獲得・サインアップ
   - **毎回**: 購入・取引

### 推奨コンバージョン

| コンバージョン | イベント | カウント方法 |
|:---|:---|:---|
| サインアップ | `signup_completed` | セッションごとに1回 |
| デモ申し込み | `demo_requested` | セッションごとに1回 |
| 購入 | `purchase` / `purchase_completed` | 毎回 |
| メルマガ登録 | `newsletter_subscribed` | セッションごとに1回 |

---

## デバッグと検証手順

### GA4 DebugView

有効化方法:
- URL に `?debug_mode=true` を追加
- Chrome 拡張: GA Debugger
- gtag 設定: `'debug_mode': true`

確認場所: GA4 > 管理 > DebugView

### GTM プレビューモード

1. GTM で「プレビュー」をクリック
2. サイトURLを入力
3. デバッグパネルで確認:
   - 発火したタグ / 発火しなかったタグ
   - トリガー条件の評価結果
   - 変数の値
   - データレイヤーの内容

### チェックリスト

- [ ] 全イベントが正しいトリガーで発火する
- [ ] パラメータ値が正しく送信される
- [ ] 重複発火がない
- [ ] クロスブラウザで動作する
- [ ] モバイルで動作する
- [ ] コンバージョンが正しく記録される
- [ ] PII（個人情報）が含まれていない

---

## プライバシー・コンセント対応

### GA4 Consent Mode

```javascript
// デフォルト状態（同意前）
gtag('consent', 'default', {
  'analytics_storage': 'denied',
  'ad_storage': 'denied'
});

// 同意後に更新
function onConsentGranted() {
  gtag('consent', 'update', {
    'analytics_storage': 'granted',
    'ad_storage': 'granted'
  });
}
```

### 注意事項

- EU/UK/CA では Cookie 同意が法的に必須
- イベントパラメータに個人情報を含めない
- データ保持期間を適切に設定（デフォルト2ヶ月、最大14ヶ月）
- ユーザー削除リクエストへの対応手順を準備
