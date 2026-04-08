# モーション・トランジション・アニメーション設計ガイド

> UI に「命」を吹き込むモーション設計の原則、実装パターン、アクセシビリティ対応。

---

## 1. ページロード演出パターン（Staggered Reveal）

Anthropic が「最も効果的なモーションパターン」と評価する手法。
要素を時間差で順番に表示し、ページに「命」を与える。

### パターン A: 上方向フェードイン（最も汎用的）

```css
/* Basic staggered fade-in-up */
.reveal-item {
  opacity: 0;
  transform: translateY(24px);
  animation: fadeInUp 0.6s cubic-bezier(0.22, 1, 0.36, 1) forwards;
}

.reveal-item:nth-child(1) { animation-delay: 0.1s; }
.reveal-item:nth-child(2) { animation-delay: 0.2s; }
.reveal-item:nth-child(3) { animation-delay: 0.3s; }
.reveal-item:nth-child(4) { animation-delay: 0.4s; }
.reveal-item:nth-child(5) { animation-delay: 0.5s; }

@keyframes fadeInUp {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
```

### パターン B: スケールイン（カードグリッド向け）

```css
/* Scale-in for card grids */
.card-reveal {
  opacity: 0;
  transform: scale(0.92);
  animation: scaleIn 0.5s cubic-bezier(0.22, 1, 0.36, 1) forwards;
}

.card-reveal:nth-child(1) { animation-delay: 0.05s; }
.card-reveal:nth-child(2) { animation-delay: 0.1s; }
.card-reveal:nth-child(3) { animation-delay: 0.15s; }
.card-reveal:nth-child(4) { animation-delay: 0.2s; }
.card-reveal:nth-child(5) { animation-delay: 0.25s; }
.card-reveal:nth-child(6) { animation-delay: 0.3s; }

@keyframes scaleIn {
  to {
    opacity: 1;
    transform: scale(1);
  }
}
```

### パターン C: ブラーイン（ヒーローセクション向け）

```css
/* Blur-in for hero sections */
.hero-reveal {
  opacity: 0;
  filter: blur(8px);
  transform: translateY(16px);
  animation: blurIn 0.8s cubic-bezier(0.22, 1, 0.36, 1) forwards;
}

.hero-reveal:nth-child(1) { animation-delay: 0s; }
.hero-reveal:nth-child(2) { animation-delay: 0.15s; }
.hero-reveal:nth-child(3) { animation-delay: 0.3s; }

@keyframes blurIn {
  to {
    opacity: 1;
    filter: blur(0);
    transform: translateY(0);
  }
}
```

### 設計原則

| 原則 | 説明 |
|:---|:---|
| **最重要コンテンツが最初** | ヒーローテキスト → サブテキスト → CTA → 装飾の順 |
| **delay の間隔は 50-150ms** | 間隔が短すぎると同時に見え、長すぎると遅く感じる |
| **全体の入場時間は 300-800ms** | 最後の要素が表示されるまでの合計時間 |
| **1ページ1演出** | 複数の入場アニメーションを混ぜない |

---

## 2. トランジション速度ガイド

### 速度の基準

| インタラクション | 推奨時間 | easing | 根拠 |
|:---|:---|:---|:---|
| **ホバー** | 150-300ms | `ease-out` | 即座に反応する感覚を維持 |
| **フォーカス** | 100-200ms | `ease-out` | キーボード操作の即時フィードバック |
| **展開・折りたたみ** | 200-400ms | `ease-in-out` | コンテンツ変化の認知に十分な時間 |
| **モーダル表示** | 200-300ms | `cubic-bezier(0.22, 1, 0.36, 1)` | 注目を集める適切な速度 |
| **ページ遷移** | 300-500ms | `ease-in-out` | コンテキスト切り替えの認知 |
| **スライダー** | 300-500ms | `ease-in-out` | コンテンツのスライド移動 |

### easing 関数の選択基準

