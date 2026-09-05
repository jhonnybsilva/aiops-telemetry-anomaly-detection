// app.js - Logica Interativa e Visualizacao de Dados AIOps
// Autor: Jhonny Brasiliano da Silva

document.addEventListener("DOMContentLoaded", async () => {
  let telemetryData = [];
  
  try {
    const response = await fetch("models/telemetry_sample.json");
    if (response.ok) {
      telemetryData = await response.json();
    }
  } catch (e) {
    console.warn("Utilizando dados de telemetria pré-carregados para renderização local.", e);
  }

  // Fallback caso fetch local falhe em arquivo estático direto
  if (!telemetryData || telemetryData.length === 0) {
    telemetryData = generateFallbackTelemetry();
  }

  initTelemetryChart(telemetryData);
  initIncidentPieChart();
  initFeatureImportanceChart();
  initSimulator();
});

function generateFallbackTelemetry() {
  const data = [];
  const now = new Date();
  for (let i = 60; i >= 0; i--) {
    const time = new Date(now.getTime() - i * 8 * 60000);
    const isAnomaly = i >= 15 && i <= 22;
    data.push({
      timestamp: time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      cpu_usage_pct: isAnomaly ? 88.5 + Math.random() * 8 : 32.0 + Math.random() * 10,
      memory_usage_pct: isAnomaly ? 92.0 + Math.random() * 5 : 48.0 + Math.random() * 6,
      network_latency_ms: isAnomaly ? 240 + Math.random() * 120 : 22 + Math.random() * 8,
      is_anomaly: isAnomaly ? 1 : 0
    });
  }
  return data;
}

// 1. Grafico de Telemetria de Séries Temporais
function initTelemetryChart(data) {
  const ctx = document.getElementById("telemetryChart").getContext("2d");
  
  // Pegar ultimos 50 pontos para clareza
  const displayData = data.slice(-50);
  const labels = displayData.map(d => d.timestamp.includes(" ") ? d.timestamp.split(" ")[1] : d.timestamp);
  const cpuData = displayData.map(d => d.cpu_usage_pct);
  const memData = displayData.map(d => d.memory_usage_pct);
  const latData = displayData.map(d => d.network_latency_ms);
  
  // Cores dos pontos: destaca anomalias em vermelho/rosa brilhante
  const pointColors = displayData.map(d => d.is_anomaly === 1 ? "#f43f5e" : "#3b82f6");
  const pointRadius = displayData.map(d => d.is_anomaly === 1 ? 6 : 2);

  new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "CPU Usage (%)",
          data: cpuData,
          borderColor: "#06b6d4",
          backgroundColor: "rgba(6, 182, 212, 0.1)",
          borderWidth: 2,
          pointBackgroundColor: pointColors,
          pointRadius: pointRadius,
          tension: 0.35,
          yAxisID: "y"
        },
        {
          label: "Memory Usage (%)",
          data: memData,
          borderColor: "#8b5cf6",
          backgroundColor: "transparent",
          borderWidth: 2,
          pointRadius: 1,
          tension: 0.35,
          yAxisID: "y"
        },
        {
          label: "Latency (ms)",
          data: latData,
          borderColor: "#f59e0b",
          backgroundColor: "transparent",
          borderWidth: 2,
          borderDash: [5, 5],
          pointRadius: 1,
          tension: 0.35,
          yAxisID: "y1"
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: "index",
        intersect: false
      },
      plugins: {
        legend: {
          labels: { color: "#9ca3af", font: { family: "Inter" } }
        },
        tooltip: {
          backgroundColor: "#1f2937",
          titleColor: "#f9fafb",
          bodyColor: "#d1d5db",
          borderColor: "#374151",
          borderWidth: 1
        }
      },
      scales: {
        x: {
          grid: { color: "rgba(55, 65, 81, 0.4)" },
          ticks: { color: "#9ca3af", maxTicksLimit: 12 }
        },
        y: {
          type: "linear",
          display: true,
          position: "left",
          min: 0,
          max: 100,
          grid: { color: "rgba(55, 65, 81, 0.4)" },
          ticks: { color: "#9ca3af", callback: value => value + "%" },
          title: { display: true, text: "Uso de Recursos (%)", color: "#9ca3af" }
        },
        y1: {
          type: "linear",
          display: true,
          position: "right",
          min: 0,
          grid: { drawOnChartArea: false },
          ticks: { color: "#f59e0b", callback: value => value + "ms" },
          title: { display: true, text: "Latência (ms)", color: "#f59e0b" }
        }
      }
    }
  });
}

