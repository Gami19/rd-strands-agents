# テーマカタログ

> サイトのビジュアルアイデンティティを決定づける10のデザインテーマ。各テーマに配色・フォント・モーション・背景の方向性と CSS 変数サンプルを付記。テーマを1つ選び、全デザイン判断の基盤とする。

---

## テーマ一覧

| # | テーマ名 | キーワード | 適合業種例 |
|:---|:---|:---|:---|
| 1 | Nord | 静謐・冷涼・フロスト | 開発ツール、CLI、テック系ドキュメント |
| 2 | Solarpunk | 楽観・自然×技術・有機 | 環境、再生エネルギー、サステナブルブランド |
| 3 | Art Deco | 華麗・対称・ゴールド | 高級ホテル、ジュエリー、ウェディング |
| 4 | Brutalist | 生々しい・ロウ・構造的 | ポートフォリオ、アート、実験的メディア |
| 5 | Wabi-sabi（侘び寂び） | 不完全の美・余白・素材感 | 和食、工芸、旅館、文化施設 |
| 6 | Y2K | ノスタルジック・ポップ・光沢 | ファッション、コスメ、若年層向け EC |
| 7 | Cyberpunk | ネオン・暗黒・電脳 | ゲーム、セキュリティ、先端テック |
| 8 | Natural / Organic | 大地・柔和・手触り | オーガニック食品、ウェルネス、カフェ |
| 9 | Corporate Modern | 信頼・洗練・効率 | 金融、コンサル、SaaS、B2B |
| 10 | Dark Luxury | 重厚・沈黙・格調 | 高級車、時計、プレミアムブランド |

---

## 1. Nord

