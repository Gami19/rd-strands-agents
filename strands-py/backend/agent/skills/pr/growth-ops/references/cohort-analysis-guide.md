# コホート分析ガイド

> リテンション分析の核心であるコホート分析の設計・実装・活用フレームワーク。
> SKILL.md の Step 3 で使用する。

---

## 1. コホート分析の基礎

### コホートとは

**コホート** = 特定の条件・時期で区切られたユーザーグループ。同じコホート内のユーザーの行動を時系列で追跡することで、個別施策の効果やプロダクトの健全性を評価する。

### コホートの種類

| 種類 | 定義 | 用途 | 例 |
|:---|:---|:---|:---|
| **Acquisition Cohort** | 同じ時期に獲得されたユーザー群 | リテンション推移の基本分析 | 2024年1月登録ユーザー |
| **Behavioral Cohort** | 同じ行動を取ったユーザー群 | 機能利用と定着の因果分析 | 初日にプロジェクト作成したユーザー |

**使い分けの原則**:
- まず Acquisition Cohort でプロダクト全体の健全性を把握する
- 次に Behavioral Cohort で「何が定着を促すか」を特定する

### リテンションカーブの読み方

```
リテンション率
100% │●
     │ ╲
 80% │  ╲
     │   ╲
 60% │    ╲
     │     ╲─────────── ← フラット化ポイント（コアユーザー層）
 40% │      ╲________
     │               ╲___________  ← 安定化
 20% │
     │
  0% └──────────────────────────────→ 経過時間
     Day0  D7  D14  D30  D60  D90
```

| カーブの特徴 | 意味 | アクション |
|:---|:---|:---|
| 急速な初期ドロップ | オンボーディングの課題 | Aha Moment の再設計、Time-to-Value 短縮 |
| フラット化なし | コアユーザー層が形成されていない | プロダクト価値の根本的見直し |
| フラット化が早い（Day 7） | 強いプロダクト適合 | スケール投資のタイミング |
| 緩やかなカーブ全体 | 良好なリテンション | 獲得チャネルの拡大に注力 |
| スマイルカーブ（復帰上昇） | 再エンゲージメントが効いている | 復帰施策の強化 |

### チャーン分析との関係

| 観点 | コホート分析 | チャーン分析 |
|:---|:---|:---|
| **視点** | グループ単位の推移 | 個別ユーザーの離脱 |
| **時間軸** | 相対時間（登録からの経過日数） | 絶対時間（カレンダー月） |
| **主な用途** | プロダクト改善の効果測定 | ヘルススコア・介入判断 |
| **併用方法** | コホートで課題区間を特定 → チャーン分析で個別原因を深掘り |

---

## 2. リテンションヒートマップ — 作成手順

### Step 1: データ準備

必要なデータカラム:

| カラム | 型 | 説明 | 例 |
|:---|:---|:---|:---|
| `user_id` | string/int | ユーザー識別子 | `u_12345` |
| `signup_date` | date | 登録日（コホート割り当て用） | `2024-01-15` |
| `action_date` | date | アクション実行日 | `2024-02-03` |
| `action_type` | string | （任意）アクションの種類 | `login`, `purchase` |

**データ品質チェック**:
- `signup_date` が `action_date` より後のレコードがないか
- `user_id` に NULL がないか
- テストユーザー・内部ユーザーが除外されているか

### Step 2: コホート分割

| 分割単位 | 適用場面 | メリット | デメリット |
|:---|:---|:---|:---|
| **日次** | DAU が 10,000+ の高頻度プロダクト | 粒度が細かく施策の効果を即座に検出 | ノイズが多い |
| **週次** | DAU が 1,000-10,000 のプロダクト | バランスが良い | 7 日周期の偏りを吸収 |
| **月次** | DAU が 1,000 未満、または長期分析 | サンプルサイズが安定 | 粒度が粗い |

### Step 3: リテンション率の計算