// 2. Gráfico de Rosca: Causas Raízes de Incidentes
function initIncidentPieChart() {
  const ctx = document.getElementById("incidentPieChart").getContext("2d");
  new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: ["DDoS Attack", "Disk Saturation", "Memory Leak", "Thermal Throttling"],
      datasets: [{
        data: [13, 13, 12, 5],
        backgroundColor: ["#f43f5e", "#f59e0b", "#8b5cf6", "#06b6d4"],
        borderColor: "#111827",
        borderWidth: 3,
        hoverOffset: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "bottom",
          labels: { color: "#9ca3af", boxWidth: 14, padding: 16 }
        }
      },
      cutout: "70%"
    }
  });
}

// 3. Gráfico de Barras: Importância dos Atributos (Risk Drivers)
function initFeatureImportanceChart() {
  const ctx = document.getElementById("featureImportanceChart").getContext("2d");
  new Chart(ctx, {
    type: "bar",
    data: {
      labels: [
        "Network Latency (ms)",
        "Latency Rolling Std",
        "Thermal Stress Index",
        "Network Pressure",
        "Temperature (°C)",
        "CPU Rolling Mean",
        "Memory Usage (%)"
      ],
      datasets: [{
        label: "Peso Preditivo no Modelo",
        data: [0.2477, 0.1730, 0.1072, 0.0886, 0.0652, 0.0625, 0.0498],
        backgroundColor: [
          "rgba(6, 182, 212, 0.85)",
          "rgba(59, 130, 246, 0.85)",
          "rgba(139, 92, 246, 0.85)",
          "rgba(245, 158, 11, 0.85)",
          "rgba(244, 63, 94, 0.85)",
          "rgba(16, 185, 129, 0.85)",
          "rgba(107, 114, 128, 0.85)"
        ],
        borderRadius: 6,
        borderSkipped: false
      }]
    },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (item) => ` Importância: ${(item.raw * 100).toFixed(1)}%`
          }
        }
      },
      scales: {
        x: {
          grid: { color: "rgba(55, 65, 81, 0.4)" },
          ticks: { color: "#9ca3af", callback: val => (val * 100) + "%" }
        },
        y: {
          grid: { display: false },
          ticks: { color: "#e5e7eb", font: { size: 12 } }
        }
      }
    }
  });
}

