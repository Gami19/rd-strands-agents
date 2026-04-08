# テストダブル使い分けガイド

> テストダブルの5種類を正しく分類し、モック対象を「アプリケーション境界を超える管理外依存」に限定する判断基準を提供する。

---

## 1. テストダブルの分類体系

テストダブルとは、プロダクションコードには含まれず、テストでのみ使われる偽りの依存の総称である。映画のスタントマン（stunt double）が語源。

### 5種類と2大分類

すべてのテストダブルは **モック系** と **スタブ系** のどちらかに分類される。

| 分類 | 種類 | 役割 | コミュニケーション方向 |
|:---|:---|:---|:---|
| **モック系** | モック（Mock） | 外部に向かうコミュニケーション（出力）を模倣・**検証** | SUT → 依存 |
| | スパイ（Spy） | モックと同じ役割だが、フレームワークを使わず手書きで実装 | SUT → 依存 |
| **スタブ系** | スタブ（Stub） | 内部に向かうコミュニケーション（入力）を模倣。返す値を設定できる | 依存 → SUT |
| | ダミー（Dummy） | メソッドシグネチャを満たすためだけに使う（null、空文字列等） | ― |
| | フェイク（Fake） | まだ存在しない依存の代替。インメモリDB等の簡易実装 | 依存 → SUT |

**核心的な違い**: モック系はコミュニケーションを **模倣 + 検証** する。スタブ系は **模倣のみ** で検証はしない。

---

## 2. コマンド・クエリ分離（CQS）との対応

テストダブルの選択は、置き換える対象のメソッドが **コマンド** か **クエリ** かで決まる。

| メソッド種別 | 定義 | 副作用 | 戻り値 | 対応するテストダブル | 検証すべきか |
|:---|:---|:---|:---|:---|:---|
| **コマンド** | 状態を変更する操作 | あり | void | **モック** | 呼び出し回数を検証する |
| **クエリ** | 値を返すだけの操作 | なし | あり | **スタブ** | 呼び出し自体は検証しない |

---

## 3. モック対象の判断フロー

### 依存の分類

```
依存オブジェクトのメソッドは？
  ├── 副作用がある（コマンド）
  │     ├── アプリケーション境界を超える？（管理外依存）
  │     │     ├── YES → モックで検証 ✅
  │     │     └── NO  → モック不要（内部通信はテストしない）
  │     └── 管理下にある依存（自アプリ専用DB等）？
  │           └── 実物 or インメモリ版（フェイク）を使用
  └── 値を返すだけ（クエリ）
        └── スタブで置換（呼び出しは検証しない）
```

### 管理外依存 vs 管理下依存

| 依存の種類 | 定義 | 例 | テストダブル |
|:---|:---|:---|:---|
| **管理外依存** | 他のアプリケーションと共有されるプロセス外依存 | 外部API、メッセージキュー、メール送信サービス | **モックで検証** |
| **管理下依存** | 自アプリケーション専用のプロセス外依存 | 自アプリ専用のDB、ファイルシステム | **実物 or フェイクを使用** |
| **内部依存** | 同一プロセス内のクラス・モジュール | ドメインモデル、ユーティリティクラス | **テストダブル不要**（そのまま使う） |

CRITICAL: **データベースは管理下依存** → モックにしない。インメモリ版やテスト用DBインスタンスを使う。

---

## 4. 言語別コード例

### 4.1 Python: モック（コマンドの検証）

```python
from unittest.mock import Mock

class OrderService:
    def __init__(self, email_gateway, inventory_repo):
        self._email_gateway = email_gateway
        self._inventory_repo = inventory_repo

    def place_order(self, order: Order) -> None:
        # Retrieve inventory (query — stub target)
        stock = self._inventory_repo.get_stock(order.product_id)
        if stock < order.quantity:
            raise InsufficientStockError(order.product_id)

        # Update inventory (managed dependency — use real or fake)
        self._inventory_repo.reduce_stock(order.product_id, order.quantity)

        # Send confirmation email (unmanaged dependency — mock target)
        self._email_gateway.send_confirmation(
            order.customer_email, order.id
        )


def test_placing_order_sends_confirmation_email():
    # Arrange
    email_gateway = Mock()  # mock for unmanaged dependency (command)
    inventory_repo = Mock()  # stub for query
    inventory_repo.get_stock.return_value = 10  # stub setup only

    service = OrderService(email_gateway, inventory_repo)
    order = Order(
        id="ORD-2024-001",
        customer_email="tanaka@example.co.jp",
        product_id="SKU-A100",
        quantity=3,
    )

    # Act
    service.place_order(order)

    # Assert — verify command (mock)
    email_gateway.send_confirmation.assert_called_once_with(
        "tanaka@example.co.jp", "ORD-2024-001"
    )
    # DO NOT verify: inventory_repo.get_stock.assert_called_once_with(...)
    # ↑ This would be overspecification (stub verification anti-pattern)
```

### 4.2 Python: スパイ（手書きモック）