```
リテンション率 = (期間 N にアクティブだったコホートユーザー数) / (コホートの総ユーザー数) × 100
```

**計算上の注意**:
- 「アクティブ」の定義を明確にする（ログイン? 特定アクション?）
- 期間の定義: Day 7 = 登録から 7-13 日目（7 日間のウィンドウ）か、ちょうど 7 日目か
- 推奨: **ウィンドウ方式**（Day 7 = 7-13 日目にアクティブ）

### Step 4: ヒートマップの作成

#### ヒートマップテンプレート

```markdown
## リテンションヒートマップ

| コホート | ユーザー数 | Day 0 | Day 1 | Day 7 | Day 14 | Day 30 | Day 60 | Day 90 |
|:---|---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 2024-01 | 1,200 | 100% | 45% | 28% | 22% | 18% | 14% | 12% |
| 2024-02 | 1,350 | 100% | 48% | 32% | 25% | 20% | 16% | — |
| 2024-03 | 1,500 | 100% | 52% | 35% | 28% | 22% | — | — |
| 2024-04 | 1,800 | 100% | 55% | 38% | 30% | — | — | — |
| 2024-05 | 2,100 | 100% | 58% | 40% | — | — | — | — |
```

#### 色分け基準（SaaS の場合）

| リテンション率 | 色 | 判定 |
|:---|:---|:---|
| ≥ 50% | 濃い緑 | 優秀 |
| 35-49% | 薄い緑 | 良好 |
| 20-34% | 黄色 | 標準 |
| 10-19% | オレンジ | 要改善 |
| < 10% | 赤 | 危険 |

**注意**: 上記は SaaS の月次リテンションの目安。業界・プロダクトタイプにより大幅に異なる。自社の過去データに基づいて閾値を設定すること。

---

## 3. コホート比較分析

### 3.1 施策前後の比較（Before/After Cohort）

施策のリリース前後でコホートを比較し、効果を検証する。

```markdown
## Before/After コホート比較

### 施策: [オンボーディングフロー改善]
### リリース日: 2024-03-15

| 期間 | コホート | ユーザー数 | Day 1 | Day 7 | Day 30 |
|:---|:---|---:|:---:|:---:|:---:|
| Before | 2024-02 | 1,350 | 48% | 32% | 20% |
| Before | 2024-03前半 | 780 | 50% | 33% | 21% |
| **After** | **2024-03後半** | **820** | **58%** | **40%** | **—** |
| **After** | **2024-04** | **1,800** | **55%** | **38%** | **—** |

### 効果判定
- Day 1 リテンション: +7pp（48% → 55%）
- Day 7 リテンション: +7pp（32% → 39%）
- 統計的有意性: [p-value < 0.05 / 未達]
```

**注意点**:
- Before/After だけでは因果関係を証明できない（他の要因の影響）
- 可能であれば A/B テストとの併用を推奨
- 季節性を考慮する（前年同期との比較も有効）

### 3.2 セグメント別比較

| 比較軸 | 目的 | 得られるインサイト |
|:---|:---|:---|
| 有料 / 無料 | 課金ユーザーの定着度の差 | 有料転換のリテンション効果 |
| チャネル別 | 獲得チャネルによる定着度の差 | 高品質チャネルの特定 |
| プラン別 | プラン種別による定着度の差 | プラン設計の妥当性 |
| 地域別 | 地域による利用パターンの差 | ローカライズの優先度 |
| デバイス別 | Web / Mobile の定着度の差 | プラットフォーム投資配分 |

#### セグメント別比較テンプレート

```markdown
## セグメント別コホート比較: チャネル別

| チャネル | ユーザー数 | Day 1 | Day 7 | Day 30 | Day 90 |
|:---|---:|:---:|:---:|:---:|:---:|
| オーガニック検索 | 3,200 | 52% | 35% | 22% | 15% |
| 有料広告 | 2,800 | 38% | 22% | 12% | 7% |
| リファラル | 1,500 | 65% | 48% | 35% | 28% |
| SNS | 1,200 | 42% | 25% | 14% | 8% |

### インサイト
- リファラル経由ユーザーの Day 30 リテンションは有料広告の 3 倍
- 有料広告は獲得量は多いがリテンションが低い → CAC 回収に注意
- リファラルプログラムへの投資拡大を検討
```

