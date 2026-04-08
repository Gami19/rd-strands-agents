# テスト設計アンチパターン集

> 表面上は問題を適切に対処しているように見えても、あとになってより大きな問題として遭遇する間違ったテスト設計パターンを集約し、「なぜダメか」「どう直すか」の対比で示す。

---

## AP-1: private メソッドの直接テスト

### なぜダメか

- テストが **実装の詳細** に結合する（リファクタリング耐性がゼロ）
- メソッド名変更・内部分割のたびにテストが壊れる（偽陽性の量産）
- カプセル化を破壊し、クラスの不変条件が外部から侵害されるリスクが生まれる

### どう直すか

**パターン A**: 公開 API 経由で間接的に検証する。

```python
# BAD: order._get_price() を直接テスト
# GOOD: 公開メソッド経由で検証
def test_order_description_includes_correct_total():
    order = Order(Customer("Tanaka Corp"), [Product("Widget A", Decimal("5000"))])
    description = order.generate_description()
    assert "Total: 5000" in description
```

**パターン B**: 複雑な private ロジックは **抽象化の欠落** を示唆。別クラスに抽出して独立テスト。

```python
# GOOD: extract hidden complexity into its own testable class
class PriceCalculator:
    def calculate(self, customer: Customer, products: list[Product]) -> Decimal: ...

def test_price_calculation_applies_tax_after_discount():
    result = PriceCalculator().calculate(premium_customer, [product_a])
    assert result == Decimal("10800")
```

---

## AP-2: 実装の詳細への結合（壊れやすいテスト）

### なぜダメか

- 内部の呼び出し順序やメソッド名を変更するだけでテストが壊れる（偽陽性）
- テストがプロダクションコードの「鏡像」になり、退行保護に寄与しない

### どう直すか

**最終的な観察可能な結果** のみを検証する。

```python
# BAD: db.get_user.assert_called_once_with(1) ← 実装詳細
# GOOD: 振る舞いの最終結果を検証
def test_user_rename_trims_and_truncates_name():
    user = User(name="Old Name")
    user.name = "  Tanaka Taro Very Long Name That Exceeds Fifty Characters  "
    assert len(user.name) <= 50
```

**判断基準**: 「非エンジニアのドメインエキスパートにとっても意味がある検証か？」を自問する。

---

## AP-3: 1テストで複数の振る舞いを検証

### なぜダメか

- 最初の Act が失敗すると後続の Act は実行されず、問題の特定が困難
- テスト名が1つの振る舞いを表現できない
- 統合テストやシナリオテストの兆候であり、単体テストとしては不適切

### どう直すか

1つの振る舞いに対して1つのテストを書く。**Act は常に1つ**。

```python
# BAD: cart.add → assert → cart.add → assert → cart.remove → assert

# GOOD: 1 test = 1 act
def test_adding_item_increases_cart_count():
    cart = ShoppingCart()
    cart.add_item("Widget", 2)
    assert cart.item_count == 1
```

---

## AP-4: 共有セットアップの過度な利用

### なぜダメか

- 各テストにとって **何が重要な前提条件なのか** が見えなくなる（可読性の低下）
- 共有セットアップの変更が無関係なテストを壊す（テスト間の暗黙的な結合）
- Arrange フェーズがテストから分離され、テストの意図が自明でなくなる

### どう直すか

各テストの Arrange で **意図が自明になる最小限のセットアップ** を行う。共通部分はファクトリメソッドに抽出。

```python
# BAD: setup_method で全テスト共通の customer, product, order を構築
# GOOD: factory method with only relevant parameters
def _create_order(is_premium: bool = False, price: Decimal = Decimal("5000")) -> Order:
    return Order(Customer("Tanaka", is_premium=is_premium), [Product("Widget", price)])

def test_premium_customer_gets_15_percent_discount():
    order = _create_order(is_premium=True, price=Decimal("10000"))
    assert OrderService(Mock()).calculate_total(order) == Decimal("8500")
```

---

## AP-5: テスト名が実装に依存

### なぜダメか

