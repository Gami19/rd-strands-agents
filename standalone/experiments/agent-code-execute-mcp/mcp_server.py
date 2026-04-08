from fastmcp import FastMCP
import uvicorn
import uuid
import json
from typing import Dict, Any
import base64
import io
import pandas as pd
import numpy as np
import pickle
from pathlib import Path
import scipy.stats as stats
from scipy.stats import chi2_contingency, ttest_ind, f_oneway
import warnings
warnings.filterwarnings('ignore')
import matplotlib
matplotlib.use('Agg')  # GUI不要のバックエンド
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.io import to_image
import base64
from io import BytesIO
from datetime import datetime


# MCPサーバの初期化
mcp = FastMCP("Data Analysis MCP Server")

# グローバルストレージ（Phase 2で改善予定）
data_storage: Dict[str, Any] = {}
processing_states: Dict[str, Any] = {}

# フェーズ1
@mcp.tool()
def health_check() -> str:
    """MCPサーバのヘルスチェック"""
    return json.dumps({
        "status": "healthy",
        "server": "Data Analysis MCP Server",
        "version": "1.0.0",
        "active_datasets": len(data_storage),
        "active_processes": len(processing_states)
    }, ensure_ascii=False)

@mcp.tool()
def echo_test(message: str) -> str:
    """エコーテスト - 入力された文字列をそのまま返す"""
    return f"Echo: {message}"

@mcp.tool()
def load_sample_data() -> str:
    """サンプルデータを生成してテスト用に読み込む"""
    import pandas as pd
    import numpy as np
    
    # サンプルデータ生成
    np.random.seed(42)
    sample_data = {
        'id': range(1, 101),
        'name': [f'Product_{i}' for i in range(1, 101)],
        'price': np.random.uniform(100, 1000, 100),
        'sales': np.random.randint(10, 100, 100),
        'category': np.random.choice(['A', 'B', 'C'], 100)
    }
    
    df = pd.DataFrame(sample_data)
    
    # データIDを生成して保存
    data_id = str(uuid.uuid4())
    data_storage[data_id] = df
    
    info = {
        "data_id": data_id,
        "filename": "sample_data.csv",
        "shape": df.shape,
        "columns": df.columns.tolist(),
        "sample_data": df.head().to_dict()
    }
    
    return f"サンプルデータを生成しました。\n{json.dumps(info, indent=2, ensure_ascii=False)}"

@mcp.tool()
def list_datasets() -> str:
    """読み込み済みデータセット一覧を表示"""
    if not data_storage:
        return "読み込み済みデータセットはありません"
    
    datasets = []
    for data_id, df in data_storage.items():
        datasets.append({
            "data_id": data_id,
            "shape": df.shape,
            "columns": df.columns.tolist()
        })
    
    return json.dumps(datasets, indent=2, ensure_ascii=False)

@mcp.tool()
def simple_calculation(expression: str) -> str:
    """簡単な計算を実行（テスト用）"""
    try:
        # 安全性のためeval使用は制限
        allowed_chars = set('0123456789+-*/().')
        if not all(c in allowed_chars or c.isspace() for c in expression):
            return "エラー: 許可されていない文字が含まれています"
        
        result = eval(expression)
        return f"計算結果: {expression} = {result}"
    except Exception as e:
        return f"エラー: {str(e)}"

if __name__ == "__main__":
    print("Data Analysis MCP Server を起動しています...")
    print(f"HTTP サーバー: http://localhost:8000")
    print("利用可能なツール:")
    print("- health_check: サーバーのヘルスチェック")
    print("- echo_test: エコーテスト")
    print("- load_sample_data: サンプルデータ生成")
    print("- list_datasets: データセット一覧")
    print("- simple_calculation: 簡単な計算")
    
    # FastMCPのASGIアプリケーションを取得
    app = mcp.http_app()
    
    # HTTPサーバとして起動（修正）
    uvicorn.run(
        app,  # FastMCPのASGIアプリケーション
        host="localhost", 
        port=8000,
        timeout_keep_alive=3600,
        timeout_graceful_shutdown=3600,
        reload=False  # FastMCPとの互換性のためFalseに設定
    )

# フェーズ2
# データ保存ディレクトリ
DATA_DIR = Path("data")
TEMP_DIR = DATA_DIR / "temp"
STATE_DIR = DATA_DIR / "states"

# ディレクトリ作成
DATA_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)
STATE_DIR.mkdir(exist_ok=True)

@mcp.tool()
def load_dataset(file_data: str, file_type: str, filename: str, encoding: str = "utf-8") -> str:
    """データセットファイルを読み込む（CSV/Excel/JSON対応）
    
    Args:
        file_data: Base64エンコードされたファイルデータ
        file_type: ファイルタイプ (csv, excel, json)
        filename: ファイル名
        encoding: 文字エンコーディング (デフォルト: utf-8)
    """
    try:
        # Base64デコード
        decoded_data = base64.b64decode(file_data)
        
        # ファイルタイプに応じて読み込み
        if file_type.lower() == "csv":
            df = pd.read_csv(io.StringIO(decoded_data.decode(encoding)))
        elif file_type.lower() in ["excel", "xlsx", "xls"]:
            df = pd.read_excel(io.BytesIO(decoded_data))
        elif file_type.lower() == "json":
            df = pd.read_json(io.StringIO(decoded_data.decode(encoding)))
        else:
            return json.dumps({"error": f"サポートされていないファイル形式: {file_type}"}, ensure_ascii=False)
        
        # データIDを生成して保存
        data_id = str(uuid.uuid4())
        data_storage[data_id] = {
            "dataframe": df,
            "filename": filename,
            "file_type": file_type,
            "created_at": pd.Timestamp.now(),
            "encoding": encoding
        }
        
        # データ情報を生成
        info = {
            "data_id": data_id,
            "filename": filename,
            "file_type": file_type,
            "shape": df.shape,
            "columns": df.columns.tolist(),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "memory_usage": df.memory_usage(deep=True).sum(),
            "missing_values": df.isnull().sum().to_dict(),
            "sample_data": df.head(3).to_dict(),
            "created_at": data_storage[data_id]["created_at"].isoformat()
        }
        
        return json.dumps({
            "status": "success",
            "message": f"データセット '{filename}' を正常に読み込みました",
            "data": info
        }, indent=2, ensure_ascii=False)
        
    except UnicodeDecodeError as e:
        return json.dumps({"error": f"文字エンコーディングエラー: {e}. 別のencodingを試してください"}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"データ読み込みエラー: {str(e)}"}, ensure_ascii=False)

