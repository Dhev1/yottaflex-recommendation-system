# YottaFlex.ai — E-commerce Recommendation System

## 1. Project Overview

YottaFlex.ai is a data-driven e-commerce product recommendation system designed to generate product recommendations using customer browsing behaviour, purchase history, product popularity, and category preferences.

The project implements two recommendation algorithms:

1. **Baseline Recommendation Model:** Recommends popular products based on customer category affinity and training-period product popularity.
2. **Personalized Recommendation Model:** Uses individual product-view frequency and category preferences to generate customer-specific recommendations.

The system includes synthetic e-commerce data generation, PostgreSQL data storage, chronological train-test splitting, recommendation evaluation, a FastAPI backend, and a Streamlit dashboard.

## 2. Key Features

- Synthetic e-commerce dataset generation.
- PostgreSQL relational database.
- Customer, product, session, browsing, cart, and order data.
- Chronological training and testing data separation.
- Baseline category-popularity recommendations.
- Personalized category-affinity recommendations.
- Exclusion of previously purchased products.
- Filtering of inactive and out-of-stock products.
- Precision@K, Recall@K, and NDCG@K evaluation.
- Catalog coverage and availability validation.
- FastAPI recommendation endpoints.
- Streamlit interactive dashboard.
- JSON and CSV recommendation exports.
- Automated testing using Pytest.

## 3. Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| Database | PostgreSQL |
| Database Integration | SQLAlchemy |
| Data Processing | Pandas |
| API Framework | FastAPI |
| Dashboard | Streamlit |
| Data Validation | Pydantic |
| Testing | Pytest, HTTPX |
| API Documentation | Swagger / OpenAPI |
| Data Export | CSV, JSON |

## 4. Dataset Overview

The synthetic dataset contains:

| Dataset | Records |
|---|---:|
| Customers | 20,000 |
| Categories | 20 |
| Products | 10,000 |
| Sessions | 500,000 |
| Page Views | 1,497,995 |
| Carts | 150,000 |
| Cart Lines | 375,671 |
| Orders | 100,000 |
| Order Lines | 173,646 |
| Product Relations | 20,000 |

The original database also contains 100,000 baseline recommendation records. These all-time recommendations are separate from the train-only evaluation recommendations.

## 5. Project Architecture

The project follows a modular architecture:

- **Data Generation:** Generates synthetic customers, products, browsing sessions, carts, orders, and product relationships.
- **Database Layer:** Stores and manages the generated e-commerce data in PostgreSQL.
- **Data Preparation:** Creates chronological training and testing datasets.
- **Recommendation Engine:** Generates baseline and personalized product recommendations.
- **Evaluation Module:** Measures recommendation relevance, ranking quality, catalog coverage, and availability violations.
- **API Layer:** Exposes customer, product, recommendation, evaluation, and export endpoints.
- **Dashboard:** Provides an interactive interface for customer recommendations and model comparison.

## 6. Chronological Data Split

The evaluation uses a chronological cutoff:

`2026-07-01T00:00:00+05:30`

- Training events occur strictly before the cutoff.
- Test purchase events occur at or after the cutoff.
- Customer preferences and recommendation history use training-period information.
- The original database remains unchanged.

The test evaluation uses positive purchase statuses: paid, shipped, and delivered.

## 7. Recommendation Algorithms

### 7.1 Baseline — Category Popularity

The baseline model:

1. Identifies a customer's preferred category using training-period browsing activity.
2. Ranks products using global training-period page-view popularity.
3. Prioritizes popular products in the preferred category.
4. Uses global popularity as a fallback.
5. Excludes previously purchased and currently unavailable products.
6. Produces up to five recommendations per customer.

Model identifier: `category_affinity_train_only`

### 7.2 Personalized — Customer Product Affinity

The personalized model:

1. Identifies the customer's preferred category.
2. Uses individual product-view frequency to rank previously viewed products.
3. Prioritizes products within the preferred category.
4. Uses other personally viewed products as fallback candidates.
5. Excludes previously purchased and currently unavailable products.
6. Produces up to five recommendations per customer.

Model identifier: `personalized_category_affinity_v2`

## 8. Evaluation Methodology

Both algorithms are evaluated using the same chronological test dataset.

The evaluation metrics include:

- **Precision@5:** Proportion of recommended products that are relevant.
- **Recall@5:** Proportion of relevant test products successfully recommended.
- **NDCG@5:** Measures ranking quality with greater importance assigned to higher-ranked relevant products.
- **Catalog Coverage:** Proportion of eligible catalog products appearing in recommendations.
- **Availability Violations:** Number of recommended products that are inactive or out of stock.

The ranking metrics are macro-averaged across customers with at least one relevant test purchase.

## 9. Actual Evaluation Results

| Metric | Baseline | Personalized |
|---|---:|---:|
| Precision@5 | 0.000345 | 0.000162 |
| Recall@5 | 0.000649 | 0.000253 |
| NDCG@5 | 0.000547 | 0.000215 |
| Catalog Coverage | 1.64% | 99.96% |
| Availability Violations | 0 | 0 |

Evaluation population: 9,869 customers with at least one positive test purchase.

Each model generated 100,000 recommendation rows.

### Interpretation

The baseline model achieved higher Precision@5, Recall@5, and NDCG@5.

The personalized model achieved substantially higher catalog coverage, exposing customers to a much broader range of products.

Neither model is universally superior across all evaluation dimensions.

## 10. Running the Project

### Prerequisites

- Python 3.13
- PostgreSQL
- Virtual environment
- Project database configured through `.env`

### Step 1: Activate the virtual environment

```powershell
.\venv\Scripts\Activate.ps1
```

### Step 2: Start the FastAPI backend

```powershell
uvicorn app.main:app --reload
```

API base URL:

`http://127.0.0.1:8000`

Swagger documentation:

`http://127.0.0.1:8000/docs`

### Step 3: Start the Streamlit dashboard

Open another PowerShell terminal, activate the virtual environment, and execute:

```powershell
python -m streamlit run .\dashboard\dashboard.py
```

Dashboard URL:

`http://localhost:8501`

### Step 4: Run automated tests

```powershell
python -m pytest -v
```

The verified test suite contains 18 passing tests.

## 11. API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | API information |
| GET | `/health` | API and database health |
| GET | `/customers/{customer_id}` | Retrieve customer details |
| GET | `/products/{product_id}` | Retrieve product details |
| GET | `/recommendations/{customer_id}` | Generate or retrieve recommendations |
| GET | `/evaluation/models` | Compare evaluation results |
| GET | `/recommendations/{customer_id}/export` | Export recommendations |

Recommendation model selection:

`?model=baseline`

or

`?model=personalized`

Export format selection:

`?format=json`

or

`?format=csv`

## 12. Project Limitations

- The recommendation algorithms use browsing frequency and popularity rather than a trained machine-learning ranking model.
- The personalized algorithm recommends previously viewed products, making it more suitable for conversion-oriented recommendations than unseen-product discovery.
- The synthetic dataset may not represent real-world customer behaviour.
- Product creation timestamps are not used for historical catalog eligibility because the synthetic catalog records were created after the evaluation cutoff.
- Product availability is evaluated using the current active and in-stock snapshot, not historical inventory.
- Evaluation measures purchase relevance, not customer satisfaction or actual business revenue.

## 13. Future Enhancements

- Collaborative filtering.
- Matrix factorization.
- Content-based product recommendations.
- Hybrid recommendation algorithms.
- Product similarity using embeddings.
- Real-time recommendation updates.
- Customer segmentation.
- A/B testing and recommendation performance monitoring.
- Integration with a production e-commerce platform.

## 14. Conclusion

YottaFlex.ai demonstrates an end-to-end e-commerce recommendation workflow, from synthetic data generation and PostgreSQL storage to chronological evaluation, recommendation APIs, and an interactive dashboard.

The project compares a popularity-based baseline with a personalized category-affinity approach and highlights the trade-off between ranking relevance and catalog coverage.




## AI-Assisted Development and Prompt Engineering

YottaFlex.ai was developed through an iterative AI-assisted engineering workflow. Structured prompts were used to support requirement analysis, database design, synthetic data generation, chronological data preparation, recommendation algorithm development, model evaluation, API implementation, dashboard development, testing, and documentation.

The complete collection of professionally structured development prompts is available here:

[AI-Assisted Development and Prompt Engineering Journey](docs/ai_prompting_journey.md)

This document presents a chronological reconstruction of the key technical instructions used throughout the project, highlighting the role of structured prompting, iterative implementation, debugging, and validation.