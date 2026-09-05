TRACK_ID=PS03

# ShelfIQ - Retail Sales & Inventory Copilot

**Smarter shelves. Better decisions.**

ShelfIQ is a judge-ready retail analytics and AI copilot application for PS03 - Retail Sales & Inventory Copilot. It helps a store manager understand what may run out, what is overstocked, what is not moving, which products have sales spikes or drops, and what action should be considered next.

## Problem

Retail managers need to make daily decisions from scattered sales and inventory data. ShelfIQ turns local CSV data into deterministic metrics, prioritized attention items, and grounded AI explanations with visible evidence.

## Main Features

- Executive dashboard with sales, growth, inventory value, low-stock, trend, attention, and top-product views.
- Inventory table with store, category, status, and search filters.
- Sales analytics with real API-backed trend data, growth comparison, top products, and bottom products.
- Attention page for stock-out risks, slow-moving items, overstock, sales spikes, and sales drops.
- AI Copilot page that answers retail questions with supporting numbers, evidence, recommendations, assumptions, and data sufficiency.
- Graceful fallback when Gemini is unavailable: deterministic analytics still work.

## Architecture

```text
CSV data
  -> DataLoader validation
  -> deterministic AnalyticsEngine
  -> deterministic AttentionEngine rules
  -> FastAPI endpoints
  -> static frontend served by Python
  -> Gemini explanation over structured evidence only
```

Python remains the source of truth for all business calculations. Gemini never calculates critical metrics.

## Deterministic Analytics

`src/analytics.py` calculates totals, units sold, daily averages, product performance, category performance, store performance, inventory value, days remaining, sales trends, sales growth, stock-out risk, slow-moving products, overstock, sales spikes, and sales drops.

The analytics layer handles zero sales, missing sales, short history, division by zero, no-sales products, and filtered store/category/date ranges.

## Business Rules

`src/rules.py` converts analytics output into attention items with:

- attention type and severity
- product and store identifiers
- metric summary
- evidence values
- recommendation
- assumptions
- data sufficiency

The supported attention types are stock-out risk, slow-moving, overstock, sales spike, and sales drop.

## Gemini Role

Gemini is optional and is used only for grounded explanation. It receives a small structured evidence payload from Python and must not invent products, stores, dates, numbers, prices, inventory quantities, trends, or percentages.

If `GEMINI_API_KEY` is missing or Gemini fails, ShelfIQ returns deterministic evidence with a clear message that AI explanation is unavailable.

## Grounded Evidence

Copilot responses include:

- `answer`
- `key_points`
- `supporting_numbers`
- `evidence`
- `recommendation`
- `assumptions`
- `data_sufficiency`

Evidence labels are internal application sources such as `Inventory analysis`, `Sales analysis`, `Attention engine`, `Product performance`, and `Store analysis`.

## Dataset

The committed synthetic dataset lives in `data/`:

- `stores.csv`
- `products.csv`
- `inventory.csv`
- `sales.csv`

The dataset includes multiple stores, product categories, 90 days of sales history, and intentional demo scenarios for stock-out risk, slow-moving items, overstock, sales spikes, sales drops, insufficient history, and store variance.

## Install

```bash
pip install -r requirements.txt
```

## Configure Gemini

Gemini is optional for deterministic operation. To enable live AI explanations, create a local `.env` file or set an environment variable:

```bash
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.0-flash
```

Do not commit `.env`. The repository includes `.env.example` only as a template.

## Run

```bash
python app.py
```

Open:

```text
http://localhost:8000
```

API docs:

```text
http://localhost:8000/docs
```

No npm, frontend build, hosted database, second terminal, or manual data generation is required.

## API

Core endpoints:

- `GET /`
- `GET /api/health`
- `GET /api/summary`
- `GET /api/inventory`
- `GET /api/sales`
- `GET /api/attention`
- `GET /api/products/{product_id}`
- `POST /api/ai/analyze`

`POST /api/ai/analyze` accepts:

```json
{
  "question": "Which products are likely to run out?"
}
```

## Testing

Run the full test suite:

```bash
python -m unittest discover -s tests -v
```

Validate demo data:

```bash
python data/validate_data.py
```

The live Gemini tests run only when `GEMINI_API_KEY` is available.

## Failure Handling

ShelfIQ handles invalid filters, invalid products, invalid dates, empty questions, malformed copilot requests, missing Gemini configuration, Gemini API failures, malformed Gemini responses, and insufficient data without exposing stack traces or secrets.

## Human In The Loop

ShelfIQ makes recommendations such as reviewing replenishment or investigating a drop. It does not place orders, perform external actions, or claim that an action was completed.

## Demo Flow

1. Open Dashboard and show KPI cards and real sales trend.
2. Open Attention and show stock-out evidence and recommendation.
3. Show slow-moving or overstock examples.
4. Open Sales and show top/bottom products plus sales growth.
5. Open AI Copilot and ask: `Which products are likely to run out?`
6. Show answer, supporting numbers, evidence, recommendation, assumptions, and data sufficiency.
7. Ask: `What should I review today?`
8. Explain that deterministic Python calculations produce the evidence and Gemini only explains it.

## Known Limitations

- Live Gemini explanation requires a valid `GEMINI_API_KEY`.
- The dataset is synthetic and designed for hackathon demonstration.
- Recommendations are decision support, not automated procurement actions.
- Supplier lead times, employee data, competitor pricing, weather, and promotions are outside the current dataset.

## Track ID Note

This repository uses `TRACK_ID=PS03`, matching the selected problem statement: Retail Sales & Inventory Copilot. No conflicting official project document was present in the repository during finalization.
