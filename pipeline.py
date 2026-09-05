"""
pipeline.py - Pipeline de Machine Learning & Detecção de Anomalias para AIOps
Projeto: AIOps & Cyber-Telemetry Analytics
Autor: Jhonny Brasiliano da Silva
"""

import sqlite3
import pandas as pd
import numpy as np
import json
import os
import joblib

from sklearn.model_selection import train_test_split
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier, IsolationForest
from sklearn.metrics import (
    classification_report, roc_auc_score, average_precision_score,
    confusion_matrix, f1_score, precision_score, recall_score
)

def run_ml_pipeline():
    print("Iniciando Pipeline de Machine Learning AIOps...")
    
    conn = sqlite3.connect("data/telemetry_infrastructure.db")
    df = pd.read_sql("SELECT * FROM telemetry_logs ORDER BY timestamp ASC", conn)
    conn.close()
    
    print(f"Total de registros carregados: {len(df):,}")
    
    # --- Feature Engineering ---
    print("Executando Engenharia de Atributos (Feature Engineering)...")
    
    df['cpu_mem_ratio'] = df['cpu_usage_pct'] / (df['memory_usage_pct'] + 1e-5)
    df['network_pressure'] = df['network_latency_ms'] * (df['packet_loss_pct'] + 0.01)
    df['iops_per_conn'] = df['disk_io_mbs'] / (df['active_connections'] + 1)
    df['error_volume'] = df['error_rate_5xx'] * df['active_connections']
    df['thermal_stress'] = df['temperature_celsius'] / (df['cpu_usage_pct'] + 10.0)
    
    # Médias móveis agrupadas por servidor
    df['cpu_rolling_mean_3'] = df.groupby('server_id')['cpu_usage_pct'].transform(lambda x: x.rolling(3, min_periods=1).mean())
    df['lat_rolling_std_3'] = df.groupby('server_id')['network_latency_ms'].transform(lambda x: x.rolling(3, min_periods=1).std()).fillna(0)
    
    feature_cols = [
        'cpu_usage_pct', 'memory_usage_pct', 'disk_io_mbs', 'network_latency_ms',
        'packet_loss_pct', 'error_rate_5xx', 'active_connections', 'temperature_celsius',
        'cpu_mem_ratio', 'network_pressure', 'iops_per_conn', 'error_volume',
        'thermal_stress', 'cpu_rolling_mean_3', 'lat_rolling_std_3'
    ]
    
    X = df[feature_cols]
    y_failure = df['failure_within_1h']
    y_anomaly = df['is_anomaly']
    
    # --- Modelo 1: Classificação Supervisionada (Predição de Falha em 1h) ---
    print("\n--- Treinando Modelo 1: Predição de Falha em 1 Hora ---")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_failure, test_size=0.20, random_state=42, stratify=y_failure
    )
    
    clf_failure = HistGradientBoostingClassifier(
        max_iter=150,
        learning_rate=0.08,
        max_leaf_nodes=31,
        random_state=42
    )
    clf_failure.fit(X_train, y_train)
    
    y_pred = clf_failure.predict(X_test)
    y_prob = clf_failure.predict_proba(X_test)[:, 1]
    
    roc_auc = roc_auc_score(y_test, y_prob)
    pr_auc = average_precision_score(y_test, y_prob)
    f1 = f1_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec = recall_score(y_test, y_pred)
    cm = confusion_matrix(y_test, y_pred)
    
    print(f"ROC-AUC: {roc_auc:.4f}")
    print(f"PR-AUC:  {pr_auc:.4f}")
    print(f"F1-Score: {f1:.4f}")
    print(f"Precision: {prec:.4f} | Recall: {rec:.4f}")
    print("Matriz de Confusao (TN, FP, FN, TP):")
    print(cm)
    
    # Importância dos Atributos via Random Forest compacta para interpretabilidade
    print("\nCalculando Importância dos Atributos (Feature Importances)...")
    rf_explainer = RandomForestClassifier(n_estimators=60, max_depth=12, random_state=42, n_jobs=-1)
    rf_explainer.fit(X_train, y_train)
    
    importances = rf_explainer.feature_importances_
    feat_imp_list = [
        {"feature": col, "importance": round(float(imp), 4)}
        for col, imp in sorted(zip(feature_cols, importances), key=lambda x: x[1], reverse=True)
    ]
    for item in feat_imp_list[:8]:
        print(f"  {item['feature']:<20}: {item['importance']:.4f}")

    # --- Modelo 2: Detecção Não-supervisionada de Anomalias (Isolation Forest) ---
    print("\n--- Treinando Modelo 2: Detecção Não-Supervisionada (Isolation Forest) ---")
    iso_forest = IsolationForest(
        n_estimators=100,
        contamination=0.02,
        random_state=42,
        n_jobs=-1
    )
    iso_forest.fit(X_train)
    
    # Anomaly score (-1 anomalia, 1 normal)
    iso_preds_raw = iso_forest.predict(X_test)
    iso_anomalies = np.where(iso_preds_raw == -1, 1, 0)
    iso_f1 = f1_score(df.loc[X_test.index, 'is_anomaly'], iso_anomalies)
    print(f"Isolation Forest F1-Score contra Anomalias Reais: {iso_f1:.4f}")
    
    # Salvar modelos serializados
    os.makedirs("models", exist_ok=True)
    joblib.dump(clf_failure, "models/failure_predictor_hgb.joblib")
    joblib.dump(iso_forest, "models/anomaly_detector_iforest.joblib")
    print("Modelos serializados salvos em models/")
    
    # Exportar métricas em JSON
    metrics = {
        "dataset_total_samples": len(df),
        "total_servers": int(df['server_id'].nunique()),
        "anomaly_rate_pct": round(float(df['is_anomaly'].mean() * 100), 2),
        "supervised_model": {
            "name": "HistGradientBoosting Classifier",
            "target": "failure_within_1h",
            "roc_auc": round(float(roc_auc), 4),
            "pr_auc": round(float(pr_auc), 4),
            "f1_score": round(float(f1), 4),
            "precision": round(float(prec), 4),
            "recall": round(float(rec), 4),
            "confusion_matrix": {
                "true_negative": int(cm[0][0]),
                "false_positive": int(cm[0][1]),
                "false_negative": int(cm[1][0]),
                "true_positive": int(cm[1][1])
            }
        },
        "unsupervised_model": {
            "name": "Isolation Forest",
            "contamination": 0.02,
            "detected_anomaly_count_test": int(sum(iso_anomalies)),
            "f1_score": round(float(iso_f1), 4)
        },
        "feature_importances": feat_imp_list
    }
    
    with open("models/metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
        
    # Extrair amostra de telemetria rica com janelas anômalas para visualização no dashboard
    print("Extraindo amostra representativa para o Dashboard Interativo...")
    # Pegar 1 servidor em particular durante uma anomalia (ex: srv-web-01 ou srv-api-01)
    sample_df = df[df['server_id'] == 'srv-api-01'].tail(150)
    sample_data = sample_df[[
        'timestamp', 'cpu_usage_pct', 'memory_usage_pct', 'disk_io_mbs',
        'network_latency_ms', 'packet_loss_pct', 'error_rate_5xx',
        'active_connections', 'temperature_celsius', 'incident_type', 'is_anomaly'
    ]].to_dict(orient="records")
    
    with open("models/telemetry_sample.json", "w", encoding="utf-8") as f:
        json.dump(sample_data, f, indent=2)
        
    print("Pipeline de Machine Learning concluído com êxito!")

if __name__ == "__main__":
    run_ml_pipeline()
