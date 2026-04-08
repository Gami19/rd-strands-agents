# JavaScript → TypeScript 移行パターン

> 段階的移行戦略・ファイル単位の変換手順・型定義の書き方・よくあるエラーと対処法の実践リファレンス

---

## 1. 段階的移行戦略（strict: false → strict: true）

### Phase 0: 準備（移行前）

```
目標: TypeScript コンパイラを導入し、JS/TS の共存環境を構築する

1. TypeScript をインストール
   npm install --save-dev typescript @types/node

2. tsconfig.json を作成（最小限の設定）
   {
     "compilerOptions": {
       "target": "ES2022",
       "module": "NodeNext",
       "moduleResolution": "NodeNext",
       "outDir": "./dist",
       "rootDir": "./src",
       "allowJs": true,          // JS ファイルをそのまま処理
       "checkJs": false,         // JS の型チェックはまだ無効
       "strict": false,          // 段階的に有効化
       "esModuleInterop": true,
       "skipLibCheck": true,
       "declaration": true
     },
     "include": ["src"]
   }

3. ビルドスクリプトを更新
   "scripts": {
     "build": "tsc",
     "typecheck": "tsc --noEmit"
   }
```

### Phase 1: allowJs + checkJs による漸進的チェック

```
目標: JS ファイルを TS に変換せずに型チェックの恩恵を受ける

1. 個別ファイルに @ts-check を追加
   // @ts-check
   /** @type {string} */
   const name = "Alice";

2. JSDoc で型アノテーションを記述
   /**
    * @param {string} userId
    * @returns {Promise<User>}
    */
   async function getUser(userId) { ... }

3. 型エラーを段階的に修正
```

### Phase 2: ファイル単位の .js → .ts 変換

```
目標: 依存関係グラフの末端（importされる側）から .ts に変換

変換順序:
  1. ユーティリティ関数（他に依存しない純粋関数）
  2. 型定義ファイル（interface / type のみ）
  3. データアクセス層（DB / API クライアント）
  4. ビジネスロジック
  5. コントローラー / ルーター
  6. エントリーポイント（index.ts）
```

### Phase 3: strict フラグの段階的有効化

| 段階 | フラグ | 影響範囲 | 対処の難易度 |
|:---|:---|:---|:---|
| 1 | `noImplicitAny` | 型アノテーションのない引数にエラー | 中（量が多いが対処は明確） |
| 2 | `strictNullChecks` | null/undefined の未チェック箇所にエラー | 高（影響範囲が広い） |
| 3 | `strictFunctionTypes` | 関数型の共変/反変チェック | 低（エラー少数） |
| 4 | `strictBindCallApply` | bind/call/apply の型チェック | 低 |
| 5 | `strictPropertyInitialization` | クラスプロパティの初期化チェック | 中 |
| 6 | `strict: true` | 上記すべて + 将来の strict フラグ | — |

**CRITICAL**: `noImplicitAny` が有効になるまで移行は**未完了**である（項目83）。

---

## 2. ファイル単位の移行手順

### Step-by-Step: 1 ファイルの変換

```typescript
// === Before: utils.js ===
function formatCurrency(amount, currency) {
  return new Intl.NumberFormat('ja-JP', {
    style: 'currency',
    currency: currency
  }).format(amount);
}
module.exports = { formatCurrency };

// === After: utils.ts ===
type CurrencyCode = "JPY" | "USD" | "EUR";

export function formatCurrency(
  amount: number,
  currency: CurrencyCode
): string {
  return new Intl.NumberFormat("ja-JP", {
    style: "currency",
    currency,
  }).format(amount);
}
```

### 変換チェックリスト（1 ファイルごと）

- [ ] 拡張子を `.js` → `.ts`（JSX なら `.jsx` → `.tsx`）に変更
- [ ] `require` → `import` に変換
- [ ] `module.exports` → `export` に変換
- [ ] 関数の引数に型アノテーションを追加
- [ ] パブリック API の戻り値に型を明示
- [ ] `any` を使った箇所を `unknown` またはより具体的な型に置換
- [ ] `tsc --noEmit` でエラーが 0 であることを確認
- [ ] 既存テストが通ることを確認

---

## 3. 型定義ファイル（.d.ts）の書き方

### 型定義が存在しないライブラリへの対応

```
優先順序:
  1. @types/xxx が DefinitelyTyped に存在するか確認
     npm install --save-dev @types/xxx

  2. ライブラリ自体に型定義が同梱されているか確認
     node_modules/xxx/index.d.ts

  3. 上記どちらもない場合 → 自作の .d.ts を作成
```

### 最小限の型定義テンプレート

```typescript
// types/legacy-lib.d.ts

// Module declaration for untyped library
declare module "legacy-lib" {
  // Export specific functions/classes you actually use
  export function initialize(config: LegacyConfig): void;
  export function process(data: unknown): ProcessResult;

  export interface LegacyConfig {
    apiKey: string;
    timeout?: number;
    retries?: number;
  }

  export interface ProcessResult {
    success: boolean;
    data: Record<string, unknown>;
    errors: string[];
  }
}
```

### Global 型の拡張（Module Augmentation）

