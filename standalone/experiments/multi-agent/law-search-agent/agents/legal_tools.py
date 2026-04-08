import requests
import json
import re
from typing import Union
from config import config

try:
    from strands import tool
except ImportError:
    def tool(func):
        func.is_tool = True
        return func

@tool
def check_applicability(situation: str) -> str:
    """
    この状況に適用される法令は？
    
    Args:
        situation (str): 具体的な状況や事例
        
    Returns:
        str: 適用可能性のある法令と解説
    """
    try:
        # 状況から関連キーワードを抽出
        keywords = _extract_situation_keywords(situation)
        
        applicable_laws = []
        
        # 各キーワードで法令検索
        for keyword in keywords:
            search_result = _search_for_situation(keyword)
            if search_result:
                applicable_laws.extend(search_result)
        
        if not applicable_laws:
            return f"NO_APPLICABLE_LAWS:状況 '{situation}' に明確に適用される法令が特定できませんでした。より具体的な状況説明をお試しください。"
        
        # 適用可能性を評価
        evaluated_laws = []
        for law in applicable_laws[:5]:  # 上位5件
            evaluation = _evaluate_applicability(situation, law)
            evaluated_laws.append(evaluation)
        
        result = {
            "⚖️ 状況": situation,
            "🎯 適用可能性のある法令": evaluated_laws,
            "💡 実務上の注意": _generate_practical_advice(situation, evaluated_laws),
            "🔍 詳細確認": "具体的な条文内容は analysis_tools.py の explain_article をご利用ください"
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return f"ERROR:APPLICABILITY:適用性チェックエラー: {e}"

@tool
def find_penalties(law_id: str) -> str:
    """
    罰則・制裁措置を検索
    
    Args:
        law_id (str): 法令ID、法令番号、または法令履歴ID
        
    Returns:
        str: 罰則情報
    """
    try:
        # 法令データを取得
        law_data = _get_law_data_for_penalties(law_id)
        if "ERROR:" in str(law_data):
            return str(law_data)
        
        # 罰則条文を検索
        penalty_info = _extract_penalty_provisions(law_data)
        
        if not penalty_info["罰則条文"]:
            return f"NO_PENALTIES:法令 '{law_id}' に明確な罰則規定が見つかりませんでした。"
        
        penalty_result = {
            "⚖️ 対象法令": _extract_law_basic_info(law_data),
            "🚨 罰則条文": penalty_info["罰則条文"],
            "💰 罰金・科料": penalty_info["金銭罰"],
            "🏛️ 刑事罰": penalty_info["刑事罰"],
            "📋 行政罰": penalty_info["行政罰"],
            "⚠️ 重要事項": _generate_penalty_warnings(penalty_info)
        }
        
        return json.dumps(penalty_result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return f"ERROR:PENALTY_SEARCH:罰則検索エラー: {e}"

@tool
def find_procedures(law_id: str, procedure_type: str = "全般") -> str:
    """
    手続き・届出要件を検索
    
    Args:
        law_id (str): 法令ID
        procedure_type (str): 手続きの種類（"申請", "届出", "許可", "全般"）
        
    Returns:
        str: 手続き情報
    """
    try:
        law_data = _get_law_data_for_procedures(law_id)
        if "ERROR:" in str(law_data):
            return str(law_data)
        
        procedures = _extract_procedure_requirements(law_data, procedure_type)
        
        if not procedures:
            return f"NO_PROCEDURES:法令 '{law_id}' に {procedure_type} の手続き規定が見つかりませんでした。"
        
        procedure_result = {
            "📋 対象法令": _extract_law_basic_info(law_data),
            "📝 手続き種別": procedure_type,
            "✅ 必要な手続き": procedures["必要手続き"],
            "📅 期限・締切": procedures["期限"],
            "📄 必要書類": procedures["必要書類"],
            "🏢 提出先": procedures["提出先"],
            "💡 実務アドバイス": _generate_procedure_advice(procedures)
        }
        
        return json.dumps(procedure_result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return f"ERROR:PROCEDURE_SEARCH:手続き検索エラー: {e}"

@tool
def assess_legal_risk(situation: str, action: str) -> str:
    """
    法的リスクを評価
    
    Args:
        situation (str): 現在の状況
        action (str): 取ろうとする行動
        
    Returns:
        str: リスク評価結果
    """
    try:
        # 状況と行動から法的リスクを分析
        risk_factors = _identify_risk_factors(situation, action)
        applicable_laws = _find_relevant_laws_for_risk(situation, action)
        
        risk_assessment = {
            "⚠️ 評価対象": {
                "状況": situation,
                "予定行動": action
            },
            "🎯 関連法令": applicable_laws,
            "🚨 リスクレベル": _calculate_risk_level(risk_factors),
            "⚡ 特定リスク": risk_factors,
            "🛡️ 対策・回避方法": _suggest_risk_mitigation(risk_factors),
            "📞 推奨アクション": _recommend_next_steps(risk_factors)
        }
        
        return json.dumps(risk_assessment, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return f"ERROR:RISK_ASSESSMENT:リスク評価エラー: {e}"

# ヘルパー関数
def _extract_situation_keywords(situation: str) -> list:
    """状況から関連キーワードを抽出"""
    keywords = []
    
    # 業務分野のキーワード
    business_keywords = {
        "個人情報": ["個人情報保護", "プライバシー", "データ保護"],
        "契約": ["民法", "商法", "契約"],
        "労働": ["労働基準法", "労働契約", "雇用"],
        "会社": ["会社法", "商法", "法人"],
        "建設": ["建築基準法", "都市計画", "建設業"],
        "食品": ["食品衛生法", "食品安全", "保健所"],
        "医療": ["医療法", "薬事法", "医師法"],
        "教育": ["教育基本法", "学校教育", "教員"],
        "環境": ["環境基本法", "廃棄物", "公害"]
    }
    
    for key, related_terms in business_keywords.items():
        if key in situation:
            keywords.extend(related_terms)
    
    # 行為のキーワード
    action_keywords = {
        "販売": ["販売", "商取引", "消費者"],
        "提供": ["サービス提供", "業務提供"],
        "収集": ["情報収集", "データ収集"],
        "公開": ["情報公開", "開示"],
        "変更": ["変更届", "更新"],
        "廃止": ["廃止届", "終了"]
    }
    
    for key, related_terms in action_keywords.items():
        if key in situation:
            keywords.extend(related_terms)
    
    return list(set(keywords)) if keywords else ["一般"]

def _search_for_situation(keyword: str) -> list:
    """状況に関連する法令を検索"""
    try:
        url = f"{config.LAWS_API_BASE_URL}/keyword"
        params = {"keyword": keyword}
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        api_data = response.json()
        laws = api_data.get("items", [])
        
        results = []
        for law in laws[:3]:  # 各キーワードにつき最大3件
            law_info = law.get("law_info", {})
            revision_info = law.get("revision_info", {})
            
            results.append({
                "法令名": revision_info.get("law_title", "不明"),
                "法令ID": law_info.get("law_id", ""),
                "関連度": "高" if keyword in revision_info.get("law_title", "") else "中"
            })
        
        return results
        
    except Exception:
        return []

def _evaluate_applicability(situation: str, law: dict) -> dict:
    """法令の適用可能性を評価"""
    law_name = law.get("法令名", "")
    
    # 簡単な適用可能性判定
    applicability_score = "中"
    
    situation_lower = situation.lower()
    law_lower = law_name.lower()
    
    # 高い関連性の判定
    if any(keyword in law_lower for keyword in ["基本", "一般", "共通"]):
        applicability_score = "高"
    
    # 具体的な分野の一致
    field_matches = ["個人情報", "労働", "建築", "食品", "医療", "教育"]
    for field in field_matches:
        if field in situation and field in law_name:
            applicability_score = "高"
            break
    
    return {
        "法令名": law_name,
        "適用可能性": applicability_score,
        "理由": _generate_applicability_reason(situation, law_name, applicability_score)
    }

def _generate_applicability_reason(situation: str, law_name: str, score: str) -> str:
    """適用可能性の理由を生成"""
    if score == "高":
        return f"状況と法令名に直接的な関連性があります"
    elif score == "中":
        return f"間接的に関連する可能性があります"
    else:
        return f"関連性は低いと思われます"

def _generate_practical_advice(situation: str, laws: list) -> list:
    """実務上のアドバイスを生成"""
    advice = []
    
    if laws:
        advice.append("🔍 特定された関連法令の詳細条文を確認してください")
        advice.append("⚖️ 具体的な適用については専門家への相談を推奨します")
        
        # 高い適用可能性がある場合
        high_relevance_laws = [law for law in laws if law.get("適用可能性") == "高"]
        if high_relevance_laws:
            advice.append(f"🎯 特に「{high_relevance_laws[0].get('法令名', '')}」は重点的に確認が必要です")
    else:
        advice.append("📝 より具体的な状況説明で再検索をお試しください")
    
    return advice

def _get_law_data_for_penalties(law_id: str) -> dict:
    """罰則検索用の法令データ取得"""
    try:
        url = f"{config.LAWS_API_BASE_URL}/law_data/{law_id}"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        law_data = response.json()
        if not law_data:
            return {"ERROR": f"法令ID '{law_id}' が見つかりません"}
            
        return law_data
        
    except Exception as e:
        return {"ERROR": f"データ取得エラー: {e}"}

def _extract_penalty_provisions(law_data: dict) -> dict:
    """罰則条文を抽出"""
    full_text = law_data.get("law_full_text", {})
    text_content = _extract_text_from_json(full_text)
    
    penalty_info = {
        "罰則条文": [],
        "金銭罰": [],
        "刑事罰": [],
        "行政罰": []
    }
    
    # 罰則キーワードで検索
    penalty_patterns = [
        r"(第\d+条.*?(?:罰金|科料|懲役|禁錮).*?)(?=第\d+条|$)",
        r"(罰則.*?)(?=第\d+条|\n\n|$)",
        r"(違反.*?(?:罰金|科料|懲役).*?)(?=第\d+条|\n\n|$)"
    ]
    
    for pattern in penalty_patterns:
        matches = re.finditer(pattern, text_content, re.DOTALL)
        for match in matches:
            penalty_text = match.group(1).strip()
            if penalty_text:
                penalty_info["罰則条文"].append(penalty_text)
                
                # 罰則の分類
                if "罰金" in penalty_text or "科料" in penalty_text:
                    penalty_info["金銭罰"].append(penalty_text)
                if "懲役" in penalty_text or "禁錮" in penalty_text:
                    penalty_info["刑事罰"].append(penalty_text)
    
    # 重複除去
    for key in penalty_info:
        penalty_info[key] = list(set(penalty_info[key]))
    
    return penalty_info

def _extract_law_basic_info(law_data: dict) -> dict:
    """法令基本情報を抽出"""
    law_info = law_data.get("law_info", {})
    revision_info = law_data.get("revision_info", {})
    
    return {
        "法令名": revision_info.get("law_title", "不明"),
        "法令番号": law_info.get("law_num", "不明"),
        "法令ID": law_info.get("law_id", "不明")
    }

def _generate_penalty_warnings(penalty_info: dict) -> list:
    """罰則に関する警告を生成"""
    warnings = []
    
    if penalty_info["刑事罰"]:
        warnings.append("⚠️ 刑事罰（懲役・禁錮）が規定されています - 重大な違反行為です")
    
    if penalty_info["金銭罰"]:
        warnings.append("💰 罰金・科料が規定されています - 金銭的制裁があります")
    
    if not penalty_info["罰則条文"]:
        warnings.append("ℹ️ 明確な罰則規定は見つかりませんでした")
    
    warnings.append("📞 具体的な適用については法律専門家にご相談ください")
    
    return warnings

def _get_law_data_for_procedures(law_id: str) -> dict:
    """手続き検索用の法令データ取得"""
    return _get_law_data_for_penalties(law_id)  # 同じ処理

def _extract_procedure_requirements(law_data: dict, procedure_type: str) -> dict:
    """手続き要件を抽出"""
    full_text = law_data.get("law_full_text", {})
    text_content = _extract_text_from_json(full_text)
    
    procedures = {
        "必要手続き": [],
        "期限": [],
        "必要書類": [],
        "提出先": []
    }
    
    # 手続きキーワードで検索
    procedure_keywords = {
        "申請": ["申請", "申し込み", "願い出"],
        "届出": ["届出", "届け出", "通知"],
        "許可": ["許可", "認可", "承認"],
        "全般": ["手続", "書類", "提出", "申請", "届出", "許可"]
    }
    
    search_keywords = procedure_keywords.get(procedure_type, procedure_keywords["全般"])
    
    for keyword in search_keywords:
        # 簡単なパターンマッチング
        pattern = f"({keyword}.*?)(?=第\\d+条|\\n\\n|$)"
        matches = re.finditer(pattern, text_content, re.DOTALL)
        
        for match in matches:
            procedure_text = match.group(1).strip()
            if len(procedure_text) < 500:  # 長すぎる場合は除外
                procedures["必要手続き"].append(procedure_text)
    
    # その他の情報抽出（簡易版）
    if "日以内" in text_content or "月以内" in text_content:
        procedures["期限"].append("法令本文に期限の記載があります")
    
    if "書類" in text_content or "様式" in text_content:
        procedures["必要書類"].append("法令本文に必要書類の記載があります")
    
    return procedures

def _generate_procedure_advice(procedures: dict) -> list:
    """手続きアドバイスを生成"""
    advice = []
    
    if procedures["必要手続き"]:
        advice.append("📋 該当する手続きが見つかりました")
        advice.append("📅 期限がある場合は早めの対応を推奨します")
    
    advice.append("🏢 詳細な提出先・様式は関係官庁にお問い合わせください")
    advice.append("💼 複雑な手続きは行政書士等の専門家への相談を推奨します")
    
    return advice

def _identify_risk_factors(situation: str, action: str) -> list:
    """リスク要因を特定"""
    risk_factors = []
    
    # 高リスクキーワード
    high_risk_keywords = ["個人情報", "金銭", "契約", "販売", "提供", "公開", "収集"]
    
    combined_text = f"{situation} {action}"
    
    for keyword in high_risk_keywords:
        if keyword in combined_text:
            risk_factors.append({
                "要因": keyword,
                "リスクレベル": "注意",
                "説明": f"{keyword}に関連する行為は法的規制の対象となる可能性があります"
            })
    
    return risk_factors

def _find_relevant_laws_for_risk(situation: str, action: str) -> list:
    """リスク評価のための関連法令検索"""
    keywords = _extract_situation_keywords(f"{situation} {action}")
    laws = []
    
    for keyword in keywords[:3]:  # 最大3つのキーワード
        search_results = _search_for_situation(keyword)
        laws.extend(search_results)
    
    return laws[:5]  # 最大5つの法令

def _calculate_risk_level(risk_factors: list) -> str:
    """リスクレベルを計算"""
    if not risk_factors:
        return "低"
    elif len(risk_factors) >= 3:
        return "高"
    else:
        return "中"

def _suggest_risk_mitigation(risk_factors: list) -> list:
    """リスク軽減策を提案"""
    suggestions = []
    
    if risk_factors:
        suggestions.append("📖 関連法令の詳細な確認")
        suggestions.append("👥 法律専門家への事前相談")
        suggestions.append("📋 適切な手続きの確認・実施")
        suggestions.append("📝 必要な場合は契約書面の整備")
    else:
        suggestions.append("✅ 特別な対策は不要と思われます")
    
    return suggestions

def _recommend_next_steps(risk_factors: list) -> list:
    """推奨する次のアクションを提案"""
    steps = []
    
    if risk_factors:
        steps.append("1️⃣ 関連法令の詳細条文を analysis_tools で確認")
        steps.append("2️⃣ 必要な手続きを find_procedures で確認")
        steps.append("3️⃣ 罰則の有無を find_penalties で確認")
        steps.append("4️⃣ 法律専門家への相談を検討")
    else:
        steps.append("✅ 現時点で特別な対応は不要と思われます")
    
    return steps

def _extract_text_from_json(law_json_data) -> str:
    """JSON構造からテキストを抽出"""
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