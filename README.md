TRACK_ID=PS03

# ShelfIQ - Retail Sales & Inventory Copilot

> **Smarter shelves. Better decisions.**

ShelfIQ is a decision-support application for small retail operations managing multiple stores. It helps store managers answer key operational questions regarding inventory health, stock-out risks, slow-moving items, overstocked inventory, and sales anomalies using deterministic analytics powered by real retail data and grounded AI explanations.

---

## 📌 Problem Statement
Retail managers often struggle to synthesize daily sales and stock data across multiple store locations to identify:
- What is running out or at immediate stock-out risk?
- What products are slow-moving or overstocked?
- Which items have experienced unusual sales spikes or drops?
- What actionable steps should be taken today?

ShelfIQ provides actionable answers backed by transparent, deterministic data calculations and structured evidence.

---

## 🏗️ Project Architecture
```
retailiq/
│
├── app.py                  # FastAPI web server entrypoint
├── requirements.txt        # Core project dependencies
├── README.md               # Project documentation & Track ID
├── .gitignore              # Ignored files & environment protection
│
├── src/                    # Core Python modules
│   ├── __init__.py         # Package initialization
│   ├── analytics.py        # Deterministic calculations (velocity, days remaining, trends)
│   ├── rules.py            # Business logic thresholds & recommendation rules
│   ├── gemini.py           # Gemini API client wrapper for grounded response generation
│   ├── retrieval.py        # Local vector index & context retriever
│   ├── models.py           # Data schemas & Pydantic models
│   ├── data_loader.py      # CSV loading & validation pipelines
│   └── query_engine.py     # Copilot query pipeline & evidence synthesis
│
├── data/                   # Retail dataset (products, stores, sales, inventory)
│
└── static/                 # Frontend assets
    ├── index.html          # Single-page executive application layout
    ├── style.css           # Clean, professional modern retail UI design system
    └── app.js             # Interactive client logic & API bindings
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Google Gemini API key (`GEMINI_API_KEY`)

### Installation & Execution
```bash
# Install dependencies
pip install -r requirements.txt

# Environment Setup
export GEMINI_API_KEY="your-api-key-here"

# Run Application (Serves UI + Backend at http://localhost:8000)
python app.py
```