```typescript
// types/express-extensions.d.ts

// Extend Express Request with custom properties
declare module "express" {
  interface Request {
    userId?: string;
    tenantId?: string;
  }
}
```

### 型定義の粒度ガイドライン

| 状況 | アプローチ | 理由 |
|:---|:---|:---|
| 広く使うライブラリ | 完全な型定義 | 投資対効果が高い |
| 特定箇所のみ使用 | 使う API のみ型定義 | 最小労力で最大効果 |
| 移行途中の自社コード | 段階的に型を追加 | 完璧より前進 |
| 非推奨・置換予定 | `declare module "xxx"` のみ | 投資を抑制 |

---

## 4. 型推論を活かした最小限の型アノテーション戦略

### 書くべき場所と書かないべき場所

```typescript
// NG: 冗長な型アノテーション（推論で十分）
const count: number = items.length;
const names: string[] = users.map((u: User): string => u.name);
const isValid: boolean = amount > 0;

// OK: 推論に任せる
const count = items.length;
const names = users.map((u) => u.name);
const isValid = amount > 0;

// OK: パブリック API には型を明示（項目27）
export function calculateDiscount(
  price: number,
  membershipLevel: MembershipLevel
): DiscountResult {
  // Internal implementation - let inference work
  const baseRate = DISCOUNT_RATES[membershipLevel];
  const adjustedRate = Math.min(baseRate * 1.1, 0.5);
  return { originalPrice: price, discountedPrice: price * (1 - adjustedRate) };
}
```

### satisfies 演算子の活用（TypeScript 5.0+）

```typescript
// satisfies: 型チェックしつつ、推論された型を保持
const ROUTES = {
  home: "/",
  about: "/about",
  contact: "/contact",
} satisfies Record<string, string>;

// ROUTES.home は string ではなく "/" リテラル型として推論される
// Record<string, string> を満たすことも保証される
```

---

## 5. 移行時のよくあるエラーと対処法

| エラー | 原因 | 対処法 |
|:---|:---|:---|
| `TS7006: Parameter 'x' implicitly has an 'any' type` | `noImplicitAny` 有効化後、型アノテーション不足 | 引数に型を追加。不明なら `unknown` で始めて絞り込む |
| `TS2322: Type 'null' is not assignable` | `strictNullChecks` 有効化後 | null チェックを追加: `if (value !== null)` |
| `TS2307: Cannot find module 'xxx'` | 型定義なし | `@types/xxx` をインストール、または `.d.ts` を自作 |
| `TS2345: Argument of type 'string' is not assignable to parameter of type 'X'` | 文字列リテラル型との不一致 | `as const` アサーション、または入力値を型ガードで絞り込む |
| `TS2532: Object is possibly 'undefined'` | Optional Chaining 未使用 | `obj?.prop` または `if (obj)` で絞り込む |
| `TS1259: Module 'xxx' can only be default-imported using 'esModuleInterop'` | CJS/ESM 混在 | `esModuleInterop: true` を設定 |
| `TS2339: Property 'xxx' does not exist on type 'yyy'` | 構造的型付けの不一致 | interface を拡張するか、型アサーションで対応 |
| `TS7016: Could not find a declaration file` | JS ライブラリに型なし | `types/` に `.d.ts` を作成 |
| `TS18046: 'xxx' is of type 'unknown'` | `unknown` 型の未絞り込み | 型ガード・`instanceof`・`typeof` で絞り込む |
| `TS2554: Expected N arguments, but got M` | オプション引数の未定義 | パラメーターに `?` を付与するか、デフォルト値を設定 |

### any の段階的除去戦略

```
Phase A: any のインベントリ作成
  → type-coverage ツールで any の割合を計測
  → npx type-coverage --detail で全箇所を一覧化

Phase B: 優先順位付け
  → パブリック API の any を最優先で除去
  → 内部ユーティリティは次点
  → テストコードは最後

Phase C: 置換パターン
  → any → unknown（最も安全。使用箇所で絞り込み必須）
  → any → 具体的な型（型が判明している場合）
  → any → ジェネリック T（関数が汎用的な場合）
  → any[] → unknown[]（配列の場合）
  → Record<string, any> → Record<string, unknown>
```

---

## 6. 移行の進捗管理

### 移行メトリクス

| メトリクス | 計測方法 | 目標値 |
|:---|:---|:---|
| **TS ファイル率** | `.ts` ファイル数 / 全ファイル数 | 100% |
| **型カバレッジ** | `type-coverage` ツール | 95%+ |
| **any 出現数** | `type-coverage --detail` | 0（理想） |
| **strict 準拠** | `tsc --strict --noEmit` の Exit Code | 0 |
| **テスト通過率** | Jest/Vitest の結果 | 100% |

### 移行完了の定義

```
移行完了 = 以下のすべてを満たす状態:
  ✓ 全 .js ファイルが .ts に変換済み
  ✓ tsconfig.json で strict: true が有効
  ✓ 型カバレッジが 95% 以上
  ✓ any の使用が 0（やむを得ない箇所は型安全な関数で隠蔽）
  ✓ 全テストが通過
  ✓ CI/CD に tsc --noEmit が組み込み済み
```
