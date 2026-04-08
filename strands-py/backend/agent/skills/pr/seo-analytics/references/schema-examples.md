# JSON-LD スキーマ実装例集

ページ種別ごとの完全な JSON-LD 実装例。コピー&ペーストで使用できるテンプレートとして設計。

---

## 目次
- Organization（企業・ブランド）
- WebSite（検索ボックス付き）
- Article / BlogPosting（ブログ記事）
- Product（商品ページ）
- SoftwareApplication（SaaS）
- FAQPage（FAQ）
- HowTo（ハウツー）
- BreadcrumbList（パンくず）
- LocalBusiness（ローカルビジネス）
- Event（イベント・ウェビナー）
- 複数スキーマの結合（@graph）
- 実装方法（Next.js / WordPress）
- バリデーション手順

---

## Organization

企業・ブランドのトップページまたは会社概要ページに配置する。

```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "株式会社サンプル",
  "url": "https://example.com",
  "logo": "https://example.com/images/logo.png",
  "sameAs": [
    "https://twitter.com/example",
    "https://www.linkedin.com/company/example",
    "https://www.facebook.com/example"
  ],
  "contactPoint": {
    "@type": "ContactPoint",
    "telephone": "+81-3-1234-5678",
    "contactType": "customer service",
    "availableLanguage": ["Japanese", "English"]
  },
  "description": "企業の説明文をここに記載"
}
```

---

## WebSite（検索ボックス付き）

トップページに配置。サイトリンク検索ボックスを有効化する。

```json
{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "name": "サイト名",
  "url": "https://example.com",
  "potentialAction": {
    "@type": "SearchAction",
    "target": {
      "@type": "EntryPoint",
      "urlTemplate": "https://example.com/search?q={search_term_string}"
    },
    "query-input": "required name=search_term_string"
  }
}
```

---

## Article / BlogPosting

ブログ記事・ニュース記事に配置する。AI検索での著者認識に重要。

```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "記事のタイトル（70文字以内推奨）",
  "image": "https://example.com/images/article-image.jpg",
  "datePublished": "2026-01-15T08:00:00+09:00",
  "dateModified": "2026-02-20T10:00:00+09:00",
  "author": {
    "@type": "Person",
    "name": "著者名",
    "url": "https://example.com/authors/name",
    "jobTitle": "肩書き",
    "worksFor": {
      "@type": "Organization",
      "name": "所属組織"
    }
  },
  "publisher": {
    "@type": "Organization",
    "name": "サイト名",
    "logo": {
      "@type": "ImageObject",
      "url": "https://example.com/images/logo.png"
    }
  },
  "description": "記事のメタディスクリプション",
  "mainEntityOfPage": {
    "@type": "WebPage",
    "@id": "https://example.com/blog/article-slug"
  }
}
```

---

## Product

EC・SaaS の商品ページに配置する。価格・レビュー情報をリッチリザルトに表示。

```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "商品名",
  "image": "https://example.com/images/product.jpg",
  "description": "商品の説明",
  "sku": "SKU-001",
  "brand": {
    "@type": "Brand",
    "name": "ブランド名"
  },
  "offers": {
    "@type": "Offer",
    "url": "https://example.com/products/product-name",
    "priceCurrency": "JPY",
    "price": "9800",
    "availability": "https://schema.org/InStock",
    "priceValidUntil": "2026-12-31"
  },
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.7",
    "reviewCount": "89"
  }
}
```

---

## SoftwareApplication

SaaS 商品ページ・アプリランディングページに配置する。

```json
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "アプリケーション名",
  "applicationCategory": "BusinessApplication",
  "operatingSystem": "Web, iOS, Android",
  "offers": {
    "@type": "AggregateOffer",
    "lowPrice": "0",
    "highPrice": "9800",
    "priceCurrency": "JPY",
    "offerCount": "3"
  },
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.5",
    "ratingCount": "320"
  }
}
```

---

## FAQPage

FAQ コンテンツに配置する。AI検索での引用率向上に特に効果的。

```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "質問文をここに記載する？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "回答文をここに記載する。50-100語程度で簡潔に回答する。"
      }
    },
    {
      "@type": "Question",
      "name": "2つ目の質問文？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "2つ目の回答文。HTML タグも使用可能（<a>, <b> 等）。"
      }
    },
    {
      "@type": "Question",
      "name": "3つ目の質問文？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "3つ目の回答文。"
      }
    }
  ]
}
```

---

## HowTo

チュートリアル・手順説明ページに配置する。

```json
{
  "@context": "https://schema.org",
  "@type": "HowTo",
  "name": "手順のタイトル",
  "description": "手順の概要説明",
  "totalTime": "PT15M",
  "step": [
    {
      "@type": "HowToStep",
      "name": "ステップ1のタイトル",
      "text": "ステップ1の詳細な説明をここに記載する。",
      "url": "https://example.com/guide#step1"
    },
    {
      "@type": "HowToStep",
      "name": "ステップ2のタイトル",
      "text": "ステップ2の詳細な説明をここに記載する。",
      "url": "https://example.com/guide#step2"
    },
    {
      "@type": "HowToStep",
      "name": "ステップ3のタイトル",
      "text": "ステップ3の詳細な説明をここに記載する。",
      "url": "https://example.com/guide#step3"
    }
  ]
}
```