### 3.3 異常値検知

| 異常パターン | 考えられる原因 | 調査方法 |
|:---|:---|:---|
| 特定コホートの急激なドロップ | バグ、サービス障害 | リリースログ・インシデント記録の照合 |
| 特定期間のスパイク | キャンペーン、メディア露出 | マーケティング施策カレンダーの照合 |
| 段階的な悪化トレンド | プロダクト品質低下、競合台頭 | NPS 推移、競合動向の確認 |
| 特定日のリテンション異常 | 曜日効果、祝日影響 | 曜日別・祝日フラグでの分解 |

---

## 4. Python/pandas テンプレート

### 4.1 コホート分析の基本コード

```python
"""
コホートリテンション分析テンプレート
前提: user_actions テーブルに user_id, signup_date, action_date が存在
"""
import pandas as pd
import numpy as np

def build_cohort_retention(df: pd.DataFrame,
                           cohort_period: str = "M") -> pd.DataFrame:
    """
    コホートリテンションテーブルを構築する。

    Args:
        df: user_id, signup_date, action_date を含む DataFrame
        cohort_period: コホートの分割単位 ("M": 月次, "W": 週次)

    Returns:
        コホート × 経過期間のリテンション率テーブル
    """
    # 1. コホート割り当て
    df["cohort"] = df["signup_date"].dt.to_period(cohort_period)
    df["action_period"] = df["action_date"].dt.to_period(cohort_period)

    # 2. 経過期間の計算
    df["period_number"] = (df["action_period"] - df["cohort"]).apply(
        lambda x: x.n
    )

    # 3. コホートサイズ
    cohort_sizes = (
        df.groupby("cohort")["user_id"]
        .nunique()
        .rename("cohort_size")
    )

    # 4. コホート × 期間のアクティブユーザー数
    cohort_data = (
        df.groupby(["cohort", "period_number"])["user_id"]
        .nunique()
        .reset_index()
        .rename(columns={"user_id": "active_users"})
    )

    # 5. リテンション率の計算
    cohort_data = cohort_data.merge(
        cohort_sizes, on="cohort"
    )
    cohort_data["retention_rate"] = (
        cohort_data["active_users"] / cohort_data["cohort_size"]
    )

    # 6. ピボットテーブル化
    retention_table = cohort_data.pivot_table(
        index="cohort",
        columns="period_number",
        values="retention_rate",
    )

    return retention_table
```

### 4.2 可視化テンプレート

#### ヒートマップ

```python
"""リテンションヒートマップの描画"""
import matplotlib.pyplot as plt
import seaborn as sns

def plot_retention_heatmap(retention_table: pd.DataFrame,
                           title: str = "Cohort Retention Heatmap") -> None:
    """
    リテンションテーブルをヒートマップで描画する。

    Args:
        retention_table: build_cohort_retention の出力
        title: グラフタイトル
    """
    fig, ax = plt.subplots(figsize=(14, 8))

    sns.heatmap(
        retention_table,
        annot=True,
        fmt=".0%",
        cmap="YlGnBu",
        vmin=0,
        vmax=1,
        linewidths=0.5,
        ax=ax,
    )

    ax.set_title(title, fontsize=16, pad=20)
    ax.set_xlabel("Period Number", fontsize=12)
    ax.set_ylabel("Cohort", fontsize=12)

    plt.tight_layout()
    plt.savefig("retention_heatmap.png", dpi=150, bbox_inches="tight")
    plt.show()
```

#### リテンションカーブ