```css
:root {
  /* Standard: most UI interactions */
  --ease-standard: cubic-bezier(0.4, 0, 0.2, 1);

  /* Decelerate: elements entering the screen */
  --ease-decelerate: cubic-bezier(0, 0, 0.2, 1);

  /* Accelerate: elements leaving the screen */
  --ease-accelerate: cubic-bezier(0.4, 0, 1, 1);

  /* Expressive: emphasis, attention-grabbing */
  --ease-expressive: cubic-bezier(0.22, 1, 0.36, 1);
}
```

| easing | 用途 | 印象 |
|:---|:---|:---|
| `--ease-standard` | 汎用インタラクション | 自然で滑らか |
| `--ease-decelerate` | 要素の出現・入場 | ゆっくり着地する安定感 |
| `--ease-accelerate` | 要素の退場・消滅 | 素早く去る軽快さ |
| `--ease-expressive` | 強調・注目誘導 | ダイナミックで印象的 |

---

## 3. CSS-only アニメーション集

コピペ可能な `@keyframes` 定義。CSS-only で実現できるものは CSS-only で実装する。

### fadeInUp

```css
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(24px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Usage */
.animate-fadeInUp {
  animation: fadeInUp 0.6s var(--ease-expressive) forwards;
}
```

### slideIn（左右からのスライド）

```css
@keyframes slideInLeft {
  from {
    opacity: 0;
    transform: translateX(-32px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(32px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

/* Usage */
.animate-slideInLeft {
  animation: slideInLeft 0.5s var(--ease-decelerate) forwards;
}
.animate-slideInRight {
  animation: slideInRight 0.5s var(--ease-decelerate) forwards;
}
```

### scaleIn

```css
@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.9);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

/* Usage */
.animate-scaleIn {
  animation: scaleIn 0.4s var(--ease-expressive) forwards;
}
```

### blurIn

```css
@keyframes blurIn {
  from {
    opacity: 0;
    filter: blur(8px);
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    filter: blur(0);
    transform: translateY(0);
  }
}

/* Usage */
.animate-blurIn {
  animation: blurIn 0.6s var(--ease-decelerate) forwards;
}
```

### shimmer（スケルトンスクリーン用）

```css
@keyframes shimmer {
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
}

/* Skeleton placeholder */
.skeleton {
  background: linear-gradient(
    90deg,
    hsl(210, 15%, 92%) 25%,
    hsl(210, 15%, 96%) 50%,
    hsl(210, 15%, 92%) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
  border-radius: 4px;
}

.skeleton-text {
  height: 1em;
  margin-bottom: 0.5em;
}

.skeleton-title {
  height: 1.5em;
  width: 60%;
  margin-bottom: 1em;
}
```

### インタラクションフィードバック

```css
/* Button hover + active */
.btn {
  transition: transform 200ms var(--ease-standard),
              box-shadow 200ms var(--ease-standard);
}

.btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px hsla(0, 0%, 0%, 0.15);
}

.btn:active {
  transform: translateY(0);
  box-shadow: 0 1px 3px hsla(0, 0%, 0%, 0.2);
}

/* Card hover elevation */
.card {
  transition: transform 250ms var(--ease-standard),
              box-shadow 250ms var(--ease-standard);
}

.card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px hsla(0, 0%, 0%, 0.1),
              0 4px 8px hsla(0, 0%, 0%, 0.06);
}

/* Focus ring */
.focusable:focus-visible {
  outline: 2px solid var(--primary-500);
  outline-offset: 2px;
  transition: outline-offset 100ms var(--ease-standard);
}
```

---

## 4. React Motion ライブラリ連携

CSS-only では表現が難しい複雑なアニメーション（ジェスチャー、レイアウトアニメーション、Exit アニメーション）には、React 向け Motion ライブラリを活用する。

### framer-motion / Motion ライブラリ基本パターン

#### 基本的な出現アニメーション

```tsx
import { motion } from "framer-motion";

// Basic fade-in-up
function FadeInSection({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </motion.div>
  );
}
```

#### Staggered Reveal（子要素の時間差表示）

```tsx
import { motion } from "framer-motion";

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.1,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 24 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] },
  },
};

function StaggeredList({ items }: { items: string[] }) {
  return (
    <motion.ul
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {items.map((item, i) => (
        <motion.li key={i} variants={itemVariants}>
          {item}
        </motion.li>
      ))}
    </motion.ul>
  );
}
```