- メソッド名が変わるとテスト名も変えなければならない（リファクタリング耐性の低下）
- テストが「何を検証しているか」ではなく「どのメソッドを呼んでいるか」を伝えている

### どう直すか

**振る舞いを自然言語で平叙文として記述**。「should」で始めない。メソッド名を含めない。

```
BAD:  test_IsDeliveryValid_InvalidDate_ReturnsFalse
GOOD: test_delivery_with_past_date_is_invalid

BAD:  test_CalculateDiscount_PremiumTrue_Returns1500
GOOD: test_premium_customer_with_large_order_gets_15_percent_discount
```

---

## AP-6: AAA パターンの違反

### 6a: テスト内の if 文

テストケースは **分岐のない直線的なコード** でなければならない。if 文は「1つのテストで複数の振る舞いを検証している」兆候。分岐ごとに独立したテストを書く。

### 6b: ドメイン知識の漏洩（Assert での計算ロジック）

```python
# BAD: expected = value1 + value2 ← production code algorithm leaked
# GOOD: assert Calculator.add(100, 500) == 600  ← hard-coded expected
```

期待値は **ハードコード** する。プロダクションコードのアルゴリズムをテストに複製しない。

### 6c: Arrange の肥大化

Arrange が 20 行以上 → テスト対象が **過度に複雑なコード** である可能性が高い。Humble Object パターンでビジネスロジックを分離し、単体テストの Arrange を小さく保つ。

---

## AP-7: プロダクションコードへのテスト用汚染

### なぜダメか

- テスト用コード（フラグ、分岐）がプロダクションコードに混入し、保守コストが増加
- テスト用フラグが本番環境で誤って有効化されるリスクがある

### どう直すか

インターフェースを導入し、本番実装とテスト実装を分離する。

```python
# BAD: Logger(is_test_environment=True) ← test flag in production code
# GOOD: interface separation
class LoggerProtocol(ABC):
    @abstractmethod
    def log(self, text: str) -> None: ...

class Logger(LoggerProtocol): ...        # production — no test logic
class FakeLogger(LoggerProtocol): ...    # test code only
```

---

## AP-8: 具象クラスに対するテストダブル

### なぜダメか

- 具象クラスが **単一責任の原則（SRP）に違反** していることを示唆
- 「計算ロジック」と「外部依存との通信」が1つのクラスに混在
- 部分的モックは脆く、元クラスの内部実装に依存する

### どう直すか

2つの責務を分離し、それぞれ独立したクラスにする。

```python
# BAD: Mock(spec=StatisticsCalculator, wraps=...) で一部だけ override
# GOOD: split into two classes
class DeliveryGateway:   # external communication — mock target
    def get_deliveries(self, customer_id: int) -> list[DeliveryRecord]: ...

class StatisticsCalculator:  # pure domain logic — no mocks needed
    def calculate(self, records: list[DeliveryRecord]) -> tuple[float, float]: ...
```

---

## アンチパターン早見表

| # | アンチパターン | 4本柱への影響 | 修正方針 |
|:---|:---|:---|:---|
| AP-1 | private メソッドの直接テスト | リファクタリング耐性 = 0 | 公開API経由でテスト or 抽象化を抽出 |
| AP-2 | 実装の詳細への結合 | リファクタリング耐性 = 0 | 観察可能な振る舞いのみ検証 |
| AP-3 | 1テスト複数 Act | 保守性が低下、障害特定が困難 | 1テスト = 1振る舞い = 1 Act |
| AP-4 | 共有セットアップの過度な利用 | 保守性が低下、可読性が喪失 | テストごとに意図が自明な最小 Arrange |
| AP-5 | 実装依存のテスト名 | リファクタリング耐性が低下 | 振る舞いを自然言語の平叙文で記述 |
| AP-6 | AAA パターン違反 | 退行保護 + リファクタリング耐性が低下 | 期待値ハードコード、分岐なし、Arrange 最小化 |
| AP-7 | プロダクションコードへの汚染 | 保守性が低下 | インターフェース分離で本番/テスト実装を分ける |
| AP-8 | 具象クラスへのテストダブル | リファクタリング耐性が低下 | SRP 違反を修正し責務を分離 |
