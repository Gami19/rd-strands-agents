import requests
import json
import base64
from typing import Union
from config import config

try:
    from strands import tool
except ImportError:
    def tool(func):
        func.is_tool = True
        return func

@tool
def explain_article(law_id: str, article_num: str = "") -> str:
    """
    条文をわかりやすく解説
    
    Args:
        law_id (str): 法令ID、法令番号、または法令履歴ID
        article_num (str): 条文番号（空の場合は法令全体）
        
    Returns:
        str: 条文の詳細解説
    """
    try:
        # 法令データを取得
        law_data = _get_law_full_data(law_id)
        if "ERROR:" in law_data:
            return law_data
        
        # 条文特定の場合
        if article_num:
            article_text = _extract_specific_article(law_data, article_num)
            if "ERROR:" in article_text:
                return article_text
                
            explanation = {
                "📜 対象条文": f"第{article_num}条",
                "📝 条文内容": article_text,
                "🎯 重要ポイント": _identify_key_points(article_text),
                "🔍 用語解説": _explain_legal_terms(article_text),
                "🌟 実務上の意味": _practical_implications(article_text),
                "🔗 関連条文": _find_related_articles(law_data, article_num)
            }
        else:
            # 法令全体の解説
            explanation = _explain_entire_law(law_data)
        
        return json.dumps(explanation, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return f"ERROR:EXPLANATION:条文解説エラー: {e}"

@tool
def summarize_law(law_id: str) -> str:
    """
    法令の要点まとめ
    
    Args:
        law_id (str): 法令ID、法令番号、または法令履歴ID
        
    Returns:
        str: 法令の要約
    """
    try:
        law_data = _get_law_full_data(law_id)
        if "ERROR:" in law_data:
            return law_data
        
        summary = {
            "📋 法令概要": _extract_law_overview(law_data),
            "🎯 目的・趣旨": _extract_purpose(law_data),
            "📊 構成・章立て": _analyze_law_structure(law_data),
            "⭐ 重要条文": _identify_important_articles(law_data),
            "📅 施行・改正情報": _extract_enforcement_info(law_data),
            "🔗 関連法令": _suggest_related_laws(law_data)
        }
        
        return json.dumps(summary, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return f"ERROR:SUMMARY:法令要約エラー: {e}"

@tool
def analyze_law_structure(law_id: str) -> str:
    """
    法令の構造を詳細分析
    
    Args:
        law_id (str): 法令ID
        
    Returns:
        str: 法令構造の分析結果
    """
    try:
        law_data = _get_law_full_data(law_id)
        if "ERROR:" in law_data:
            return law_data
        
        structure_analysis = {
            "🏗️ 法令構造": _parse_law_hierarchy(law_data),
            "📊 条文統計": _calculate_article_statistics(law_data),
            "🎭 条文種別": _categorize_articles(law_data),
            "📈 複雑度分析": _analyze_complexity(law_data)
        }
        
        return json.dumps(structure_analysis, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return f"ERROR:STRUCTURE:構造分析エラー: {e}"

# ヘルパー関数
def _get_law_full_data(law_id: str) -> str:
    """法令の完全データを取得"""
    try:
        url = f"{config.LAWS_API_BASE_URL}/law_data/{law_id}"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        law_data = response.json()
        if not law_data:
            return f"ERROR:NO_DATA:法令ID '{law_id}' が見つかりません"
            
        return law_data
        
    except Exception as e:
        return f"ERROR:DATA_FETCH:データ取得エラー: {e}"

def _extract_specific_article(law_data: dict, article_num: str) -> str:
    """特定の条文を抽出"""
    # 法令本文から指定された条文を検索
    full_text = law_data.get("law_full_text", {})
    text_content = _extract_text_from_json(full_text)
    
    # 第X条のパターンを検索
    import re
    patterns = [
        f"第{article_num}条",
        f"第{article_num.zfill(2)}条",
        f"第{article_num}條"  # 旧字体
    ]
    
    for pattern in patterns:
        match = re.search(f"{pattern}.*?(?=第\\d+条|$)", text_content, re.DOTALL)
        if match:
            return match.group(0)
    
    return f"ERROR:NOT_FOUND:第{article_num}条が見つかりませんでした"

def _identify_key_points(article_text: str) -> list:
    """条文の重要ポイントを特定"""
    key_points = []
    
    # キーワードベースの重要ポイント抽出
    important_keywords = ["目的", "定義", "権利", "義務", "禁止", "罰則", "適用"]
    
    for keyword in important_keywords:
        if keyword in article_text:
            key_points.append(f"💡 {keyword}に関する規定が含まれています")
    
    return key_points if key_points else ["📝 一般的な法的規定です"]

def _explain_legal_terms(article_text: str) -> dict:
    """法律用語の解説"""
    legal_terms = {
        "この法律": "この法令自身を指します",
        "何人も": "すべての人（個人・法人問わず）",
        "みなす": "法的に同じものとして扱う",
        "推定する": "証拠がない限り、そうであると考える"
    }
    
    found_terms = {}
    for term, explanation in legal_terms.items():
        if term in article_text:
            found_terms[term] = explanation
    
    return found_terms if found_terms else {"一般用語": "特別な法律用語は使用されていません"}

def _practical_implications(article_text: str) -> str:
    """実務上の意味を推測"""
    if "目的" in article_text:
        return "この条文は法令の目的を定めており、他の条文の解釈基準となります"
    elif "定義" in article_text:
        return "この条文は重要な用語の定義を行っており、法令全体の理解に必要です"
    elif "禁止" in article_text or "してはならない" in article_text:
        return "この条文は禁止事項を定めており、違反すると法的責任が生じる可能性があります"
    else:
        return "具体的な権利・義務や手続きを定めた規定です"

def _find_related_articles(law_data: dict, article_num: str) -> list:
    """関連条文を検索"""
    # 簡単な関連条文検索ロジック
    related = []
    
    # 前後の条文
    try:
        num = int(article_num)
        related.extend([f"第{num-1}条", f"第{num+1}条"])
    except:
        pass
    
    return [f"🔗 {art}" for art in related[:3]]

def _explain_entire_law(law_data: dict) -> dict:
    """法令全体の解説"""
    law_info = law_data.get("law_info", {})
    revision_info = law_data.get("revision_info", {})
    
    return {
        "📜 法令名": revision_info.get("law_title", "不明"),
        "📅 制定": law_info.get("promulgation_date", "不明"),
        "🎯 概要": "詳細な解説は summarize_law ツールをご利用ください",
        "📖 重要条文": "explain_article で個別条文の詳細解説が可能です"
    }

def _extract_law_overview(law_data: dict) -> dict:
    """法令概要を抽出"""
    law_info = law_data.get("law_info", {})
    revision_info = law_data.get("revision_info", {})
    
    return {
        "法令名": revision_info.get("law_title", "不明"),
        "法令番号": law_info.get("law_num", "不明"),
        "公布日": law_info.get("promulgation_date", "不明"),
        "施行日": revision_info.get("enforcement_date", "不明")
    }

def _extract_purpose(law_data: dict) -> str:
    """目的条文を抽出"""
    full_text = law_data.get("law_full_text", {})
    text_content = _extract_text_from_json(full_text)
    
    # 第1条または目的条文を検索
    import re
    purpose_match = re.search(r"第一?条.*?目的.*?。", text_content)
    if purpose_match:
        return purpose_match.group(0)
    else:
        return "目的条文が明確に特定できませんでした"

def _analyze_law_structure(law_data: dict) -> dict:
    """法令構造を分析"""
    full_text = law_data.get("law_full_text", {})
    text_content = _extract_text_from_json(full_text)
    
    # 章・条文数の概算
    import re
    chapters = len(re.findall(r"第.*章", text_content))
    articles = len(re.findall(r"第.*条", text_content))
    
    return {
        "推定章数": chapters if chapters > 0 else "不明",
        "推定条文数": articles if articles > 0 else "不明",
        "構成": "章立てがある法令" if chapters > 0 else "章立てのない法令"
    }

def _identify_important_articles(law_data: dict) -> list:
    """重要条文を特定"""
    return [
        "📌 第1条（目的）",
        "📌 定義条文",
        "📌 罰則条文"
    ]

def _extract_enforcement_info(law_data: dict) -> dict:
    """施行・改正情報を抽出"""
    law_info = law_data.get("law_info", {})
    revision_info = law_data.get("revision_info", {})
    
    return {
        "公布日": law_info.get("promulgation_date", "不明"),
        "施行日": revision_info.get("enforcement_date", "不明"),
        "最終改正": revision_info.get("amendment_promulgate_date", "なし")
    }

def _suggest_related_laws(law_data: dict) -> list:
    """関連法令を提案"""
    return ["🔗 関連法令の詳細検索は search_tools.py の find_related_laws をご利用ください"]

def _extract_text_from_json(law_json_data) -> str:
    """JSON構造からテキストを抽出（既存の関数を再利用）"""
    if isinstance(law_json_data, str):
        return law_json_data
    
    def extract_recursive(node):
        texts = []
        if isinstance(node, dict):
            if "children" in node:
                for child in node["children"]:
                    if isinstance(child, str):
                        texts.append(child)
                    else:
                        texts.extend(extract_recursive(child))
            if "text" in node and isinstance(node["text"], str):
                texts.append(node["text"])
            for key, value in node.items():
                if key not in ["children", "text", "tag", "attr"]:
                    texts.extend(extract_recursive(value))
        elif isinstance(node, list):
            for item in node:
                texts.extend(extract_recursive(item))
        return texts
    
    extracted_parts = extract_recursive(law_json_data)
    return "".join(extracted_parts)

def _parse_law_hierarchy(law_data: dict) -> dict:
    """法令階層を解析"""
    return {"階層解析": "詳細な階層解析機能は今後実装予定"}

def _calculate_article_statistics(law_data: dict) -> dict:
    """条文統計を計算"""
    return {"統計情報": "条文統計機能は今後実装予定"}

def _categorize_articles(law_data: dict) -> dict:
    """条文を種別分類"""
    return {"条文分類": "条文分類機能は今後実装予定"}

def _analyze_complexity(law_data: dict) -> dict:
    """複雑度を分析"""
    return {"複雑度": "複雑度分析機能は今後実装予定"}