```python
class SpyEmailGateway:
    """Hand-written mock (spy) for email gateway."""

    def __init__(self) -> None:
        self.sent_emails: list[tuple[str, str]] = []

    def send_confirmation(self, email: str, order_id: str) -> None:
        self.sent_emails.append((email, order_id))


def test_placing_order_sends_confirmation_email_with_spy():
    # Arrange
    email_spy = SpyEmailGateway()
    inventory_repo = FakeInventoryRepo(initial_stock={"SKU-A100": 10})
    service = OrderService(email_spy, inventory_repo)
    order = Order(
        id="ORD-2024-002",
        customer_email="suzuki@example.co.jp",
        product_id="SKU-A100",
        quantity=2,
    )

    # Act
    service.place_order(order)

    # Assert
    assert email_spy.sent_emails == [("suzuki@example.co.jp", "ORD-2024-002")]
```

### 4.3 TypeScript: モック（Vitest）

```typescript
import { describe, it, expect, vi } from "vitest";

interface EmailGateway {
  sendConfirmation(email: string, orderId: string): Promise<void>;
}

interface InventoryRepo {
  getStock(productId: string): Promise<number>;
  reduceStock(productId: string, quantity: number): Promise<void>;
}

describe("OrderService", () => {
  it("sends confirmation email when order is placed", async () => {
    // Arrange
    const emailGateway: EmailGateway = {
      sendConfirmation: vi.fn().mockResolvedValue(undefined), // mock
    };
    const inventoryRepo: InventoryRepo = {
      getStock: vi.fn().mockResolvedValue(10), // stub
      reduceStock: vi.fn().mockResolvedValue(undefined),
    };
    const service = new OrderService(emailGateway, inventoryRepo);

    // Act
    await service.placeOrder({
      id: "ORD-2024-003",
      customerEmail: "yamada@example.co.jp",
      productId: "SKU-B200",
      quantity: 1,
    });

    // Assert — verify command only
    expect(emailGateway.sendConfirmation).toHaveBeenCalledOnce();
    expect(emailGateway.sendConfirmation).toHaveBeenCalledWith(
      "yamada@example.co.jp",
      "ORD-2024-003"
    );
    // DO NOT: expect(inventoryRepo.getStock).toHaveBeenCalled()
  });
});
```

---

## 5. スタブの過剰検証（アンチパターン）

スタブに対する呼び出しを検証することは **過剰検証（overspecification）** であり、テストを壊れやすくする最大の原因の一つ。

### 悪い例: スタブの呼び出しを検証

```python
def test_bad_greeting_verifies_stub():
    # Arrange
    repo = Mock()
    repo.get_user.return_value = User("Alice")  # stub setup
    service = UserService(repo)

    # Act
    greeting = service.greet_user(1)

    # Assert
    assert greeting == "Hello, Alice!"
    repo.get_user.assert_called_once_with(1)  # NG: overspecification!
```

**なぜダメか**: `get_user` はクエリ（値を返すだけ）であり、最終結果を生み出すための一過程に過ぎない。内部でキャッシュを導入して `get_user` の呼び出し回数が変わっても、振る舞い（`greeting` の値）は変わらない。呼び出し回数の検証は実装詳細への結合。

### 良い例: 最終結果のみ検証

```python
def test_greeting_includes_user_name():
    # Arrange
    repo = Mock()
    repo.get_user.return_value = User("Alice")  # stub setup only
    service = UserService(repo)

    # Act
    greeting = service.greet_user(1)

    # Assert — only verify the final observable result
    assert greeting == "Hello, Alice!"
```

---

## 6. モック対象の型は自プロジェクトが所有する型のみ

サードパーティライブラリのインターフェースを直接モックしてはならない。

### 原則

```
サードパーティAPI（例: AWS SDK, Stripe SDK）
    ↓ アダプタパターンで変換
自プロジェクトのインターフェース（例: IPaymentGateway）
    ↓ テスト時はここをモック
テスト対象コード
```

### 理由

1. サードパーティAPIのインターフェースが変更されるとテストが壊れる
2. 自プロジェクトのインターフェースに変換することで、テストがプロジェクトのドメイン言語で書ける
3. サードパーティへの依存が1箇所（アダプタ）に集中し、変更時の影響範囲が限定される

---

## 7. モックの呼び出し回数は必ず確認する

モックに対しては **何回呼ばれたか** を必ず検証する。「少なくとも1回呼ばれた」ではなく **正確に1回** を確認する。

```python
# Good: exact call count
email_gateway.send_confirmation.assert_called_once_with(
    "tanaka@example.co.jp", "ORD-2024-001"
)

# Bad: at least once (hides duplicate send bug)
email_gateway.send_confirmation.assert_called_with(
    "tanaka@example.co.jp", "ORD-2024-001"
)
```

**理由**: メール2通送信、メッセージキューへの二重投入などの重複バグを検出するため。

---

## 8. 判断早見表

| 状況 | テストダブルの選択 | 検証方法 |
|:---|:---|:---|
| 外部APIへのリクエスト送信 | モック | 呼び出し回数 + 引数を検証 |
| メッセージキューへの投入 | モック | 投入されたメッセージの内容を検証 |
| メール送信 | モック | 送信先・件名・本文を検証 |
| DBからのデータ取得 | スタブ or フェイク | 最終結果のみ検証（呼び出しは検証しない） |
| DBへのデータ書込み（自アプリ専用） | フェイク（インメモリDB） | 書込み後の状態を検証 |
| 設定値の取得 | スタブ | 設定値に依存する振る舞いの結果を検証 |
| ドメインモデル間のやり取り | テストダブル不要 | 実オブジェクトをそのまま使う |
| 現在日時 | 値として注入 | 固定日時を引数で渡す |