```python
"""コホート別リテンションカーブの描画"""

def plot_retention_curves(retention_table: pd.DataFrame,
                          cohorts: list[str] | None = None,
                          title: str = "Retention Curves") -> None:
    """
    指定コホートのリテンションカーブを重ねて描画する。

    Args:
        retention_table: build_cohort_retention の出力
        cohorts: 描画するコホート名のリスト（None なら全コホート）
        title: グラフタイトル
    """
    fig, ax = plt.subplots(figsize=(12, 6))

    if cohorts is None:
        plot_data = retention_table
    else:
        plot_data = retention_table.loc[cohorts]

    for cohort in plot_data.index:
        ax.plot(
            plot_data.columns,
            plot_data.loc[cohort],
            marker="o",
            label=str(cohort),
            linewidth=2,
        )

    ax.set_title(title, fontsize=16, pad=20)
    ax.set_xlabel("Period Number", fontsize=12)
    ax.set_ylabel("Retention Rate", fontsize=12)
    ax.set_ylim(0, 1.05)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.0%}"))
    ax.legend(title="Cohort", bbox_to_anchor=(1.05, 1), loc="upper left")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("retention_curves.png", dpi=150, bbox_inches="tight")
    plt.show()
```

### 4.3 セグメント別比較コード

```python
"""セグメント別コホート比較"""

def compare_cohort_segments(df: pd.DataFrame,
                            segment_column: str,
                            cohort_period: str = "M") -> dict[str, pd.DataFrame]:
    """
    セグメント別にコホートリテンションテーブルを構築する。

    Args:
        df: user_id, signup_date, action_date, segment_column を含む DataFrame
        segment_column: セグメント分割に使うカラム名
        cohort_period: コホート分割単位

    Returns:
        セグメント名 → リテンションテーブルの辞書
    """
    results = {}
    for segment, segment_df in df.groupby(segment_column):
        results[segment] = build_cohort_retention(
            segment_df, cohort_period
        )
    return results
```

---

## 5. 分析から施策への変換

### 5.1 リテンションドロップポイント → Aha Moment 仮説

| ドロップ区間 | 仮説 | 検証方法 | 施策案 |
|:---|:---|:---|:---|
| Day 0 → Day 1 | 初期価値体験が不十分 | Behavioral Cohort で Day 1 復帰者の初回行動を分析 | オンボーディングフローの改善 |
| Day 1 → Day 7 | 習慣化のフックが弱い | 復帰トリガーの有無で比較 | プッシュ通知・メールリマインダー |
| Day 7 → Day 30 | 継続的な価値提供が不足 | 離脱者と継続者の機能利用差を分析 | 新機能の段階的開放、ゲーミフィケーション |
| Day 30 → Day 90 | マンネリ化・競合への流出 | 解約理由サーベイ | コンテンツ更新、ロイヤリティプログラム |

#### Aha Moment 特定テンプレート

```markdown
## Aha Moment 仮説検証

### 仮説
「[特定のアクション]を[期間]以内に実行したユーザーは、リテンションが有意に高い」

### 検証データ
| グループ | ユーザー数 | Day 7 RT | Day 30 RT | Day 90 RT |
|:---|---:|:---:|:---:|:---:|
| アクション実行 | [値] | [%] | [%] | [%] |
| アクション未実行 | [値] | [%] | [%] | [%] |
| **差分** | — | [pp] | [pp] | [pp] |

### 判定
- Day 30 リテンションの差が 10pp 以上 → 強い Aha Moment 候補
- 5-10pp → 中程度の影響、複合条件を検討
- 5pp 未満 → Aha Moment とは言えない
```

### 5.2 コホート差異 → A/B テスト仮説

| 観察されたコホート差異 | 仮説 | A/B テスト設計 |
|:---|:---|:---|
| 施策後コホートの Day 1 が改善 | オンボーディング変更が効いた | 旧フロー vs 新フロー |
| 特定チャネルのリテンション低下 | チャネル品質の劣化 | 広告ターゲティング A vs B |
| 有料ユーザーのリテンションが突出 | 課金がコミットメントを生む | 早期課金促進 vs 従来フロー |
| 招待機能利用者の定着が高い | ソーシャル要素が定着を促す | 招待 CTA 表示 vs 非表示 |

