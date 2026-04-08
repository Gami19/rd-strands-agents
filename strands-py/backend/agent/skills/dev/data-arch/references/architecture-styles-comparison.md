# ソフトウェアアーキテクチャスタイル比較（data-arch 参照用）

> Source: Fundamentals of Software Architecture, 2nd Edition (Richards & Ford, O'Reilly 2025)
> Progressive Disclosure: Step 2（アーキテクチャ候補の絞り込み）で参照するデータ視点の補足資料

---

## 9 スタイル概要比較

ソフトウェアアーキテクチャスタイルをデータアーキテクチャの観点で評価した比較表。

| スタイル | 種別 | データトポロジー | データ統合性 | スケーラビリティ | data-arch 関連度 |
|:---|:---|:---|:---|:---|:---|
| **Layered** | モノリス | 単一共有 DB | ACID（強整合） | 低（垂直のみ） | 低 |
| **Modular Monolith** | モノリス | 共有 DB + スキーマ分割 | ACID（モジュール内） | 低〜中 | 中 |
| **Pipeline** | モノリス | フロー型（ファイル/ストリーム） | 結果整合（段階処理） | 低（単体） | **高** |
| **Microkernel** | モノリス | コア DB + プラグイン DB | ACID（コア内） | 低 | 低 |
| **Service-Based** | 分散 | 共有 DB or サービス別 DB | ACID〜BASE（選択可） | 中 | **高** |
| **Event-Driven** | 分散 | プロセッサ別 DB / イベントストア | BASE（結果整合） | 高 | **最高** |
| **Space-Based** | 分散 | インメモリグリッド + 非同期永続化 | BASE（結果整合） | 非常に高 | 中 |
| **Orchestration SOA** | 分散 | ESB 経由の共有 DB | ACID（ESB 管理） | 中 | 低（非推奨） |
| **Microservices** | 分散 | サービス別 DB（厳密分離） | BASE（Saga 補償） | 非常に高 | **最高** |

### データ統合性モデルの補足

| モデル | 特徴 | 適合するデータアーキテクチャ |
|:---|:---|:---|
| **ACID** | 即座の一貫性。ロールバック可能 | RDW, MDW（DWH 層） |
| **BASE** | 結果整合。高可用性・高スループット優先 | Data Lake, Data Lakehouse, Data Mesh |
| **Saga（補償トランザクション）** | 分散環境での擬似 ACID。各ステップに補償アクションを定義 | Microservices + Data Mesh |

---

## data-arch で特に重要なスタイル

### Event-Driven Architecture

データパイプラインと最も親和性が高いスタイル。

**データパイプラインとの関連**:
- Broker トポロジー: Kafka / Event Hubs を中核としたストリーミング取り込み
- Mediator トポロジー: ワークフローエンジン（Airflow, DLT）による ETL/ELT オーケストレーション
- Data Lake の Raw 層への継続的なイベント投入に最適

**CQRS / Event Sourcing パターン**:
- 書き込み（Command）と読み取り（Query）を分離 → DWH の読み取り最適化と整合
- Event Sourcing: イベントログが Single Source of Truth → Data Lake の Raw 層と概念が一致
- data-arch の Lambda / Kappa アーキテクチャの基盤となるパターン

**data-arch Step 5 との接続**:
| data-arch パターン | Event-Driven での実装 |
|:---|:---|
| Lambda Architecture | Broker(Speed 層) + バッチ処理(Batch 層)の並列 |
| Kappa Architecture | ストリーム処理のみで統一（Broker トポロジー） |
| Data Lake 層構造 | Raw = イベントストア、Conformed = 変換済みイベント |

### Service-Based Architecture

データドメイン分割の第一歩として現実的な選択肢。

**データドメイン分割との整合**:
- 4〜12 の粗粒度サービスが、data-arch の「ドメイン別データマート」と自然に対応
- 共有 DB を維持しつつドメイン境界を明確化 → Data Mesh 導入前の過渡期に最適
- MDW のドメイン分割をアプリケーション層でも反映する際の自然な選択肢

**Team Topologies との関連**:
- Stream-aligned team（ドメインチーム）がサービスとデータの両方を所有
- data-arch Step 7 のチーム構成設計と直結
- Data Mesh の「Domain Ownership」原則への段階的移行パスを提供

**data-arch Step 2 での位置づけ**:
- Data Mesh ほどの組織変革は不要だが、ドメイン単位のデータオーナーシップを確立したい場合に推奨
- ACID トランザクションを維持しながら段階的にドメインを分離可能

### Microservices Architecture

Data Mesh と最も整合するスタイル。

**Database per Service パターン**:
- 各サービスが自身のデータストアを所有（Polyglot Persistence）
- サービス間のデータアクセスは API 経由のみ → データの結合には非同期イベントを活用
- data-arch の観点: 分散したデータをどう統合・分析するかが最大の課題

**Data Mesh との整合**:
| Data Mesh 原則 | Microservices での対応 |
|:---|:---|
| Domain Ownership | Bounded Context = ドメインデータの所有 |
| Data as a Product | サービスの API = データプロダクトインターフェース |
| Self-Serve Platform | Service Mesh / Sidecar = インフラ抽象化 |
| Federated Governance | API 標準 + Schema Registry = 連合的ガバナンス |

**データ統合の課題と対策**:
- 分散データの分析: Change Data Capture (CDC) → 中央 Data Lake / Lakehouse への集約
- 結合クエリ: CQRS の Query 側で非正規化ビューを構築
- data-arch Step 8（Data Mesh 適性評価）と組み合わせて判断

---

## Pipeline Architecture とデータ処理

ETL/ELT パイプラインの基盤概念として重要。

**data-arch Step 5 との直接対応**:
- Producer フィルタ = データソース抽出（Extract）
- Transformer フィルタ = データ変換（Transform）
- Tester フィルタ = データ品質チェック（data-validation スキル連携）
- Consumer フィルタ = ターゲットへのロード（Load）

**Medallion Architecture との対応**:
```
Raw(Bronze) → Conformed(Silver) → Cleansed(Gold) → Presentation
  Producer      Transformer         Tester           Consumer
```

---

## スタイル選定の判断軸

data-arch Step 2 でソフトウェアアーキテクチャスタイルを考慮する際の判断マトリクス。

### データアーキテクチャ × ソフトウェアアーキテクチャ 適合マトリクス

| データアーキテクチャ | 推奨スタイル | 理由 |
|:---|:---|:---|
| **RDW** | Layered / Modular Monolith | 単一 DB、ACID、小〜中規模で十分 |
| **Data Lake** | Pipeline + Event-Driven | フロー型処理、ストリーミング取り込み |
| **MDW** | Service-Based + Event-Driven | ドメイン分割 + バッチ/RT の二系統 |
| **Data Fabric** | Event-Driven + Microservices | メタデータ駆動、多システム仮想統合 |
| **Data Mesh** | Microservices | Bounded Context = ドメインデータ所有 |
| **Data Lakehouse** | Event-Driven + Pipeline | Delta Lake のストリーミング + バッチ統合 |

### 判断フロー（data-arch 視点）

```
データトランザクション要件は？
  ├─ 強整合性（ACID）が必須
  │    ├─ 単一チーム → Layered / Modular Monolith + RDW
  │    └─ 複数チーム → Service-Based + MDW（共有 DB）
  │
  └─ 結果整合性（BASE）を許容
       ├─ ストリーミング中心 → Event-Driven + Data Lakehouse
       ├─ ドメイン分散 → Microservices + Data Mesh
       └─ バッチ中心 → Pipeline + Data Lake
```

### 段階的移行パス

```
Phase 1: Layered + RDW
    ↓ データ量・種別の増加
Phase 2: Modular Monolith + MDW
    ↓ リアルタイム要件の追加
Phase 3: Service-Based + Event-Driven + Data Lakehouse
    ↓ 組織のドメイン分散
Phase 4: Microservices + Data Mesh (Hub-and-Spoke)
```

> **注意**: この段階的移行は理想的なパスであり、すべての組織が Phase 4 を目指す必要はない。
> data-arch Step 1 の 6 Vs 分析と Step 8 の Data Mesh 適性評価に基づいて判断すること。
