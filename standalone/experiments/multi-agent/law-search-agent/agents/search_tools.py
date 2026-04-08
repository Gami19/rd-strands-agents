import requests
import json
from typing import Union
from config import config

try:
    from strands import tool
except ImportError:
    def tool(func):
        func.is_tool = True
        return func

@tool
def smart_search(keyword: str, max_results: int = None) -> str:
    """
    賢い法令検索（キーワード最適化付き）
    
    Args:
        keyword (str): 検索キーワード
        max_results (int): 最大結果件数
    
    Returns:
        str: 検索結果（JSON形式）
    
    検索例:
    - 基本: "民法", "デジタル庁"
    - ワイルドカード: "第*条", "第?条"
    - AND検索: "デジタル庁 AND 設置"
    - OR検索: "個人情報 OR プライバシー"
    """
    if max_results is None:
        max_results = config.MAX_SEARCH_RESULTS
    
    # キーワードの自動最適化
    optimized_keyword = _optimize_search_keyword(keyword)
    
    try:
        url = f"{config.LAWS_API_BASE_URL}/keyword"
        params = {"keyword": optimized_keyword}
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        api_data = response.json()
        
        if not isinstance(api_data, dict) or "items" not in api_data:
            return f"ERROR:API_FORMAT:予期しないAPI応答形式です"
            
        laws = api_data["items"]
        total_count = api_data.get("total_count", len(laws))
        
        if not laws:
            return f"NO_RESULTS:キーワード '{keyword}' に合致する法令が見つかりませんでした。ワイルドカード(*、?)やAND/OR検索をお試しください。"
        
        # 検索結果を整理（検索特化の詳細情報）
        results = []
        for i, law in enumerate(laws[:max_results]):
            law_info = law.get("law_info", {})
            revision_info = law.get("revision_info", {})
            sentences = law.get("sentences", [])
            
            # マッチした条文（検索専門として詳細に）
            matched_texts = []
            for sentence in sentences[:3]:
                position = sentence.get("position", "")
                text = sentence.get("text", "")
                if text:
                    if len(text) > 80:
                        text = text[:80] + "..."
                    matched_texts.append(f"📍 {position}: {text}")
            
            result = {
                "🏆 順位": i + 1,
                "📜 法令名": revision_info.get("law_title", "不明"),
                "🔢 法令番号": law_info.get("law_num", "不明"),
                "🆔 法令ID": law_info.get("law_id", ""),
                "📅 公布日": law_info.get("promulgation_date", ""),
                "🎯 マッチした条文": matched_texts,
                "🔗 関連度": _calculate_relevance(keyword, sentences)
            }
            results.append(result)
        
        search_result = {
            "🔍 検索キーワード": keyword,
            "⚡ 最適化後": optimized_keyword,
            "📊 総件数": total_count,
            "📋 表示件数": len(results),
            "📚 法令一覧": results
        }
        
        return json.dumps(search_result, ensure_ascii=False, indent=2)
        
    except requests.RequestException as e:
        return f"ERROR:API_CALL:法令API呼び出しエラー: {e}"
    except Exception as e:
        return f"ERROR:SYSTEM:システムエラー: {e}"

@tool
def find_related_laws(law_id: str) -> str:
    """
    関連法令の自動発見
    
    Args:
        law_id (str): 基準となる法令ID
        
    Returns:
        str: 関連法令のリスト
    """
    try:
        # まず基準法令の情報を取得
        base_law_info = _get_basic_law_info(law_id)
        if "ERROR:" in base_law_info:
            return base_law_info
        
        # 基準法令から関連キーワードを抽出
        keywords = _extract_related_keywords(base_law_info)
        
        # 関連法令を検索
        related_results = []
        for keyword in keywords:
            result = smart_search(keyword, max_results=2)
            if "ERROR:" not in result and "NO_RESULTS:" not in result:
                related_results.append({
                    "関連キーワード": keyword,
                    "検索結果": result
                })
        
        if not related_results:
            return f"NO_RESULTS:法令ID '{law_id}' に関連する法令が見つかりませんでした。"
        
        return json.dumps({
            "🏛️ 基準法令": base_law_info,
            "🔗 関連法令": related_results
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return f"ERROR:RELATED_SEARCH:関連法令検索エラー: {e}"

@tool
def search_by_article_advanced(article_pattern: str, additional_keyword: str = "") -> str:
    """
    高度な条文パターン検索
    
    Args:
        article_pattern (str): 条文パターン（例: "第1条", "第*条"）
        additional_keyword (str): 追加キーワード
        
    Returns:
        str: 検索結果
    """
    if additional_keyword:
        keyword = f"{article_pattern} AND {additional_keyword}"
    else:
        keyword = article_pattern
        
    result = smart_search(keyword)
    
    # 条文検索専用の後処理
    if "ERROR:" not in result and "NO_RESULTS:" not in result:
        # 条文に特化した情報を追加
        enhanced_result = _enhance_article_search_result(result, article_pattern)
        return enhanced_result
    
    return result

# ヘルパー関数
def _optimize_search_keyword(keyword: str) -> str:
    """検索キーワードの自動最適化"""
    # よくある表記ゆれを統一
    optimizations = {
        "デジタル庁": "デジタル庁",
        "個人情報": "個人情報保護",
        "民法": "民法",
        # 追加の最適化ルールをここに
    }
    
    for original, optimized in optimizations.items():
        if original in keyword and original != optimized:
            keyword = keyword.replace(original, optimized)
    
    return keyword

def _calculate_relevance(keyword: str, sentences: list) -> str:
    """関連度の計算"""
    if not sentences:
        return "低"
    
    match_count = sum(1 for s in sentences if keyword.lower() in s.get("text", "").lower())
    if match_count >= 3:
        return "高"
    elif match_count >= 1:
        return "中"
    else:
        return "低"

def _get_basic_law_info(law_id: str) -> str:
    """法令の基本情報を取得"""
    try:
        url = f"{config.LAWS_API_BASE_URL}/law_data/{law_id}"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        law_data = response.json()
        if not law_data:
            return f"ERROR:NO_DATA:法令ID '{law_id}' が見つかりません"
        
        law_info = law_data.get("law_info", {})
        revision_info = law_data.get("revision_info", {})
        
        return json.dumps({
            "法令名": revision_info.get("law_title", "不明"),
            "法令番号": law_info.get("law_num", "不明"),
            "法令ID": law_id
        }, ensure_ascii=False)
        
    except Exception as e:
        return f"ERROR:BASIC_INFO:基本情報取得エラー: {e}"

def _extract_related_keywords(law_info: str) -> list:
    """法令情報から関連キーワードを抽出"""
    # 簡単なキーワード抽出ロジック
    keywords = []
    
    if "デジタル" in law_info:
        keywords.extend(["情報システム", "電子政府", "行政手続"])
    if "個人情報" in law_info:
        keywords.extend(["プライバシー", "データ保護", "情報管理"])
    if "民法" in law_info:
        keywords.extend(["契約", "財産", "損害賠償"])
    
    return keywords[:3]  # 最大3つまで

def _enhance_article_search_result(result: str, article_pattern: str) -> str:
    """条文検索結果の拡張"""
    try:
        result_data = json.loads(result)
        result_data["🎯 条文検索特化情報"] = {
            "検索パターン": article_pattern,
            "条文解析": "条文の詳細解析は analysis_tools.py の explain_article をご利用ください",
            "実務適用": "実務上の適用については legal_tools.py の check_applicability をご利用ください"
        }
        return json.dumps(result_data, ensure_ascii=False, indent=2)
    except:
        return result