#### Exit アニメーション（AnimatePresence）

```tsx
import { AnimatePresence, motion } from "framer-motion";

function Modal({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            className="backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />
          {/* Modal content */}
          <motion.div
            className="modal"
            initial={{ opacity: 0, scale: 0.95, y: 16 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 16 }}
            transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
          >
            {/* ... */}
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
```

#### レイアウトアニメーション

```tsx
import { motion } from "framer-motion";

// Elements smoothly animate to new positions when layout changes
function LayoutCard({ isExpanded }: { isExpanded: boolean }) {
  return (
    <motion.div layout transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}>
      <motion.h3 layout="position">Card Title</motion.h3>
      {isExpanded && (
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          Expanded content here...
        </motion.p>
      )}
    </motion.div>
  );
}
```

### ライブラリ選定ガイド

| ライブラリ | 推奨場面 | 特徴 |
|:---|:---|:---|
| **CSS transitions/animations** | ホバー、フォーカス、単純な入場 | ゼロ依存、最高パフォーマンス |
| **framer-motion / Motion** | Exit アニメ、レイアウトアニメ、ジェスチャー | React 標準、宣言的 API |
| **react-spring** | 物理ベースアニメーション | 自然な動き、spring 計算 |
| **CSS `@starting-style`** | 要素の初期表示アニメーション | ネイティブ、ゼロ依存（対応ブラウザ注意） |

---

## 5. アクセシビリティ

### `prefers-reduced-motion` の完全実装

前庭障害や動きに敏感なユーザーへの配慮は必須。すべてのアニメーションに対応コードを含める。

#### CSS での対応

```css
/* Approach 1: Remove all animations (recommended as base) */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}

/* Approach 2: Per-component graceful degradation */
@media (prefers-reduced-motion: reduce) {
  .reveal-item {
    opacity: 1;
    transform: none;
    animation: none;
  }

  .card {
    transition: box-shadow 200ms var(--ease-standard);
    /* Keep shadow change but remove transform */
  }

  .card:hover {
    transform: none;
  }
}
```

#### React での対応

```tsx
import { useReducedMotion } from "framer-motion";

function AnimatedCard({ children }: { children: React.ReactNode }) {
  const shouldReduceMotion = useReducedMotion();

  return (
    <motion.div
      initial={shouldReduceMotion ? false : { opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={
        shouldReduceMotion
          ? { duration: 0 }
          : { duration: 0.5, ease: [0.22, 1, 0.36, 1] }
      }
    >
      {children}
    </motion.div>
  );
}
```

#### JavaScript での検出

```javascript
// Check user preference
const prefersReducedMotion = window.matchMedia(
  "(prefers-reduced-motion: reduce)"
).matches;

// Listen for changes
window
  .matchMedia("(prefers-reduced-motion: reduce)")
  .addEventListener("change", (event) => {
    if (event.matches) {
      // Disable or simplify animations
    }
  });
```

### WCAG 準拠ガイド

| 基準 | 要件 | 実装 |
|:---|:---|:---|
| **WCAG 2.3.1 (A)** | 3Hz 以上の点滅を含むコンテンツを避ける | 点滅アニメーションの周波数を 3Hz 未満に制限 |
| **WCAG 2.3.3 (AAA)** | モーションアニメーションを無効化できる | `prefers-reduced-motion` に対応 |
| **WCAG 2.2.2 (A)** | 自動再生コンテンツは 5 秒以内に停止可能 | 無限ループアニメーションに停止ボタンを提供 |
| **WCAG 2.2.1 (A)** | タイミング制御が可能 | ユーザーが制御できないタイムアウトを避ける |

### チェックリスト

- [ ] すべてのアニメーションに `prefers-reduced-motion` 対応がある
- [ ] 点滅は 3Hz 以下に制限されている
- [ ] 無限ループアニメーションに停止手段がある
- [ ] アニメーション時間は 150-500ms の範囲内
- [ ] `transform` と `opacity` のみをアニメーション対象にしている（レイアウトシフト防止）
- [ ] フォーカス状態はアニメーション無効時でも視覚的に明確
