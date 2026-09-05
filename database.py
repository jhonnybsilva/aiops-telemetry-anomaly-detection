"""
database.py - Modelagem e Estruturacao do Banco Relacional SQLite
Projeto: AIOps & Cyber-Telemetry Analytics
Autor: Jhonny Brasiliano da Silva
"""

import sqlite3
import pandas as pd
import os

DB_PATH = "data/telemetry_infrastructure.db"

def build_database():
    print(f"Criando e populando banco de dados relacional em {DB_PATH}...")
    
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE servers (
        server_id TEXT PRIMARY KEY,
        role TEXT NOT NULL,
        region TEXT NOT NULL,
        specs TEXT NOT NULL
    );
    """)
    
    cursor.execute("""
    CREATE TABLE telemetry_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME NOT NULL,
        server_id TEXT NOT NULL,
        role TEXT NOT NULL,
        region TEXT NOT NULL,
        cpu_usage_pct REAL NOT NULL,
        memory_usage_pct REAL NOT NULL,
        disk_io_mbs REAL NOT NULL,
        network_latency_ms REAL NOT NULL,
        packet_loss_pct REAL NOT NULL,
        error_rate_5xx REAL NOT NULL,
        active_connections INTEGER NOT NULL,
        temperature_celsius REAL NOT NULL,
        incident_type TEXT NOT NULL,
        is_anomaly INTEGER NOT NULL,
        failure_within_1h INTEGER NOT NULL,
        FOREIGN KEY (server_id) REFERENCES servers(server_id)
    );
    """)
    
    cursor.execute("""
    CREATE TABLE incidents (
        incident_id TEXT PRIMARY KEY,
        server_id TEXT NOT NULL,
        start_time DATETIME NOT NULL,
        end_time DATETIME NOT NULL,
        incident_type TEXT NOT NULL,
        severity TEXT NOT NULL,
        mttr_minutes INTEGER NOT NULL,
        root_cause TEXT NOT NULL,
        FOREIGN KEY (server_id) REFERENCES servers(server_id)
    );
    """)
    
    cursor.execute("CREATE INDEX idx_telemetry_timestamp ON telemetry_logs(timestamp);")
    cursor.execute("CREATE INDEX idx_telemetry_server ON telemetry_logs(server_id);")
    cursor.execute("CREATE INDEX idx_telemetry_anomaly ON telemetry_logs(is_anomaly);")
    cursor.execute("CREATE INDEX idx_incidents_server ON incidents(server_id);")
    
    conn.commit()
    
    df_servers = pd.read_csv("data/servers_metadata.csv", keep_default_na=False)
    df_incidents = pd.read_csv("data/incidents_history.csv", keep_default_na=False)
    df_telemetry = pd.read_csv("data/telemetry_data.csv", keep_default_na=False)
    
    df_servers.to_sql("servers", conn, if_exists="append", index=False)
    df_incidents.to_sql("incidents", conn, if_exists="append", index=False)
    df_telemetry.to_sql("telemetry_logs", conn, if_exists="append", index=False)
    
    conn.commit()
    print("Tabelas criadas e 63.000 dados inseridos com sucesso!")
    
    print("\n--- [CONSULTA SQL 1: MTTR Medio e Impacto por Tipo de Incidente] ---")
    query_mttr = """
    SELECT 
        incident_type AS Tipo_Incidente,
        COUNT(*) AS Ocorrencias,
        ROUND(AVG(mttr_minutes), 1) AS MTTR_Medio_Minutos,
        MIN(mttr_minutes) AS MTTR_Min,
        MAX(mttr_minutes) AS MTTR_Max
    FROM incidents
    GROUP BY incident_type
    ORDER BY Ocorrencias DESC;
    """
    print(pd.read_sql(query_mttr, conn).to_string(index=False))
    
    print("\n--- [CONSULTA SQL 2: Comparativo Operacional: Normal vs Sob Anomalia] ---")
    query_comp = """
    SELECT 
        CASE WHEN is_anomaly = 1 THEN 'Sob Anomalia' ELSE 'Operacao Normal' END AS Estado,
        COUNT(*) AS Total_Amostras,
        ROUND(AVG(cpu_usage_pct), 2) AS Media_CPU_Pct,
        ROUND(AVG(memory_usage_pct), 2) AS Media_RAM_Pct,
        ROUND(AVG(network_latency_ms), 2) AS Media_Latencia_ms,
        ROUND(AVG(packet_loss_pct), 3) AS Media_Perda_Pacotes_Pct,
        ROUND(AVG(error_rate_5xx), 3) AS Media_Erros_5xx_Pct
    FROM telemetry_logs
    GROUP BY is_anomaly;
    """
    print(pd.read_sql(query_comp, conn).to_string(index=False))
    
    conn.close()

if __name__ == "__main__":
    build_database()