@mcp.tool()
def get_dataset_info(data_id: str) -> str:
    """データセットの詳細情報を取得"""
    try:
        if data_id not in data_storage:
            return json.dumps({"error": "指定されたdata_idが見つかりません"}, ensure_ascii=False)
        
        data_info = data_storage[data_id]
        df = data_info["dataframe"]
        
        # 詳細統計情報
        info = {
            "data_id": data_id,
            "filename": data_info["filename"],
            "file_type": data_info["file_type"],
            "shape": df.shape,
            "columns": df.columns.tolist(),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "memory_usage_mb": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
            "missing_values": df.isnull().sum().to_dict(),
            "numeric_columns": df.select_dtypes(include=[np.number]).columns.tolist(),
            "categorical_columns": df.select_dtypes(include=['object']).columns.tolist(),
            "datetime_columns": df.select_dtypes(include=['datetime']).columns.tolist(),
            "created_at": data_info["created_at"].isoformat(),
            "sample_data": {
                "head": df.head(3).to_dict(),
                "tail": df.tail(3).to_dict()
            }
        }
        
        # 数値列の基本統計
        if len(info["numeric_columns"]) > 0:
            info["basic_statistics"] = df[info["numeric_columns"]].describe().to_dict()
        
        return json.dumps(info, indent=2, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({"error": f"データ情報取得エラー: {str(e)}"}, ensure_ascii=False)

@mcp.tool()
def save_processing_state(data_id: str, operation: str, parameters: str, checkpoint_data: str = "") -> str:
    """処理状態を保存（Resume機能用）"""
    try:
        state_id = str(uuid.uuid4())
        
        state_info = {
            "state_id": state_id,
            "data_id": data_id,
            "operation": operation,
            "parameters": json.loads(parameters) if parameters else {},
            "checkpoint_data": checkpoint_data,
            "created_at": pd.Timestamp.now().isoformat(),
            "status": "saved"
        }
        
        # 状態をファイルに保存
        state_file = STATE_DIR / f"{state_id}.json"
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state_info, f, ensure_ascii=False, indent=2)
        
        # メモリにも保存
        processing_states[state_id] = state_info
        
        return json.dumps({
            "status": "success",
            "state_id": state_id,
            "message": "処理状態を保存しました"
        }, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({"error": f"状態保存エラー: {str(e)}"}, ensure_ascii=False)

@mcp.tool()
def resume_processing(state_id: str) -> str:
    """保存された処理状態から復帰"""
    try:
        # メモリから確認
        if state_id in processing_states:
            state_info = processing_states[state_id]
        else:
            # ファイルから読み込み
            state_file = STATE_DIR / f"{state_id}.json"
            if not state_file.exists():
                return json.dumps({"error": "指定されたstate_idが見つかりません"}, ensure_ascii=False)
            
            with open(state_file, 'r', encoding='utf-8') as f:
                state_info = json.load(f)
                processing_states[state_id] = state_info
        
        # データIDの確認
        data_id = state_info["data_id"]
        if data_id not in data_storage:
            return json.dumps({"error": "関連するデータセットが見つかりません"}, ensure_ascii=False)
        
        result = {
            "status": "success",
            "message": "処理状態を復帰しました",
            "state_info": {
                "state_id": state_id,
                "data_id": data_id,
                "operation": state_info["operation"],
                "parameters": state_info["parameters"],
                "created_at": state_info["created_at"]
            },
            "data_info": {
                "filename": data_storage[data_id]["filename"],
                "shape": data_storage[data_id]["dataframe"].shape
            }
        }
        
        return json.dumps(result, indent=2, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({"error": f"状態復帰エラー: {str(e)}"}, ensure_ascii=False)

@mcp.tool()
def list_processing_states(data_id: str = "") -> str:
    """処理状態一覧を表示"""
    try:
        states = []
        
        for state_id, state_info in processing_states.items():
            if not data_id or state_info["data_id"] == data_id:
                states.append({
                    "state_id": state_id,
                    "data_id": state_info["data_id"],
                    "operation": state_info["operation"],
                    "created_at": state_info["created_at"],
                    "status": state_info["status"]
                })
        
        return json.dumps({
            "status": "success",
            "total_states": len(states),
            "states": states
        }, indent=2, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({"error": f"状態一覧取得エラー: {str(e)}"}, ensure_ascii=False)

# フェーズ3
@mcp.tool()
def basic_statistics(data_id: str, columns: str = "") -> str:
    """基本統計量を計算する
    
    Args:
        data_id: データセットID
        columns: 分析対象カラム（JSON配列文字列、空の場合は全数値列）
    """
    try:
        if data_id not in data_storage:
            return json.dumps({"error": "指定されたdata_idが見つかりません"}, ensure_ascii=False)
        
        df = data_storage[data_id]["dataframe"]
        
        # カラム指定の処理
        if columns:
            try:
                target_columns = json.loads(columns)
                # 指定されたカラムが存在するかチェック
                missing_cols = [col for col in target_columns if col not in df.columns]
                if missing_cols:
                    return json.dumps({"error": f"存在しないカラム: {missing_cols}"}, ensure_ascii=False)
                df_target = df[target_columns]
            except json.JSONDecodeError:
                return json.dumps({"error": "columns は有効なJSON配列である必要があります"}, ensure_ascii=False)
        else:
            # 数値列のみを対象とする
            df_target = df.select_dtypes(include=[np.number])
        
        if df_target.empty:
            return json.dumps({"error": "分析対象の数値列がありません"}, ensure_ascii=False)
        
        # 基本統計量計算
        basic_stats = df_target.describe()
        
        # 追加統計量
        additional_stats = {}
        for col in df_target.columns:
            col_data = df_target[col].dropna()
            if len(col_data) > 0:
                additional_stats[col] = {
                    "variance": float(col_data.var()),
                    "skewness": float(col_data.skew()),
                    "kurtosis": float(col_data.kurtosis()),
                    "range": float(col_data.max() - col_data.min()),
                    "iqr": float(col_data.quantile(0.75) - col_data.quantile(0.25)),
                    "median_absolute_deviation": float((col_data - col_data.median()).abs().median()),
                    "coefficient_of_variation": float(col_data.std() / col_data.mean()) if col_data.mean() != 0 else None
                }
        
        result = {
            "status": "success",
            "data_id": data_id,
            "analyzed_columns": df_target.columns.tolist(),
            "sample_size": len(df_target),
            "basic_statistics": basic_stats.to_dict(),
            "additional_statistics": additional_stats,
            "summary": {
                "total_columns_analyzed": len(df_target.columns),
                "total_missing_values": int(df_target.isnull().sum().sum()),
                "most_variable_column": max(additional_stats.keys(), key=lambda x: additional_stats[x]["variance"]) if additional_stats else None
            }
        }
        
        return json.dumps(result, indent=2, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({"error": f"基本統計量計算エラー: {str(e)}"}, ensure_ascii=False)

@mcp.tool()
def correlation_analysis(data_id: str, method: str = "pearson", columns: str = "") -> str:
    """相関分析を実行する
    
    Args:
        data_id: データセットID
        method: 相関係数の種類 (pearson, spearman, kendall)
        columns: 分析対象カラム（JSON配列文字列）
    """
    try:
        if data_id not in data_storage:
            return json.dumps({"error": "指定されたdata_idが見つかりません"}, ensure_ascii=False)
        
        df = data_storage[data_id]["dataframe"]
        
        # カラム指定の処理
        if columns:
            try:
                target_columns = json.loads(columns)
                df_target = df[target_columns]
            except json.JSONDecodeError:
                return json.dumps({"error": "columns は有効なJSON配列である必要があります"}, ensure_ascii=False)
        else:
            # 数値列のみを対象
            df_target = df.select_dtypes(include=[np.number])
        
        if df_target.shape[1] < 2:
            return json.dumps({"error": "相関分析には少なくとも2つの数値列が必要です"}, ensure_ascii=False)
        
        # 相関係数計算
        if method not in ["pearson", "spearman", "kendall"]:
            return json.dumps({"error": "method は pearson, spearman, kendall のいずれかである必要があります"}, ensure_ascii=False)
        
        corr_matrix = df_target.corr(method=method)
        
        # 強い相関を持つペアを特定
        corr_pairs = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                col1 = corr_matrix.columns[i]
                col2 = corr_matrix.columns[j]
                corr_value = corr_matrix.iloc[i, j]
                
                if not np.isnan(corr_value):
                    corr_pairs.append({
                        "variable1": col1,
                        "variable2": col2,
                        "correlation": float(corr_value),
                        "strength": "strong" if abs(corr_value) > 0.7 else "moderate" if abs(corr_value) > 0.4 else "weak"
                    })
        
        # 相関の強い順にソート
        corr_pairs.sort(key=lambda x: abs(x["correlation"]), reverse=True)
        
        result = {
            "status": "success",
            "data_id": data_id,
            "method": method,
            "analyzed_columns": df_target.columns.tolist(),
            "correlation_matrix": corr_matrix.to_dict(),
            "correlation_pairs": corr_pairs,
            "summary": {
                "strongest_positive_correlation": max([p for p in corr_pairs if p["correlation"] > 0], key=lambda x: x["correlation"]) if any(p["correlation"] > 0 for p in corr_pairs) else None,
                "strongest_negative_correlation": min([p for p in corr_pairs if p["correlation"] < 0], key=lambda x: x["correlation"]) if any(p["correlation"] < 0 for p in corr_pairs) else None,
                "strong_correlations_count": len([p for p in corr_pairs if abs(p["correlation"]) > 0.7])
            }
        }
        
        return json.dumps(result, indent=2, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({"error": f"相関分析エラー: {str(e)}"}, ensure_ascii=False)

@mcp.tool()
def outlier_detection(data_id: str, method: str = "iqr", columns: str = "") -> str:
    """外れ値検出を実行する
    
    Args:
        data_id: データセットID
        method: 検出手法 (iqr, zscore, modified_zscore)
        columns: 分析対象カラム（JSON配列文字列）
    """
    try:
        if data_id not in data_storage:
            return json.dumps({"error": "指定されたdata_idが見つかりません"}, ensure_ascii=False)
        
        df = data_storage[data_id]["dataframe"]
        
        # カラム指定の処理
        if columns:
            try:
                target_columns = json.loads(columns)
                df_target = df[target_columns]
            except json.JSONDecodeError:
                return json.dumps({"error": "columns は有効なJSON配列である必要があります"}, ensure_ascii=False)
        else:
            df_target = df.select_dtypes(include=[np.number])
        
        if df_target.empty:
            return json.dumps({"error": "分析対象の数値列がありません"}, ensure_ascii=False)
        
        outliers_info = {}
        
        for col in df_target.columns:
            col_data = df_target[col].dropna()
            outliers_idx = []
            
            if method == "iqr":
                Q1 = col_data.quantile(0.25)
                Q3 = col_data.quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                outliers_idx = col_data[(col_data < lower_bound) | (col_data > upper_bound)].index.tolist()
                
            elif method == "zscore":
                z_scores = np.abs(stats.zscore(col_data))
                outliers_idx = col_data[z_scores > 3].index.tolist()
                
            elif method == "modified_zscore":
                median = col_data.median()
                mad = (col_data - median).abs().median()
                modified_z_scores = 0.6745 * (col_data - median) / mad
                outliers_idx = col_data[np.abs(modified_z_scores) > 3.5].index.tolist()
                
            else:
                return json.dumps({"error": "method は iqr, zscore, modified_zscore のいずれかである必要があります"}, ensure_ascii=False)
            
            outliers_info[col] = {
                "outlier_count": len(outliers_idx),
                "outlier_percentage": round(len(outliers_idx) / len(col_data) * 100, 2),
                "outlier_indices": outliers_idx,
                "outlier_values": col_data[outliers_idx].tolist() if outliers_idx else [],
                "column_stats": {
                    "mean": float(col_data.mean()),
                    "median": float(col_data.median()),
                    "std": float(col_data.std()),
                    "min": float(col_data.min()),
                    "max": float(col_data.max())
                }
            }
        
        total_outliers = sum([info["outlier_count"] for info in outliers_info.values()])
        
        result = {
            "status": "success",
            "data_id": data_id,
            "method": method,
            "analyzed_columns": list(outliers_info.keys()),
            "outliers_by_column": outliers_info,
            "summary": {
                "total_outliers_detected": total_outliers,
                "columns_with_outliers": len([col for col, info in outliers_info.items() if info["outlier_count"] > 0]),
                "most_outliers_column": max(outliers_info.keys(), key=lambda x: outliers_info[x]["outlier_count"]) if outliers_info else None
            }
        }
        
        return json.dumps(result, indent=2, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({"error": f"外れ値検出エラー: {str(e)}"}, ensure_ascii=False)

@mcp.tool()
def statistical_test(data_id: str, test_type: str, parameters: str) -> str:
    """統計的検定を実行する
    
    Args:
        data_id: データセットID
        test_type: 検定の種類 (t_test, chi_square, anova)
        parameters: 検定のパラメータ（JSON文字列）
    """
    try:
        if data_id not in data_storage:
            return json.dumps({"error": "指定されたdata_idが見つかりません"}, ensure_ascii=False)
        
        df = data_storage[data_id]["dataframe"]
        
        try:
            params = json.loads(parameters)
        except json.JSONDecodeError:
            return json.dumps({"error": "parameters は有効なJSONである必要があります"}, ensure_ascii=False)
        
        result = {"status": "success", "data_id": data_id, "test_type": test_type}
        
        if test_type == "t_test":
            # 2標本t検定
            if "group_column" not in params or "value_column" not in params:
                return json.dumps({"error": "t_testには group_column と value_column が必要です"}, ensure_ascii=False)
            
            group_col = params["group_column"]
            value_col = params["value_column"]
            
            if group_col not in df.columns or value_col not in df.columns:
                return json.dumps({"error": "指定されたカラムが存在しません"}, ensure_ascii=False)
            
            groups = df[group_col].unique()
            if len(groups) != 2:
                return json.dumps({"error": "t_testには正確に2つのグループが必要です"}, ensure_ascii=False)
            
            group1_data = df[df[group_col] == groups[0]][value_col].dropna()
            group2_data = df[df[group_col] == groups[1]][value_col].dropna()
            
            statistic, p_value = ttest_ind(group1_data, group2_data)
            
            result.update({
                "group_column": group_col,
                "value_column": value_col,
                "groups": groups.tolist(),
                "group1_stats": {"mean": float(group1_data.mean()), "std": float(group1_data.std()), "count": len(group1_data)},
                "group2_stats": {"mean": float(group2_data.mean()), "std": float(group2_data.std()), "count": len(group2_data)},
                "statistic": float(statistic),
                "p_value": float(p_value),
                "significant": p_value < 0.05,
                "interpretation": "有意差あり" if p_value < 0.05 else "有意差なし"
            })
            
        elif test_type == "chi_square":
            # カイ二乗検定
            if "column1" not in params or "column2" not in params:
                return json.dumps({"error": "chi_squareには column1 と column2 が必要です"}, ensure_ascii=False)
            
            col1, col2 = params["column1"], params["column2"]
            
            if col1 not in df.columns or col2 not in df.columns:
                return json.dumps({"error": "指定されたカラムが存在しません"}, ensure_ascii=False)
            
            contingency_table = pd.crosstab(df[col1], df[col2])
            statistic, p_value, dof, expected = chi2_contingency(contingency_table)
            
            result.update({
                "column1": col1,
                "column2": col2,
                "contingency_table": contingency_table.to_dict(),
                "statistic": float(statistic),
                "p_value": float(p_value),
                "degrees_of_freedom": int(dof),
                "significant": p_value < 0.05,
                "interpretation": "独立性の仮説を棄却（関連あり）" if p_value < 0.05 else "独立性の仮説を採択（関連なし）"
            })
            
        elif test_type == "anova":
            # 一元配置分散分析
            if "group_column" not in params or "value_column" not in params:
                return json.dumps({"error": "anovaには group_column と value_column が必要です"}, ensure_ascii=False)
            
            group_col = params["group_column"]
            value_col = params["value_column"]
            
            if group_col not in df.columns or value_col not in df.columns:
                return json.dumps({"error": "指定されたカラムが存在しません"}, ensure_ascii=False)
            
            groups = [group[value_col].dropna() for name, group in df.groupby(group_col)]
            statistic, p_value = f_oneway(*groups)
            
            group_stats = {}
            for name, group in df.groupby(group_col):
                group_data = group[value_col].dropna()
                group_stats[str(name)] = {
                    "mean": float(group_data.mean()),
                    "std": float(group_data.std()),
                    "count": len(group_data)
                }
            
            result.update({
                "group_column": group_col,
                "value_column": value_col,
                "group_stats": group_stats,
                "statistic": float(statistic),
                "p_value": float(p_value),
                "significant": p_value < 0.05,
                "interpretation": "グループ間に有意差あり" if p_value < 0.05 else "グループ間に有意差なし"
            })
            
        else:
            return json.dumps({"error": "test_type は t_test, chi_square, anova のいずれかである必要があります"}, ensure_ascii=False)
        
        return json.dumps(result, indent=2, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({"error": f"統計的検定エラー: {str(e)}"}, ensure_ascii=False)

@mcp.tool()
def distribution_analysis(data_id: str, column: str) -> str:
    """分布分析を実行する
    
    Args:
        data_id: データセットID
        column: 分析対象カラム
    """
    try:
        if data_id not in data_storage:
            return json.dumps({"error": "指定されたdata_idが見つかりません"}, ensure_ascii=False)
        
        df = data_storage[data_id]["dataframe"]
        
        if column not in df.columns:
            return json.dumps({"error": f"カラム '{column}' が存在しません"}, ensure_ascii=False)
        
        col_data = df[column].dropna()
        
        if not np.issubdtype(col_data.dtype, np.number):
            return json.dumps({"error": f"カラム '{column}' は数値型である必要があります"}, ensure_ascii=False)
        
        # 分布の基本統計量
        basic_stats = {
            "count": len(col_data),
            "mean": float(col_data.mean()),
            "median": float(col_data.median()),
            "mode": float(col_data.mode().iloc[0]) if not col_data.mode().empty else None,
            "std": float(col_data.std()),
            "variance": float(col_data.var()),
            "skewness": float(col_data.skew()),
            "kurtosis": float(col_data.kurtosis()),
            "min": float(col_data.min()),
            "max": float(col_data.max()),
            "range": float(col_data.max() - col_data.min())
        }
        
        # パーセンタイル
        percentiles = {}
        for p in [5, 10, 25, 50, 75, 90, 95]:
            percentiles[f"p{p}"] = float(col_data.quantile(p/100))
        
        # 正規性検定（Shapiro-Wilk検定）
        if len(col_data) >= 3 and len(col_data) <= 5000:  # Shapiro-Wilk検定の制限
            shapiro_stat, shapiro_p = stats.shapiro(col_data)
            normality_test = {
                "test": "Shapiro-Wilk",
                "statistic": float(shapiro_stat),
                "p_value": float(shapiro_p),
                "is_normal": shapiro_p > 0.05,
                "interpretation": "正規分布に従う" if shapiro_p > 0.05 else "正規分布に従わない"
            }
        else:
            normality_test = {"test": "N/A", "reason": "サンプルサイズが範囲外（3-5000）"}
        
        # 分布の形状判定
        shape_analysis = {
            "symmetry": "対称" if abs(basic_stats["skewness"]) < 0.5 else ("右偏" if basic_stats["skewness"] > 0 else "左偏"),
            "kurtosis_type": "正規" if abs(basic_stats["kurtosis"]) < 0.5 else ("尖った" if basic_stats["kurtosis"] > 0 else "平たい"),
            "outlier_potential": "高" if abs(basic_stats["kurtosis"]) > 3 else "低"
        }
        
        result = {
            "status": "success",
            "data_id": data_id,
            "column": column,
            "basic_statistics": basic_stats,
            "percentiles": percentiles,
            "normality_test": normality_test,
            "shape_analysis": shape_analysis
        }
        
        return json.dumps(result, indent=2, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({"error": f"分布分析エラー: {str(e)}"}, ensure_ascii=False)


# フェーズ4（修正版）
class DataAnalyzer:
    def __init__(self):
        self.charts = []
        # チャート保存ディレクトリを作成
        self.output_dir = Path("./output")
        self.charts_dir = self.output_dir / "charts"
        self.charts_dir.mkdir(parents=True, exist_ok=True)
        
        # Matplotlib設定（日本語フォント対応）
        plt.rcParams['font.family'] = 'DejaVu Sans'
        plt.rcParams['figure.figsize'] = (10, 6)
        plt.rcParams['savefig.dpi'] = 300
        plt.rcParams['savefig.bbox'] = 'tight'
        
        # Seaborn設定
        sns.set_style("whitegrid")
        
    def _generate_filename(self, chart_type: str, extension: str = "png") -> str:
        """タイムスタンプ付きファイル名を生成"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{chart_type}_{timestamp}.{extension}"
    
    def _save_chart_info(self, chart_type: str, file_path: str, columns_used: list = None) -> str:
        """チャート情報を記録"""
        chart_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        chart_info = {
            'id': chart_id,
            'type': chart_type,
            'path': str(file_path),
            'created_at': datetime.now().isoformat(),
            'columns_used': columns_used or [],
            'file_size': file_path.stat().st_size if file_path.exists() else 0
        }
        self.charts.append(chart_info)
        return chart_id
    
    def _get_base64_image(self, file_path: Path) -> str:
        """画像ファイルをBase64エンコード"""
        try:
            with open(file_path, 'rb') as f:
                img_data = f.read()
            return base64.b64encode(img_data).decode()
        except Exception:
            return ""

# グローバルアナライザーインスタンス
analyzer = DataAnalyzer()

@mcp.tool()
def create_basic_chart(data_id: str, chart_type: str, x_col: str = "", y_col: str = "", 
                      title: str = "", figsize: str = "[10, 6]", style: str = "matplotlib") -> str:
    """基本的なチャートを作成する
    
    Args:
        data_id: データセットID
        chart_type: チャートタイプ (scatter, line, bar, histogram, boxplot, pie)
        x_col: X軸カラム名
        y_col: Y軸カラム名（必要に応じて）
        title: チャートタイトル
        figsize: 図のサイズ [width, height]
        style: 描画スタイル (matplotlib, seaborn, plotly)
    """
    try:
        if data_id not in data_storage:
            return json.dumps({"error": "指定されたdata_idが見つかりません"}, ensure_ascii=False)
        
        df = data_storage[data_id]["dataframe"]
        
        # figsize解析
        try:
            figsize_list = json.loads(figsize)
            if len(figsize_list) != 2:
                figsize_list = [10, 6]
        except:
            figsize_list = [10, 6]
        
        # ファイルパス生成
        filename = analyzer._generate_filename(chart_type)
        file_path = analyzer.charts_dir / filename
        
        # チャートタイトル設定
        if not title:
            title = f"{chart_type.title()} Chart"
        
        # チャート作成
        if style == "plotly":
            fig = None
            
            if chart_type == "scatter":
                if not x_col or not y_col:
                    return json.dumps({"error": "散布図にはx_colとy_colの両方が必要です"}, ensure_ascii=False)
                fig = px.scatter(df, x=x_col, y=y_col, title=title)
                
            elif chart_type == "line":
                if not x_col or not y_col:
                    return json.dumps({"error": "線グラフにはx_colとy_colの両方が必要です"}, ensure_ascii=False)
                fig = px.line(df, x=x_col, y=y_col, title=title)
                
            elif chart_type == "bar":
                if not x_col or not y_col:
                    return json.dumps({"error": "棒グラフにはx_colとy_colの両方が必要です"}, ensure_ascii=False)
                fig = px.bar(df, x=x_col, y=y_col, title=title)
                
            elif chart_type == "histogram":
                if not x_col:
                    return json.dumps({"error": "ヒストグラムにはx_colが必要です"}, ensure_ascii=False)
                fig = px.histogram(df, x=x_col, title=title)
                
            elif chart_type == "boxplot":
                if not y_col:
                    return json.dumps({"error": "箱ひげ図にはy_colが必要です"}, ensure_ascii=False)
                fig = px.box(df, y=y_col, x=x_col if x_col else None, title=title)
                
            elif chart_type == "pie":
                if not x_col:
                    return json.dumps({"error": "円グラフにはx_colが必要です"}, ensure_ascii=False)
                value_counts = df[x_col].value_counts()
                fig = px.pie(values=value_counts.values, names=value_counts.index, title=title)
            
            if fig:
                # HTMLとPNG両方で保存
                html_path = file_path.with_suffix('.html')
                png_path = file_path.with_suffix('.png')
                
                fig.write_html(str(html_path))
                fig.write_image(str(png_path))
                
                # チャート情報記録
                chart_id = analyzer._save_chart_info(chart_type, png_path, [x_col, y_col] if y_col else [x_col])
                
                return json.dumps({
                    "status": "success",
                    "message": f"✅ {chart_type}が作成されました",
                    "chart_id": chart_id,
                    "file_path": str(png_path),
                    "html_path": str(html_path),
                    "chart_type": chart_type,
                    "style": style
                }, ensure_ascii=False)
        
        else:  # matplotlib or seaborn
            plt.figure(figsize=figsize_list)
            
            if chart_type == "scatter":
                if not x_col or not y_col:
                    return json.dumps({"error": "散布図にはx_colとy_colの両方が必要です"}, ensure_ascii=False)
                
                if style == "seaborn":
                    sns.scatterplot(data=df, x=x_col, y=y_col)
                else:
                    plt.scatter(df[x_col], df[y_col], alpha=0.6)
                
                plt.xlabel(x_col)
                plt.ylabel(y_col)
                
            elif chart_type == "line":
                if not x_col or not y_col:
                    return json.dumps({"error": "線グラフにはx_colとy_colの両方が必要です"}, ensure_ascii=False)
                
                if style == "seaborn":
                    sns.lineplot(data=df, x=x_col, y=y_col)
                else:
                    plt.plot(df[x_col], df[y_col])
                
                plt.xlabel(x_col)
                plt.ylabel(y_col)
                
            elif chart_type == "bar":
                if not x_col or not y_col:
                    return json.dumps({"error": "棒グラフにはx_colとy_colの両方が必要です"}, ensure_ascii=False)
                
                if style == "seaborn":
                    sns.barplot(data=df, x=x_col, y=y_col)
                else:
                    plt.bar(df[x_col], df[y_col])
                
                plt.xlabel(x_col)
                plt.ylabel(y_col)
                
            elif chart_type == "histogram":
                if not x_col:
                    return json.dumps({"error": "ヒストグラムにはx_colが必要です"}, ensure_ascii=False)
                
                if style == "seaborn":
                    sns.histplot(data=df, x=x_col, bins=30)
                else:
                    plt.hist(df[x_col].dropna(), bins=30, alpha=0.7)
                
                plt.xlabel(x_col)
                plt.ylabel("Frequency")
                
            elif chart_type == "boxplot":
                if not y_col:
                    return json.dumps({"error": "箱ひげ図にはy_colが必要です"}, ensure_ascii=False)
                
                if style == "seaborn":
                    if x_col:
                        sns.boxplot(data=df, x=x_col, y=y_col)
                    else:
                        sns.boxplot(data=df, y=y_col)
                else:
                    if x_col:
                        df.boxplot(column=y_col, by=x_col)
                    else:
                        df[y_col].plot(kind='box')
                
                if x_col:
                    plt.xlabel(x_col)
                plt.ylabel(y_col)
                
            elif chart_type == "pie":
                if not x_col:
                    return json.dumps({"error": "円グラフにはx_colが必要です"}, ensure_ascii=False)
                
                value_counts = df[x_col].value_counts()
                plt.pie(value_counts.values, labels=value_counts.index, autopct='%1.1f%%')
            
            plt.title(title)
            plt.tight_layout()
            
            # 保存
            plt.savefig(str(file_path), dpi=300, bbox_inches='tight')
            plt.close()  # メモリリーク防止
            
            # チャート情報記録
            chart_id = analyzer._save_chart_info(chart_type, file_path, [x_col, y_col] if y_col else [x_col])
            
            print(f"✅ {chart_type}が作成されました: {file_path}")
            
            return json.dumps({
                "status": "success",
                "message": f"✅ {chart_type}が作成されました",
                "chart_id": chart_id,
                "file_path": str(file_path),
                "chart_type": chart_type,
                "style": style
            }, ensure_ascii=False)
    
    except Exception as e:
        plt.close()  # エラー時もfigureを閉じる
        return json.dumps({"error": f"チャート作成エラー: {str(e)}"}, ensure_ascii=False)

@mcp.tool()
def create_correlation_heatmap(data_id: str, method: str = "pearson", columns: str = "", 
                              title: str = "", figsize: str = "[10, 8]", style: str = "seaborn") -> str:
    """相関ヒートマップを作成する
    
    Args:
        data_id: データセットID
        method: 相関係数の種類 (pearson, spearman, kendall)
        columns: 対象カラム（JSON配列文字列、空の場合は全数値列）
        title: チャートタイトル
        figsize: 図のサイズ [width, height]
        style: 描画スタイル (seaborn, plotly)
    """
    try:
        if data_id not in data_storage:
            return json.dumps({"error": "指定されたdata_idが見つかりません"}, ensure_ascii=False)
        
        df = data_storage[data_id]["dataframe"]
        
        # カラム指定処理
        if columns:
            try:
                target_columns = json.loads(columns)
                df_target = df[target_columns]
            except json.JSONDecodeError:
                return json.dumps({"error": "columns は有効なJSON配列である必要があります"}, ensure_ascii=False)
        else:
            df_target = df.select_dtypes(include=[np.number])
        
        if df_target.shape[1] < 2:
            return json.dumps({"error": "相関ヒートマップには少なくとも2つの数値列が必要です"}, ensure_ascii=False)
        
        # figsize解析
        try:
            figsize_list = json.loads(figsize)
            if len(figsize_list) != 2:
                figsize_list = [10, 8]
        except:
            figsize_list = [10, 8]
        
        # 相関行列計算
        corr_matrix = df_target.corr(method=method)
        
        # ファイルパス生成
        filename = analyzer._generate_filename(f"correlation_heatmap_{method}")
        file_path = analyzer.charts_dir / filename
        
        # タイトル設定
        if not title:
            title = f"Correlation Heatmap ({method.title()})"
        
        if style == "plotly":
            fig = px.imshow(corr_matrix, 
                          text_auto=True, 
                          aspect="auto",
                          color_continuous_scale='RdBu',
                          title=title)
            
            # HTMLとPNG両方で保存
            html_path = file_path.with_suffix('.html')
            png_path = file_path.with_suffix('.png')
            
            fig.write_html(str(html_path))
            fig.write_image(str(png_path))
            
            chart_id = analyzer._save_chart_info("correlation_heatmap", png_path, df_target.columns.tolist())
            
            return json.dumps({
                "status": "success",
                "message": "✅ 相関ヒートマップが作成されました",
                "chart_id": chart_id,
                "file_path": str(png_path),
                "html_path": str(html_path),
                "method": method
            }, ensure_ascii=False)
        
        else:  # seaborn
            plt.figure(figsize=figsize_list)
            
            # ヒートマップ作成
            mask = np.triu(np.ones_like(corr_matrix, dtype=bool))  # 上三角をマスク
            sns.heatmap(corr_matrix, 
                       mask=mask,
                       annot=True, 
                       cmap='RdBu_r', 
                       center=0,
                       square=True,
                       fmt='.2f',
                       cbar_kws={"shrink": .8})
            
            plt.title(title)
            plt.tight_layout()
            
            # 保存
            plt.savefig(str(file_path), dpi=300, bbox_inches='tight')
            plt.close()
            
            chart_id = analyzer._save_chart_info("correlation_heatmap", file_path, df_target.columns.tolist())
            
            print(f"✅ 相関ヒートマップが作成されました: {file_path}")
            
            return json.dumps({
                "status": "success",
                "message": "✅ 相関ヒートマップが作成されました",
                "chart_id": chart_id,
                "file_path": str(file_path),
                "method": method
            }, ensure_ascii=False)
    
    except Exception as e:
        plt.close()
        return json.dumps({"error": f"相関ヒートマップ作成エラー: {str(e)}"}, ensure_ascii=False)

@mcp.tool()
def create_advanced_visualization(data_id: str, viz_type: str, parameters: str = "{}") -> str:
    """高度な可視化を作成する
    
    Args:
        data_id: データセットID
        viz_type: 可視化タイプ (pairplot, distribution_grid, violin_plot, multi_line)
        parameters: 追加パラメータ（JSON文字列）
    """
    try:
        if data_id not in data_storage:
            return json.dumps({"error": "指定されたdata_idが見つかりません"}, ensure_ascii=False)
        
        df = data_storage[data_id]["dataframe"]
        
        # パラメータ解析
        try:
            params = json.loads(parameters)
        except json.JSONDecodeError:
            params = {}
        
        # ファイルパス生成
        filename = analyzer._generate_filename(f"{viz_type}")
        file_path = analyzer.charts_dir / filename
        
        if viz_type == "pairplot":
            # ペアプロット
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            
            # パフォーマンス考慮（列数制限）
            if len(numeric_cols) > 10:
                numeric_cols = numeric_cols[:10]
                print(f"⚠️  パフォーマンス考慮により最初の10列のみ使用: {numeric_cols}")
            
            if len(numeric_cols) < 2:
                return json.dumps({"error": "ペアプロットには少なくとも2つの数値列が必要です"}, ensure_ascii=False)
            
            hue_col = params.get('hue_column')
            if hue_col and hue_col not in df.columns:
                hue_col = None
            
            # ペアプロット作成
            g = sns.pairplot(df[numeric_cols + ([hue_col] if hue_col else [])], 
                           hue=hue_col, 
                           diag_kind='hist')
            
            plt.suptitle("Pair Plot", y=1.02)
            g.savefig(str(file_path), dpi=300, bbox_inches='tight')
            plt.close()
            
            chart_id = analyzer._save_chart_info("pairplot", file_path, numeric_cols)
            
        elif viz_type == "distribution_grid":
            # 分布グリッド
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            
            if len(numeric_cols) < 1:
                return json.dumps({"error": "分布グリッドには少なくとも1つの数値列が必要です"}, ensure_ascii=False)
            
            # グリッドサイズ計算
            n_cols = min(len(numeric_cols), 4)
            n_rows = (len(numeric_cols) + n_cols - 1) // n_cols
            
            fig, axes = plt.subplots(n_rows, n_cols, figsize=(n_cols*4, n_rows*3))
            if n_rows == 1 and n_cols == 1:
                axes = [axes]
            elif n_rows == 1 or n_cols == 1:
                axes = axes.flatten()
            else:
                axes = axes.flatten()
            
            for i, col in enumerate(numeric_cols):
                if i < len(axes):
                    sns.histplot(data=df, x=col, kde=True, ax=axes[i])
                    axes[i].set_title(f'Distribution of {col}')
            
            # 余ったsubplotを非表示
            for i in range(len(numeric_cols), len(axes)):
                axes[i].set_visible(False)
            
            plt.tight_layout()
            plt.savefig(str(file_path), dpi=300, bbox_inches='tight')
            plt.close()
            
            chart_id = analyzer._save_chart_info("distribution_grid", file_path, numeric_cols)
            
        elif viz_type == "violin_plot":
            # バイオリンプロット
            x_col = params.get('x_column')
            y_col = params.get('y_column')
            
            if not x_col or not y_col:
                return json.dumps({"error": "バイオリンプロットにはx_columnとy_columnが必要です"}, ensure_ascii=False)
            
            if x_col not in df.columns or y_col not in df.columns:
                return json.dumps({"error": "指定されたカラムが存在しません"}, ensure_ascii=False)
            
            plt.figure(figsize=(10, 6))
            sns.violinplot(data=df, x=x_col, y=y_col)
            plt.title(f'Violin Plot: {y_col} by {x_col}')
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            plt.savefig(str(file_path), dpi=300, bbox_inches='tight')
            plt.close()
            
            chart_id = analyzer._save_chart_info("violin_plot", file_path, [x_col, y_col])
            
        elif viz_type == "multi_line":
            # 複数系列線グラフ
            x_col = params.get('x_column')
            y_cols = params.get('y_columns', [])
            
            if not x_col or not y_cols:
                return json.dumps({"error": "複数系列線グラフにはx_columnとy_columns（配列）が必要です"}, ensure_ascii=False)
            
            if x_col not in df.columns:
                return json.dumps({"error": f"X軸カラム '{x_col}' が存在しません"}, ensure_ascii=False)
            
            missing_cols = [col for col in y_cols if col not in df.columns]
            if missing_cols:
                return json.dumps({"error": f"存在しないY軸カラム: {missing_cols}"}, ensure_ascii=False)
            
            plt.figure(figsize=(12, 6))
            
            for y_col in y_cols:
                plt.plot(df[x_col], df[y_col], label=y_col, marker='o', markersize=3)
            
            plt.xlabel(x_col)
            plt.ylabel('Values')
            plt.title('Multi-Line Chart')
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            plt.savefig(str(file_path), dpi=300, bbox_inches='tight')
            plt.close()
            
            chart_id = analyzer._save_chart_info("multi_line", file_path, [x_col] + y_cols)
            
        else:
            return json.dumps({"error": f"サポートされていない可視化タイプ: {viz_type}"}, ensure_ascii=False)
        
        print(f"✅ {viz_type}が作成されました: {file_path}")
        
        return json.dumps({
            "status": "success",
            "message": f"✅ {viz_type}が作成されました",
            "chart_id": chart_id,
            "file_path": str(file_path),
            "viz_type": viz_type
        }, ensure_ascii=False)
    
    except Exception as e:
        plt.close()
        return json.dumps({"error": f"高度可視化作成エラー: {str(e)}"}, ensure_ascii=False)

@mcp.tool()
def list_charts() -> str:
    """作成済みチャート一覧を表示"""
    try:
        if not analyzer.charts:
            return json.dumps({
                "status": "success",
                "message": "作成済みチャートはありません",
                "charts": []
            }, ensure_ascii=False)
        
        charts_info = []
        for chart in analyzer.charts:
            # ファイル存在確認
            file_exists = Path(chart['path']).exists()
            file_size = chart.get('file_size', 0)
            
            charts_info.append({
                "chart_id": chart['id'],
                "type": chart['type'],
                "path": chart['path'],
                "created_at": chart['created_at'],
                "columns_used": chart['columns_used'],
                "file_exists": file_exists,
                "file_size_kb": round(file_size / 1024, 2) if file_size > 0 else 0
            })
        
        return json.dumps({
            "status": "success",
            "total_charts": len(charts_info),
            "charts": charts_info
        }, indent=2, ensure_ascii=False)
    
    except Exception as e:
        return json.dumps({"error": f"チャート一覧取得エラー: {str(e)}"}, ensure_ascii=False)

@mcp.tool()
def get_chart_info(chart_id: str) -> str:
    """特定のチャート情報を取得（Base64画像データ付き）"""
    try:
        chart = next((c for c in analyzer.charts if c['id'] == chart_id), None)
        
        if not chart:
            return json.dumps({"error": "指定されたchart_idが見つかりません"}, ensure_ascii=False)
        
        file_path = Path(chart['path'])
        
        if not file_path.exists():
            return json.dumps({"error": "チャートファイルが見つかりません"}, ensure_ascii=False)
        
        # Base64エンコード
        base64_data = analyzer._get_base64_image(file_path)
        
        result = {
            "status": "success",
            "chart_info": {
                "chart_id": chart['id'],
                "type": chart['type'],
                "path": chart['path'],
                "created_at": chart['created_at'],
                "columns_used": chart['columns_used'],
                "file_size_kb": round(file_path.stat().st_size / 1024, 2),
                "base64_image": base64_data[:100] + "..." if len(base64_data) > 100 else base64_data  # 最初の100文字のみ表示
            }
        }
        
        return json.dumps(result, indent=2, ensure_ascii=False)
    
    except Exception as e:
        return json.dumps({"error": f"チャート情報取得エラー: {str(e)}"}, ensure_ascii=False)

# メイン実行部分
if __name__ == "__main__":
    print("🚀 Data Analysis MCP Server を起動中...")
    print("📊 Phase 4: 可視化機能（修正版）が有効です")
    print(f"📁 チャート出力ディレクトリ: {analyzer.charts_dir}")
    
    # 出力ディレクトリの確認
    print(f"✅ 出力ディレクトリが作成されました: {analyzer.charts_dir.exists()}")
    
    uvicorn.run(mcp.app, host="0.0.0.0", port=8000)