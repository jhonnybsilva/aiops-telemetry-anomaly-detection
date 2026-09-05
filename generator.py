"""
generator.py - Gerador de Telemetria Sintetica de Alta Fidelidade para AIOps
Projeto: AIOps & Cyber-Telemetry Analytics
Autor: Jhonny Brasiliano da Silva
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random
import os

np.random.seed(42)
random.seed(42)

def generate_telemetry_data():
    print("Iniciando geracao de dados de telemetria de infraestrutura...")
    
    servers = [
        {"server_id": "srv-web-01", "role": "Web Server", "region": "sa-east-1", "specs": "16 vCPU, 32GB RAM"},
        {"server_id": "srv-web-02", "role": "Web Server", "region": "sa-east-1", "specs": "16 vCPU, 32GB RAM"},
        {"server_id": "srv-web-03", "role": "Web Server", "region": "us-east-1", "specs": "16 vCPU, 32GB RAM"},
        {"server_id": "srv-api-01", "role": "API Gateway", "region": "sa-east-1", "specs": "32 vCPU, 64GB RAM"},
        {"server_id": "srv-api-02", "role": "API Gateway", "region": "sa-east-1", "specs": "32 vCPU, 64GB RAM"},
        {"server_id": "srv-api-03", "role": "API Gateway", "region": "us-east-1", "specs": "32 vCPU, 64GB RAM"},
        {"server_id": "srv-db-primary", "role": "Database Primary", "region": "sa-east-1", "specs": "64 vCPU, 256GB RAM"},
        {"server_id": "srv-db-replica", "role": "Database Replica", "region": "sa-east-1", "specs": "64 vCPU, 256GB RAM"},
        {"server_id": "srv-edge-gw-01", "role": "Edge Gateway", "region": "sa-east-1", "specs": "16 vCPU, 32GB RAM"},
        {"server_id": "srv-cache-01", "role": "In-Memory Cache", "region": "sa-east-1", "specs": "32 vCPU, 128GB RAM"}
    ]
    
    start_date = datetime(2026, 8, 1, 0, 0, 0)
    intervals = 6300
    timestamps = [start_date + timedelta(minutes=8 * i) for i in range(intervals)]
    
    all_records = []
    incidents_list = []
    incident_id_counter = 1001

    for srv in servers:
        sid = srv["server_id"]
        role = srv["role"]
        
        if "Database" in role:
            base_cpu, base_mem, base_io, base_lat = 40.0, 65.0, 90.0, 22.0
        elif "API" in role:
            base_cpu, base_mem, base_io, base_lat = 35.0, 45.0, 30.0, 18.0
        elif "Web" in role:
            base_cpu, base_mem, base_io, base_lat = 30.0, 40.0, 20.0, 25.0
        elif "Cache" in role:
            base_cpu, base_mem, base_io, base_lat = 25.0, 70.0, 15.0, 6.0
        else:
            base_cpu, base_mem, base_io, base_lat = 32.0, 38.0, 25.0, 12.0
            
        num_anomalies = random.randint(3, 5)
        anomaly_windows = []
        possible_types = ["DDoS_Attack", "Memory_Leak", "Disk_Saturation", "Thermal_Throttling"]
        
        for _ in range(num_anomalies):
            start_idx = random.randint(200, intervals - 200)
            duration = random.randint(12, 30)
            atype = random.choice(possible_types)
            anomaly_windows.append({
                "start": start_idx,
                "end": start_idx + duration,
                "type": atype
            })
            
            incidents_list.append({
                "incident_id": f"INC-{incident_id_counter}",
                "server_id": sid,
                "start_time": timestamps[start_idx].isoformat(),
                "end_time": timestamps[min(start_idx + duration, intervals - 1)].isoformat(),
                "incident_type": atype,
                "severity": "CRITICAL" if atype in ["DDoS_Attack", "Disk_Saturation"] else "HIGH",
                "mttr_minutes": duration * 8,
                "root_cause": (
                    "Inundacao massiva de requisicoes SYN / HTTP Flood" if atype == "DDoS_Attack" else
                    "Vazamento progressivo de ponteiros e memoria nao liberada na aplicacao" if atype == "Memory_Leak" else
                    "Saturacao extrema de leitura/escrita e filas de buffer bloqueadas" if atype == "Disk_Saturation" else
                    "Falha no subsistema de refrigeracao e acionamento de throttling termico"
                )
            })
            incident_id_counter += 1
            
        for i, ts in enumerate(timestamps):
            hour = ts.hour + ts.minute / 60.0
            day_of_week = ts.weekday()
            
            daily_factor = 0.5 * np.sin((hour - 6) / 24.0 * 2 * np.pi) + 0.5
            weekend_factor = 0.65 if day_of_week >= 5 else 1.0
            load_factor = (0.7 + 0.6 * daily_factor) * weekend_factor
            
            cpu = base_cpu * load_factor + np.random.normal(0, 3.5)
            mem = base_mem + np.random.normal(0, 1.8) + (load_factor * 4.0)
            io = base_io * load_factor + np.random.normal(0, 5.0)
            lat = base_lat + (load_factor * 6.0) + np.random.normal(0, 2.0)
            packet_loss = max(0.0, np.random.exponential(0.04))
            err_5xx = max(0.0, np.random.exponential(0.02))
            active_conn = int(max(20, (180 * load_factor) + np.random.normal(0, 25)))
            temp = 44.0 + (cpu * 0.28) + np.random.normal(0, 1.2)
            
            incident_type = "None"
            is_anomaly = 0
            
            for win in anomaly_windows:
                if win["start"] <= i <= win["end"]:
                    is_anomaly = 1
                    incident_type = win["type"]
                    progress = (i - win["start"]) / max(1, (win["end"] - win["start"]))
                    
                    if win["type"] == "DDoS_Attack":
                        active_conn = int(active_conn * (4.5 + 4.0 * np.sin(progress * np.pi)))
                        packet_loss = min(35.0, packet_loss + np.random.uniform(8.0, 22.0))
                        err_5xx = min(45.0, err_5xx + np.random.uniform(12.0, 38.0))
                        lat = lat + np.random.uniform(180.0, 420.0)
                        cpu = min(99.5, cpu + 35.0)
                    elif win["type"] == "Memory_Leak":
                        mem = min(99.2, mem + (progress * 42.0) + np.random.normal(0, 1.0))
                        if mem > 88.0:
                            lat += (mem - 85.0) * 8.0
                            io += (mem - 85.0) * 6.0
                    elif win["type"] == "Disk_Saturation":
                        io = max(io, 380.0 + np.random.normal(50, 20))
                        lat += np.random.uniform(120.0, 280.0)
                        cpu = min(98.0, cpu + 25.0)
                    elif win["type"] == "Thermal_Throttling":
                        temp = min(96.0, 78.0 + (progress * 15.0) + np.random.normal(0, 2.0))
                        if temp > 82.0:
                            cpu = max(15.0, cpu - 20.0)
                            lat += np.random.uniform(80.0, 210.0)
                    break
                    
            failure_within_1h = 0
            for win in anomaly_windows:
                if win["start"] <= (i + 7) and i < win["end"]:
                    failure_within_1h = 1
                    break
                    
            cpu = float(np.clip(cpu, 5.0, 100.0))
            mem = float(np.clip(mem, 10.0, 100.0))
            io = float(np.clip(io, 2.0, 800.0))
            lat = float(np.clip(lat, 2.0, 1000.0))
            packet_loss = float(np.clip(packet_loss, 0.0, 50.0))
            err_5xx = float(np.clip(err_5xx, 0.0, 60.0))
            temp = float(np.clip(temp, 35.0, 105.0))
            
            all_records.append({
                "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
                "server_id": sid,
                "role": role,
                "region": srv["region"],
                "cpu_usage_pct": round(cpu, 2),
                "memory_usage_pct": round(mem, 2),
                "disk_io_mbs": round(io, 2),
                "network_latency_ms": round(lat, 2),
                "packet_loss_pct": round(packet_loss, 3),
                "error_rate_5xx": round(err_5xx, 3),
                "active_connections": active_conn,
                "temperature_celsius": round(temp, 1),
                "incident_type": incident_type,
                "is_anomaly": is_anomaly,
                "failure_within_1h": failure_within_1h
            })
            
    df_telemetry = pd.DataFrame(all_records)
    df_incidents = pd.DataFrame(incidents_list)
    df_servers = pd.DataFrame(servers)
    
    os.makedirs("data", exist_ok=True)
    df_telemetry.to_csv("data/telemetry_data.csv", index=False)
    df_incidents.to_csv("data/incidents_history.csv", index=False)
    df_servers.to_csv("data/servers_metadata.csv", index=False)
    
    print(f"Sucesso! Registros gerados: {len(df_telemetry):,}")
    print(f"Incidentes gerados: {len(df_incidents)}")
    print(df_telemetry['incident_type'].value_counts())

if __name__ == "__main__":
    generate_telemetry_data()