静謐なブルーグレーのパレットに、フロストブルーのアクセントを添えた落ち着いた美学。
[Nord Theme](https://www.nordtheme.com/) に代表される、開発者コミュニティで支持される配色体系。

### 方向性

| 軸 | 方向性 |
|:---|:---|
| **配色** | ポーラーナイト（ダークグレー群）+ スノーストーム（ライトグレー群）+ フロストブルー |
| **フォント** | JetBrains Mono（コード・見出し）+ IBM Plex Sans（本文） |
| **モーション** | 控えめ。フェード中心、200-300ms。氷の結晶のような静かな登場 |
| **背景** | ダークブルーグレーのべた塗りにソフトグロウ。ノイズテクスチャをほのかに重ねる |
| **適合業種** | 開発ツール、CLI ダッシュボード、ドキュメントサイト、テック系ブログ |

### CSS 変数サンプル

```css
:root {
  /* Nord Polar Night */
  --color-bg: #2e3440;
  --color-surface: #3b4252;
  --color-surface-raised: #434c5e;
  --color-text-muted: #4c566a;
  /* Nord Snow Storm */
  --color-text: #eceff4;
  --color-text-inverse: #2e3440;
  --color-text-secondary: #d8dee9;
  /* Nord Frost */
  --color-primary: #88c0d0;
  --color-primary-light: #8fbcbb;
  --color-primary-dark: #5e81ac;
  --color-accent: #81a1c1;
  /* Nord Aurora (semantic) */
  --color-success: #a3be8c;
  --color-warning: #ebcb8b;
  --color-error: #bf616a;
}
```

---

## 2. Solarpunk

自然と技術の共存を描く楽観的な美学。グリーン・ゴールド・アースカラーが主軸。
有機的な曲線と幾何学的なテクスチャを重ねて、未来的かつ温かい世界観を作る。

### 方向性

| 軸 | 方向性 |
|:---|:---|
| **配色** | フォレストグリーン + ゴールデンアンバー + アイボリー + アースブラウン |
| **フォント** | Fraunces（見出し：レトロフューチャー感）+ Source Sans 3（本文：可読性） |
| **モーション** | 有機的。パララックス、ゆったりとした fadeIn（0.8-1.2s）。植物が育つようなイージング |
| **背景** | グリーン系グラデーションにオーガニックな SVG パターン（葉脈、幾何学的ハニカム）を重ねる |
| **適合業種** | 環境、再生エネルギー、サステナブルファッション、コミュニティプラットフォーム |

### CSS 変数サンプル

```css
:root {
  --color-bg: #faf7f0;
  --color-surface: #f0ebe0;
  --color-surface-raised: #e8e0d0;
  --color-text: #2d3b2d;
  --color-text-inverse: #faf7f0;
  --color-text-muted: #5a6b5a;
  --color-primary: #2d6a4f;
  --color-primary-light: #52b788;
  --color-primary-dark: #1b4332;
  --color-accent: #d4a843;
  --color-success: #52b788;
  --color-warning: #e0a040;
  --color-error: #c0392b;
}
```

---

## 3. Art Deco

1920年代の装飾芸術をデジタルに昇華。ゴールド・ブラック・クリームの対称的な美。
幾何学的な罫線、扇形のモチーフ、優美なセリフ体がキーエレメント。

### 方向性

| 軸 | 方向性 |
|:---|:---|
| **配色** | ジェットブラック + ゴールド + オフホワイト（クリーム）。金属的な光沢感 |
| **フォント** | Playfair Display（見出し：セリフの華やかさ）+ Outfit（本文：モダンな可読性） |
| **モーション** | 対称的。スライドインは左右対称に、要素はセンターから展開。アニメーション 300-500ms |
| **背景** | ジオメトリックパターン（扇、ジグザグ、直線の反復）+ ゴールドのグラデーション |
| **適合業種** | 高級ホテル、ジュエリー、ウェディング、ワイン、高級レストラン |

### CSS 変数サンプル

```css
:root {
  --color-bg: #0a0a0a;
  --color-surface: #1a1a1a;
  --color-surface-raised: #2a2a2a;
  --color-text: #f5f0e8;
  --color-text-inverse: #0a0a0a;
  --color-text-muted: #a89f8e;
  --color-primary: #c9a84c;
  --color-primary-light: #e0c97a;
  --color-primary-dark: #9a7b2e;
  --color-accent: #d4af37;
  --color-success: #4a8c5c;
  --color-warning: #c9a84c;
  --color-error: #a63d40;
}
```

---

## 4. Brutalist

装飾を排し、構造を剥き出しにする。モノクロ基調に原色アクセント1色。
「生コンクリート」の名の通り、素材感と情報の率直さを優先する。

### 方向性

| 軸 | 方向性 |
|:---|:---|
| **配色** | モノクロ（白 + 黒）+ 原色アクセント1色（例: 赤、黄、ブルー） |
| **フォント** | Roboto Mono / Space Mono（見出し：等幅のロウ感）+ Space Grotesk（本文） |
| **モーション** | 最小限。カクカクとした瞬間的なトランジション（100-150ms）。イージングなし（linear） |
| **背景** | べた塗り白 or 黒。テクスチャなし。ボーダーとグリッド線で構造を見せる |
| **適合業種** | ポートフォリオ、アート、実験的メディア、独立系出版 |

### CSS 変数サンプル

```css
:root {
  --color-bg: #ffffff;
  --color-surface: #f0f0f0;
  --color-surface-raised: #ffffff;
  --color-text: #000000;
  --color-text-inverse: #ffffff;
  --color-text-muted: #666666;
  --color-primary: #ff0000;         /* accent: a single raw primary */
  --color-primary-light: #ff4444;
  --color-primary-dark: #cc0000;
  --color-accent: #ff0000;
  --color-success: #00cc00;
  --color-warning: #ffcc00;
  --color-error: #ff0000;
}
```

---

## 5. Wabi-sabi（侘び寂び）

不完全さ・経年変化・余白の美を大切にする日本的美学。
素材の質感と「間」の設計が鍵。装飾は最小限に、自然素材のテクスチャで語る。

### 方向性

| 軸 | 方向性 |
|:---|:---|
| **配色** | 生成り + 墨色 + 枯葉色。低彩度・中明度。自然の色をそのまま |
| **フォント** | Shippori Mincho（見出し：端正な明朝体）+ Noto Sans JP（本文：安定した可読性） |
| **モーション** | 静か。フェードのみ、800ms 以上のゆったりした登場。急な動きは使わない |
| **背景** | 和紙テクスチャ、水墨の滲み風グラデーション。SVG ノイズで質感を足す |
| **適合業種** | 和食、工芸、旅館、茶道・華道、日本文化施設、ギャラリー |

### CSS 変数サンプル

```css
:root {
  --color-bg: #f5f0e8;
  --color-surface: #ede6d8;
  --color-surface-raised: #faf5ed;
  --color-text: #3a3632;
  --color-text-inverse: #f5f0e8;
  --color-text-muted: #7a7268;
  --color-primary: #8b6e4e;
  --color-primary-light: #a88c6a;
  --color-primary-dark: #5c4a35;
  --color-accent: #b85c38;
  --color-success: #6b8f5e;
  --color-warning: #c4a35a;
  --color-error: #a04040;
}
```

---

## 6. Y2K

2000年前後のデジタルノスタルジアを再解釈。バブリーなグラデーション、光沢質感、半透明。
ポップで遊び心に満ちた、若年層に刺さるビジュアル。

### 方向性

| 軸 | 方向性 |
|:---|:---|
| **配色** | パステルピンク + ラベンダー + ミントグリーン + シルバー。光沢・虹色 |
| **フォント** | Syne（見出し：未来レトロ感）+ DM Sans（本文：モダンな可読性） |
| **モーション** | 弾むような動き。バウンスイージング、スケールイン、回転要素。200-400ms |
| **背景** | 虹色グラデーション、星や泡のパーティクル、グラスモーフィズム（半透明 + ブラー） |
| **適合業種** | ファッション、コスメ、ポップカルチャー、若年層向け EC、SNS 系サービス |

### CSS 変数サンプル

```css
:root {
  --color-bg: #fdf0f5;
  --color-surface: #ffffff;
  --color-surface-raised: #fff5fa;
  --color-text: #2d1b4e;
  --color-text-inverse: #ffffff;
  --color-text-muted: #8b6e9e;
  --color-primary: #e879a8;
  --color-primary-light: #f0a0c0;
  --color-primary-dark: #c05888;
  --color-accent: #a78bfa;
  --color-success: #68d69e;
  --color-warning: #fbbf24;
  --color-error: #f87171;
}
```

---

## 7. Cyberpunk

暗闇にネオンが走る電脳都市。ダークベースにシアン・マゼンタ・電気グリーンが刺す。
ハイコントラストで情報密度が高く、テクニカルな印象を与える。

### 方向性

| 軸 | 方向性 |
|:---|:---|
| **配色** | ほぼブラック + シアン or マゼンタのネオンアクセント。グロウ効果 |
| **フォント** | Orbitron / Rajdhani（見出し：SF 的）+ Share Tech Mono / IBM Plex Mono（本文：端末感） |
| **モーション** | グリッチ、スキャンライン、タイプライター効果。素早い（100-200ms）+ グロウ |
| **背景** | グリッド線（ワイヤーフレーム）、スキャンライン、ネオングロウのラディアルグラデーション |
| **適合業種** | ゲーム、セキュリティ、先端テック、暗号資産、ハッカソン |

### CSS 変数サンプル

```css
:root {
  --color-bg: #0a0a0f;
  --color-surface: #12121a;
  --color-surface-raised: #1a1a28;
  --color-text: #e0e0e8;
  --color-text-inverse: #0a0a0f;
  --color-text-muted: #6a6a80;
  --color-primary: #00f0ff;
  --color-primary-light: #40f8ff;
  --color-primary-dark: #00a0b0;
  --color-accent: #ff00aa;
  --color-success: #00ff88;
  --color-warning: #ffaa00;
  --color-error: #ff2244;
}
```

---

## 8. Natural / Organic

大地・植物・手触りを感じる穏やかな美学。アースカラーとソフトな曲線が基調。
「人の手が触れた」温もりを大切にし、工業的なシャープさを避ける。

### 方向性

| 軸 | 方向性 |
|:---|:---|
| **配色** | アイボリー + セージグリーン + テラコッタ + ウォームグレー |
| **フォント** | Vollkorn / Literata（見出し：温かみのあるセリフ）+ Nunito（本文：丸みの柔和さ） |
| **モーション** | ゆったり。フェードイン 600-800ms。パララックスはゆっくり（0.3-0.5 速度比） |
| **背景** | リネンテクスチャ、水彩風グラデーション、葉や枝のシルエット SVG |
| **適合業種** | オーガニック食品、ウェルネス、カフェ、フラワーショップ、農園 |

### CSS 変数サンプル

```css
:root {
  --color-bg: #faf6f0;
  --color-surface: #f0ebe2;
  --color-surface-raised: #faf6f0;
  --color-text: #3d3530;
  --color-text-inverse: #faf6f0;
  --color-text-muted: #7a706a;
  --color-primary: #6b8f6b;
  --color-primary-light: #8bb08b;
  --color-primary-dark: #4a6b4a;
  --color-accent: #c87941;
  --color-success: #6b8f6b;
  --color-warning: #d4a843;
  --color-error: #b85c5c;
}
```

---

## 9. Corporate Modern

信頼と効率を両立する現代的なビジネス美学。クリーンでプロフェッショナルだが無個性にはしない。
ネイビーまたはダークグレーの重心に、精緻なアクセントカラーを1色加える。

### 方向性

| 軸 | 方向性 |
|:---|:---|
| **配色** | ネイビー or ダークグレー + クリーンホワイト + アクセント1色（ティール、コーラル等） |
| **フォント** | Plus Jakarta Sans / IBM Plex Sans（見出し：信頼感 + 現代性）+ Noto Sans / Source Sans 3（本文） |
| **モーション** | 控えめだが洗練。フェードアップ 400-600ms。ホバー時の微細なリフト |
| **背景** | ライトグレーのセクション交互配置。ダークセクションにはソフトグロウ |
| **適合業種** | 金融、コンサル、SaaS、B2B プラットフォーム、法務 |

### CSS 変数サンプル

```css
:root {
  --color-bg: #ffffff;
  --color-surface: #f8f9fa;
  --color-surface-raised: #ffffff;
  --color-text: #1a1d23;
  --color-text-inverse: #ffffff;
  --color-text-muted: #6b7280;
  --color-primary: #1e3a5f;
  --color-primary-light: #2d5a8e;
  --color-primary-dark: #0f2440;
  --color-accent: #0d9488;
  --color-success: #059669;
  --color-warning: #d97706;
  --color-error: #dc2626;
}
```

---

## 10. Dark Luxury

漆黒の中に光る一条のゴールド。沈黙の中の格調。最小限の要素で最大限の高級感を演出。
情報量は絞り、余白とコントラストで「語らない贅沢」を表現する。

### 方向性

| 軸 | 方向性 |
|:---|:---|
| **配色** | ディープブラック + ゴールド or シャンパン + ダークチャコール。彩度は極めて低く |
| **フォント** | Cormorant Garamond / Bodoni Moda（見出し：品格あるセリフ）+ Jost（本文：洗練されたサンセリフ） |
| **モーション** | ゆったりと優雅。フェードイン 800ms+。ホバーはゴールドのグロウ。急がない |
| **背景** | ノイズテクスチャ付きのダーク単色。ゴールドのラインアクセント。光の帯のグラデーション |
| **適合業種** | 高級車、時計、プレミアムブランド、高級不動産、プライベートバンキング |

### CSS 変数サンプル

```css
:root {
  --color-bg: #0c0c0c;
  --color-surface: #161616;
  --color-surface-raised: #222222;
  --color-text: #e8e4dc;
  --color-text-inverse: #0c0c0c;
  --color-text-muted: #8a8278;
  --color-primary: #c9a84c;
  --color-primary-light: #ddc070;
  --color-primary-dark: #a08838;
  --color-accent: #c9a84c;
  --color-success: #4a8c5c;
  --color-warning: #c9a84c;
  --color-error: #a04040;
}
```

---

## IDE テーマからの配色変換ガイド

IDE テーマは開発者に馴染みが深く、洗練された配色体系を持つ。
既存の IDE テーマからウェブサイトの CSS 変数に変換する手順。

### 変換手順

1. **テーマの配色を取得する**: IDE テーマの公式リポジトリから背景色、テキスト色、アクセント色群を抽出
2. **役割にマッピングする**: テーマの色をウェブサイトの役割に対応づける

| IDE テーマの色 | ウェブサイトでの役割 |
|:---|:---|
| エディタ背景色 | `--color-bg` |
| サイドバー背景色 | `--color-surface` |
| ハイライト/選択色 | `--color-surface-raised` |
| デフォルトテキスト色 | `--color-text` |
| コメント色 | `--color-text-muted` |
| キーワード色 | `--color-primary` |
| 文字列色 | `--color-accent` |
| エラー表示色 | `--color-error` |
| 成功/追加表示色 | `--color-success` |
| 警告表示色 | `--color-warning` |

3. **コントラスト比を検証する**: WCAG AA 基準（4.5:1 以上）を満たすように調整
4. **CSS 変数テンプレートに流し込む**: `:root` に定義して一括管理

### 人気 IDE テーマ → ウェブサイト変換例

| IDE テーマ | タイプ | ウェブサイト適用時の特徴 |
|:---|:---|:---|
| **Dracula** | ダーク | パープル基調 + グリーン/ピンクアクセント。ゲーム・テック系に最適 |
| **Solarized Light** | ライト | ベージュ背景 + ブルーアクセント。読み物系・ドキュメントに最適 |
| **Solarized Dark** | ダーク | ティールグレー背景。落ち着いたテック感 |
| **One Dark** | ダーク | チャコール + マルチカラーアクセント。SaaS ダッシュボード向き |
| **GitHub Light** | ライト | クリーンホワイト + ブルーリンク。ドキュメント・OSS サイト |
| **Catppuccin Mocha** | ダーク | パステルアクセントのダーク。柔らかく温かいテック感 |
| **Tokyo Night** | ダーク | インディゴ背景 + ネオンアクセント。日本テック企業に好相性 |
| **Gruvbox** | 両方 | レトロなアースカラー。クラフト・インディー感 |

---

## テーマ選定フローチャート

```
Q1: サイトのトーンは？
├── フォーマル・信頼 → Q2へ
├── クリエイティブ・遊び心 → Q3へ
└── 文化的・伝統的 → Q4へ

Q2: 明るさの好みは？
├── ライト → 【9. Corporate Modern】
└── ダーク → 【10. Dark Luxury】

Q3: ターゲット層は？
├── Z世代・若年層 → 【6. Y2K】
├── デザイナー・アーティスト → 【4. Brutalist】
└── テック・ゲーマー → 【7. Cyberpunk】

Q4: どの文化的文脈か？
├── 日本的 → 【5. Wabi-sabi】
├── 西洋クラシック → 【3. Art Deco】
└── 未来志向 → 【2. Solarpunk】

Q5: テック系のサイトで迷ったら？
├── 開発者向けツール → 【1. Nord】
├── 自然との共存テーマ → 【2. Solarpunk】or【8. Natural / Organic】
└── B2B・エンタープライズ → 【9. Corporate Modern】
```

---

## テーマのカスタマイズ原則

テーマはそのまま使うのではなく、コンセプトに合わせて調整する。

### 調整できる軸

| 軸 | 調整方法 |
|:---|:---|
| **明度** | ダークテーマ ↔ ライトテーマの反転。CSS 変数を差し替えるだけ |
| **アクセント色** | テーマの骨格は維持しつつ、ブランドカラーをアクセントに注入 |
| **フォント** | テーマの雰囲気に合う別のフォントファミリーに差し替え |
| **モーション強度** | 控えめ ↔ ダイナミック。`animation-duration` と `easing` で調整 |

### テーマ混合の禁止事項

- 2つ以上のテーマを混ぜない（一貫性が崩壊する）
- テーマの配色とフォントの方向性を矛盾させない（例: Brutalist の配色 + Art Deco のフォント）
- テーマを選んだら strategy.md に明記し、以降のデザイン判断で参照する