---

## BreadcrumbList

パンくずナビゲーションのあるページに配置する。

```json
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {
      "@type": "ListItem",
      "position": 1,
      "name": "ホーム",
      "item": "https://example.com"
    },
    {
      "@type": "ListItem",
      "position": 2,
      "name": "ブログ",
      "item": "https://example.com/blog"
    },
    {
      "@type": "ListItem",
      "position": 3,
      "name": "記事タイトル",
      "item": "https://example.com/blog/article-slug"
    }
  ]
}
```

---

## LocalBusiness

実店舗・ローカルビジネスのページに配置する。

```json
{
  "@context": "https://schema.org",
  "@type": "LocalBusiness",
  "name": "店舗名",
  "image": "https://example.com/images/shop.jpg",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "東京都渋谷区神宮前1-2-3",
    "addressLocality": "渋谷区",
    "addressRegion": "東京都",
    "postalCode": "150-0001",
    "addressCountry": "JP"
  },
  "geo": {
    "@type": "GeoCoordinates",
    "latitude": "35.6762",
    "longitude": "139.6503"
  },
  "telephone": "+81-3-1234-5678",
  "openingHoursSpecification": [
    {
      "@type": "OpeningHoursSpecification",
      "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
      "opens": "09:00",
      "closes": "18:00"
    }
  ],
  "priceRange": "$$"
}
```

---

## Event

イベント・ウェビナー・カンファレンスのページに配置する。

```json
{
  "@context": "https://schema.org",
  "@type": "Event",
  "name": "イベント名",
  "startDate": "2026-06-15T09:00:00+09:00",
  "endDate": "2026-06-15T17:00:00+09:00",
  "eventAttendanceMode": "https://schema.org/OnlineEventAttendanceMode",
  "eventStatus": "https://schema.org/EventScheduled",
  "location": {
    "@type": "VirtualLocation",
    "url": "https://example.com/events/event-name"
  },
  "image": "https://example.com/images/event.jpg",
  "description": "イベントの概要説明",
  "offers": {
    "@type": "Offer",
    "url": "https://example.com/events/event-name/tickets",
    "price": "5000",
    "priceCurrency": "JPY",
    "availability": "https://schema.org/InStock",
    "validFrom": "2026-01-01"
  },
  "organizer": {
    "@type": "Organization",
    "name": "主催者名",
    "url": "https://example.com"
  }
}
```

---

## 複数スキーマの結合（@graph）

1ページに複数のスキーマを配置する場合は `@graph` で結合する。

```json
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": "https://example.com/#organization",
      "name": "企業名",
      "url": "https://example.com",
      "logo": "https://example.com/images/logo.png"
    },
    {
      "@type": "WebSite",
      "@id": "https://example.com/#website",
      "url": "https://example.com",
      "name": "サイト名",
      "publisher": {
        "@id": "https://example.com/#organization"
      }
    },
    {
      "@type": "BreadcrumbList",
      "itemListElement": [
        {
          "@type": "ListItem",
          "position": 1,
          "name": "ホーム",
          "item": "https://example.com"
        }
      ]
    }
  ]
}
```

---

## 実装方法

### Next.js

```jsx
export default function ArticlePage({ article }) {
  const schema = {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: article.title,
    image: article.image,
    datePublished: article.publishedAt,
    dateModified: article.updatedAt,
    author: {
      "@type": "Person",
      name: article.author.name,
    },
  };

  return (
    <>
      <Head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
        />
      </Head>
      {/* ページコンテンツ */}
    </>
  );
}
```

### WordPress

- **プラグイン**: Yoast SEO, Rank Math, Schema Pro で自動生成
- **テーマカスタム**: `wp_head` アクションフックで JSON-LD を出力
- **カスタムフィールド**: ACF 等でデータを入力し、テンプレートで JSON-LD に変換

---

## バリデーション手順

1. **Google Rich Results Test** で検証: リッチリザルト対応を確認
2. **Schema.org Validator** で構文検証: JSON-LD の文法エラーを検出
3. **Search Console 拡張レポート** で監視: 本番デプロイ後のエラー・警告を継続監視

### よくあるエラーと対処

| エラー | 原因 | 対処 |
|:---|:---|:---|
| 必須プロパティの欠落 | required な項目が未設定 | Google ドキュメントで必須項目を確認 |
| 日付形式の不正 | ISO 8601 形式でない | `YYYY-MM-DDThh:mm:ss+09:00` 形式に修正 |
| URL が完全修飾でない | 相対パスを使用している | `https://` からの完全URLに修正 |
| ページ内容との不一致 | 表示コンテンツとスキーマの値が異なる | 表示内容と一致させる |