// 4. Simulador Interativo de Risco de Falha
function initSimulator() {
  const sliders = {
    cpu: document.getElementById("sliderCpu"),
    mem: document.getElementById("sliderMem"),
    lat: document.getElementById("sliderLat"),
    loss: document.getElementById("sliderLoss"),
    err: document.getElementById("sliderErr"),
    temp: document.getElementById("sliderTemp")
  };

  const values = {
    cpu: document.getElementById("valCpu"),
    mem: document.getElementById("valMem"),
    lat: document.getElementById("valLat"),
    loss: document.getElementById("valLoss"),
    err: document.getElementById("valErr"),
    temp: document.getElementById("valTemp")
  };

  const riskPctEl = document.getElementById("riskPercentage");
  const riskBadgeEl = document.getElementById("riskBadge");
  const diagTextEl = document.getElementById("diagnosisText");
  const playbookTextEl = document.getElementById("playbookText");

  function updateSimulation() {
    const cpu = parseFloat(sliders.cpu.value);
    const mem = parseFloat(sliders.mem.value);
    const lat = parseFloat(sliders.lat.value);
    const loss = parseFloat(sliders.loss.value);
    const err = parseFloat(sliders.err.value);
    const temp = parseFloat(sliders.temp.value);

    // Atualiza rótulos
    values.cpu.textContent = `${cpu}%`;
    values.mem.textContent = `${mem}%`;
    values.lat.textContent = `${lat} ms`;
    values.loss.textContent = `${loss.toFixed(1)}%`;
    values.err.textContent = `${err.toFixed(1)}%`;
    values.temp.textContent = `${temp}°C`;

    // Função de inferência simulada (baseada nos pesos do modelo treinado)
    let score = 0;
    
    // Contribuição da latência e perda de pacotes (peso mais alto)
    score += (lat / 500) * 35;
    score += (loss / 30) * 20;
    
    // Contribuição térmica
    if (temp > 75) {
      score += ((temp - 75) / 25) * 22;
    }
    
    // Contribuição de memória e swap
    if (mem > 80) {
      score += ((mem - 80) / 20) * 20;
    }
    
    // Contribuição de erros HTTP e CPU
    score += (err / 50) * 15;
    if (cpu > 85) {
      score += ((cpu - 85) / 15) * 12;
    }

    // Normalização 0 - 100%
    const riskPct = Math.min(99, Math.max(1, Math.round(score)));
    riskPctEl.textContent = `${riskPct}%`;

    if (riskPct < 35) {
      riskPctEl.style.color = "#10b981";
      riskBadgeEl.textContent = "Status Normal • Seguro";
      riskBadgeEl.style.backgroundColor = "rgba(16, 185, 129, 0.15)";
      riskBadgeEl.style.color = "#10b981";
      riskBadgeEl.style.borderColor = "rgba(16, 185, 129, 0.4)";
      diagTextEl.textContent = "Infraestrutura com carga controlada e métricas nominais dentro da margem de SLA.";
      playbookTextEl.textContent = "📋 Playbook Recomendado: Monitoramento passivo e rotinas de backup automáticas.";
    } else if (riskPct < 70) {
      riskPctEl.style.color = "#f59e0b";
      riskBadgeEl.textContent = "Atenção • Degradação Parcial";
      riskBadgeEl.style.backgroundColor = "rgba(245, 158, 11, 0.15)";
      riskBadgeEl.style.color = "#f59e0b";
      riskBadgeEl.style.borderColor = "rgba(245, 158, 11, 0.4)";
      
      let reason = "Degradação observada em tempos de resposta.";
      if (mem > 80) reason = "Alocação excessiva de memória RAM detectada (possível saturação de buffers).";
      else if (loss > 5) reason = "Perda de pacotes elevada indicando jitter ou contenção de rede.";
      else if (temp > 80) reason = "Temperatura do chassi elevada com risco de thermal throttling.";
      
      diagTextEl.textContent = reason;
      playbookTextEl.textContent = "📋 Playbook Recomendado: Ativar auto-scaling horizontal de instâncias e alertar plantonista NOC.";
    } else {
      riskPctEl.style.color = "#f43f5e";
      riskBadgeEl.textContent = "Crítico • Risco Iminente de Pane";
      riskBadgeEl.style.backgroundColor = "rgba(244, 63, 94, 0.15)";
      riskBadgeEl.style.color = "#f43f5e";
      riskBadgeEl.style.borderColor = "rgba(244, 63, 94, 0.4)";
      
      let criticalReason = "Anomalia severa multidimensional com probabilidade crítica de colapso de serviço.";
      if (err > 20 && loss > 10) criticalReason = "Assinatura de ataque volumétrico DDoS ou falha catastrófica de gateway.";
      else if (mem > 90) criticalReason = "Vazamento crítico de memória (Memory Leak) com risco de término abrupto por OOM Killer.";
      else if (temp > 85) criticalReason = "Alerta térmico crítico: colapso no sistema de arrefecimento.";

      diagTextEl.textContent = criticalReason;
      playbookTextEl.textContent = "🚨 AÇÃO IMEDIATA: Drenar conexões para nós réplicas, isolar tráfego malicioso e reiniciar container afetado.";
    }
  }

  // Registra eventos em todos os sliders
  Object.values(sliders).forEach(slider => {
    slider.addEventListener("input", updateSimulation);
  });

  updateSimulation();
}
