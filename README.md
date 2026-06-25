# Metallurgy AI 🌍
### AI-Based Environmental Sustainability Prediction at Metallurgical Sites

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.x-lightgrey.svg)](https://flask.palletsprojects.com)
[![XGBoost](https://img.shields.io/badge/XGBoost-ML_Engine-orange.svg)](https://xgboost.readthedocs.io)
[![SHAP](https://img.shields.io/badge/SHAP-Explainability-green.svg)](https://shap.readthedocs.io)
[![Deployed on Render](https://img.shields.io/badge/Deployed-Render.com-purple.svg)](https://render.com)

> Transforming environmental monitoring from a **reactive** process into a **proactive, AI-driven** decision-support tool for mining and metallurgical operations.

---

## Problem

India's metallurgy and mining sector contributes significantly to environmental degradation. Existing Life Cycle Assessment (LCA) tools are expensive, static, non-explainable, and disconnected from geospatial context — making proactive environmental decision-making nearly impossible for small and mid-size operations.

## Solution

Metallurgy AI is an open-source, web-based LCA platform combining:

| Component | Technology | Purpose |
|---|---|---|
| Dynamic LCA Engine | Rule-based AI | Real-time environmental impact scoring per material type |
| ML Classifier | XGBoost | Classifies sites into Red / Orange / Green sustainability zones |
| Explainability (XAI) | SHAP | Identifies which inputs (energy, water, purity) drive each classification |
| Geospatial Mapping | Google Maps API | Visualizes pollution hotspots and impact radius |
| Web Interface | Flask + HTML/CSS/JS | Real-time dashboard for site audits |

---

## ML Model Performance

Trained on 94 real-world global mining facility records.

| Metric | Value |
|---|---|
| Hold-out Test Accuracy | ~88% |
| Cross-Validation Accuracy (5-fold) | ~85% ± 4% |
| Classes | Red (Critical) / Orange (Warning) / Green (Sustainable) |

SHAP explainability plots are saved automatically to `static/ml_plots/` on startup.

---

## Project Structure

```
METALLURGY_AI/
├── app.py                      # Flask API — main entry point (v2.0)
├── requirements.txt            # Python dependencies
├── process_data.py             # Data pipeline
├── Generate_graphs.py          # Performance visualizations
│
├── services/
│   ├── lca_engine.py           # Rule-based LCA scoring (original)
│   ├── ml_engine.py            # XGBoost + SHAP layer (v2.0 addition)
│   └── maps_service.py         # Google Maps coordinate resolution
│
├── data/
│   ├── master_mining_data.csv  # Facility coordinates dataset
│   └── test_cases.csv          # 94 labelled mining site records
│
├── static/
│   └── ml_plots/               # SHAP + confusion matrix plots (auto-generated)
│
└── templates/
    └── index.html              # Web dashboard
```

---

## Getting Started

### Prerequisites
```
Python 3.10+
Google Maps API Key
```

### Installation
```bash
git clone https://github.com/charanrajsandacommits/METALLURGY_AI.git
cd METALLURGY_AI
pip install -r requirements.txt
```

### Environment Variables
Create a `.env` file in the root:
```
GOOGLE_MAPS_API_KEY=your_key_here
```
Or set it directly in your Render dashboard under Environment Variables.

### Run
```bash
python app.py
```
Visit `http://localhost:5000`

The ML model trains automatically at startup from `data/test_cases.csv` — no manual steps needed.

---

## Versions

| Version | Branch | Description |
|---|---|---|
| v1.0.0 | `main` | Rule-based LCA engine + geospatial mapping (college submission) |
| v2.0.0 | `v2-ml-upgrade` | + XGBoost ML classifier + SHAP explainability |

---

## Team

| Name | Role |
|---|---|
| **Charan raj Sanda** | Team Lead — Architecture, LCA engine, ML integration |
| Team Member 2 | Frontend, data pipeline |
| Team Member 3 | Data collection, testing, documentation |

**Institution:** CMR Technical Campus, Hyderabad | CSE (AI & ML) | 2023–2027

**Aligned with:** Smart India Hackathon 2025 — Problem Statement SIH25069 (Ministry of Mines, GoI)

---

## Research Paper

> Under preparation for submission to **IRJET / IEEE Conference on AI & Sustainability (2026)**
> *"An Intelligent Dynamic Life Cycle Assessment Platform with Explainable AI for Sustainable Metallurgical Operations"*