### 5.3 セグメント差異 → ペルソナ再定義

```markdown
## コホート分析からのペルソナ再定義

### 発見
チャネル別コホート分析の結果、リファラル経由ユーザーの Day 30 リテンションが
有料広告経由の 3 倍であることが判明。

### リファラル経由ユーザーの特徴（データから抽出）
- 初日に [特定機能] を利用する率が 80%（平均 45%）
- 登録から有料転換までの日数が平均 5 日（全体平均 21 日）
- チーム招待率が 60%（全体平均 15%）

### ペルソナへの反映
→ ICP の「行動特性」セクションに上記データを追加
→ marketing-context のペルソナ定義を更新（persona-templates.md 参照）
→ リファラルプログラムの設計を growth-ops の experiment-frameworks.md で設計
```

---

## 6. 品質チェックリスト — 5 項目

コホート分析の結果を報告・意思決定に使用する前に、以下の 5 項目を必ず確認する。

### チェックリスト

```markdown
## コホート分析 品質チェックリスト

### 1. サンプルサイズの十分性
- [ ] 各コホートのユーザー数が 100 名以上（統計的安定性）
- [ ] 最新コホートは経過期間が短いため、比較対象から除外している
- [ ] 異常に小さいコホートにフラグを立てている

### 2. 季節性の考慮
- [ ] 年末年始・GW・夏季休暇など、利用パターンが変わる期間を識別している
- [ ] 前年同期比での比較を併用している
- [ ] 季節性が強い場合、月次ではなく四半期コホートも検討している

### 3. 外部要因の除外
- [ ] 大規模キャンペーン・PR がコホートに与えた影響を注記している
- [ ] プロダクトの重大バグ・障害がリテンションに影響した期間を識別している
- [ ] 競合の大型リリース・値下げ時期を把握している

### 4. 定義の一貫性
- [ ] 「アクティブ」の定義が全期間で統一されている
- [ ] コホートの分割基準（月初/登録日）が一貫している
- [ ] テストユーザー・内部ユーザーの除外が一貫している

### 5. 解釈の妥当性
- [ ] 相関関係と因果関係を区別している
- [ ] 複数の仮説を検討し、最も説明力の高いものを採用している
- [ ] 分析結果から導いた施策案が具体的かつ検証可能である
```

### よくある分析ミスと対策

| ミス | 問題 | 対策 |
|:---|:---|:---|
| 小サンプルで結論を出す | ランダム変動を施策効果と誤認 | 最低 100 名/コホート、信頼区間を表示 |
| 生存者バイアス | 残ったユーザーだけ見て全体を判断 | 離脱ユーザーの行動ログも分析する |
| Simpson のパラドックス | 全体トレンドとセグメント別が逆 | 必ずセグメント別にも確認する |
| 登録直後の除外忘れ | Day 0 が常に 100% で他が低く見える | Day 0 を基準に正規化していることを確認 |
| 定義の途中変更 | 前後のコホートが比較不可能に | 定義変更時は新旧両方で計算する |

---

## 関連スキル・リファレンス

| リファレンス | 用途 |
|:---|:---|
| `funnel-analysis-templates.md` | AARRR ファネルのコホートテーブルテンプレート |
| `retention-strategies.md` | リテンション施策の詳細（オンボーディング、チャーン防止） |
| `experiment-frameworks.md` | コホート差異から導いた A/B テスト仮説の設計 |
| `north-star-metric.md` | リテンション系 Input Metrics との接続 |
| `marketing-context/persona-templates.md` | セグメント差異からのペルソナ再定義 |
| `cro-playbook.md` | コンバージョン率改善との連携 |
