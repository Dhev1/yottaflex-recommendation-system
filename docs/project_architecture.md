\# YottaFlex.ai — System Architecture and Technical Design



\## 1. Introduction



YottaFlex.ai is an end-to-end e-commerce recommendation system designed to generate, evaluate, and deliver product recommendations using customer browsing behaviour and product popularity.



The application follows a modular architecture consisting of:



1\. Synthetic data generation.

2\. Relational database management.

3\. Data preparation and chronological splitting.

4\. Recommendation generation.

5\. Offline evaluation.

6\. REST API development.

7\. Interactive dashboard development.



The architecture separates data generation, recommendation processing, evaluation, and application delivery.



\---



\## 2. High-Level Architecture



```mermaid

flowchart TD

&#x20;   A\[Synthetic Data Generator] --> B\[PostgreSQL Database]

&#x20;   B --> C\[Data Preparation]

&#x20;   C --> D\[Chronological Train-Test Split]

&#x20;   D --> E\[Recommendation Engine]

&#x20;   E --> F\[Baseline Model]

&#x20;   E --> G\[Personalized Model]

&#x20;   F --> H\[Evaluation Engine]

&#x20;   G --> H

&#x20;   H --> I\[Evaluation Reports]

&#x20;   F --> J\[Recommendation CSV Files]

&#x20;   G --> J

&#x20;   J --> K\[FastAPI Backend]

&#x20;   I --> K

&#x20;   B --> K

&#x20;   K --> L\[Streamlit Dashboard]

&#x20;   L --> M\[Customer Recommendations]

&#x20;   L --> N\[Model Comparison]

&#x20;   L --> O\[CSV and JSON Downloads]

```



\---



\## 3. Technology Architecture



| Layer | Technology | Responsibility |

|---|---|---|

| Data Generation | Python | Synthetic e-commerce data |

| Database | PostgreSQL | Persistent relational storage |

| ORM | SQLAlchemy | Database interaction |

| Data Processing | Pandas | Data preparation and analysis |

| Recommendation Engine | Python | Recommendation algorithms |

| Evaluation | Python, Pandas | Ranking and coverage metrics |

| Backend | FastAPI | REST API endpoints |

| Validation | Pydantic | Request and response schemas |

| Frontend | Streamlit | Interactive dashboard |

| Testing | Pytest, HTTPX | Automated testing |

| API Documentation | OpenAPI, Swagger | API exploration |



\---



\## 4. Data Generation Layer



The data generation layer creates synthetic e-commerce records to simulate an online shopping platform.



The generated entities include:



\- Customers

\- Categories

\- Products

\- Sessions

\- Page views

\- Shopping carts

\- Cart lines

\- Orders

\- Order lines

\- Product relationships

\- Original all-time recommendation records



The generator produces a structured dataset that supports customer behaviour analysis and recommendation experiments.



The generated records are stored in PostgreSQL.



\---



\## 5. Database Layer



PostgreSQL serves as the primary persistent data store.



SQLAlchemy provides database connectivity and ORM-based model definitions.



The database contains 11 main tables:



| Table | Purpose |

|---|---|

| customers | Customer information |

| categories | Product categories |

| products | Product catalog and inventory |

| sessions | Customer browsing sessions |

| page\_views | Customer product browsing activity |

| carts | Shopping cart records |

| cart\_lines | Products added to carts |

| orders | Customer purchase transactions |

| order\_lines | Products included in orders |

| product\_relations | Product relationship records |

| recommendations | Original recommendation records |



The original database is preserved during offline evaluation. Train-test split files and evaluation recommendation files are maintained separately.



\---



\## 6. Data Preparation Layer



The data preparation layer extracts relevant browsing and purchase records from PostgreSQL.



A chronological cutoff is used:



`2026-07-01T00:00:00+05:30`



\### Training data



Events strictly before the cutoff are used to construct customer browsing preferences and recommendation history.



\### Test data



Events at or after the cutoff are reserved for evaluation.



\### Data preparation outputs



\- Training page views

\- Training order lines

\- Test orders

\- Test ground truth

\- Temporal split manifest



This separation prevents future test-period purchase information from influencing recommendation generation.



\---



\## 7. Recommendation Engine



The recommendation engine implements two distinct approaches.



\### 7.1 Baseline Model



Model identifier:



`category\_affinity\_train\_only`



The baseline model:



1\. Analyzes customer browsing activity.

2\. Identifies the preferred product category.

3\. Ranks products using global training-period page-view popularity.

4\. Uses fallback candidates when required.

5\. Excludes previously purchased products.

6\. Filters inactive and out-of-stock products.

7\. Generates up to five recommendations.



\### 7.2 Personalized Model



Model identifier:



`personalized\_category\_affinity\_v2`



The personalized model:



1\. Analyzes individual customer browsing history.

2\. Identifies the preferred category.

3\. Calculates individual product-view frequency.

4\. Prioritizes personally viewed products.

5\. Uses category and global popularity as supporting ranking signals and fallback considerations.

6\. Excludes previously purchased products.

7\. Filters unavailable products.

8\. Generates up to five recommendations.



Both algorithms produce separate CSV recommendation files and manifests.



\---



\## 8. Evaluation Layer



The evaluation layer measures recommendation performance against test-period purchases.



The metrics include:



| Metric | Purpose |

|---|---|

| Precision@5 | Recommendation relevance |

| Recall@5 | Relevant product retrieval |

| NDCG@5 | Ranking quality |

| Catalog Coverage | Product diversity |

| Availability Violations | Inventory eligibility validation |



The evaluation is conducted separately for each recommendation model.



\### Evaluation outputs



\- Baseline evaluation results.

\- Personalized evaluation results.

\- Per-customer metrics.

\- Combined model comparison.

\- Recommendation validation results.



The generated evaluation reports are consumed by the API and dashboard.



\---



\## 9. Backend Architecture — FastAPI



FastAPI provides the application backend.



The backend connects to PostgreSQL and reads the previously generated recommendation and evaluation files.



It exposes endpoints for customer details, product information, recommendation retrieval, model evaluation, and exports.



\### API endpoints



| Method | Endpoint | Responsibility |

|---|---|---|

| GET | `/` | API information |

| GET | `/health` | Database health |

| GET | `/customers/{customer\_id}` | Customer details |

| GET | `/products/{product\_id}` | Product details |

| GET | `/recommendations/{customer\_id}` | Customer recommendations |

| GET | `/evaluation/models` | Model evaluation comparison |

| GET | `/recommendations/{customer\_id}/export` | Recommendation export |



\### Recommendation request example



```http

GET /recommendations/1?model=baseline

```



Personalized recommendation example:



```http

GET /recommendations/1?model=personalized

```



\### Export examples



```http

GET /recommendations/1/export?model=baseline\&format=csv

```



```http

GET /recommendations/1/export?model=personalized\&format=json

```



\### API response structure



Recommendation responses contain:



\- Customer ID

\- Recommendation model

\- Model identifier

\- Recommendation count

\- Product details

\- Recommendation score

\- Ranking position

\- Preferred category

\- Recommendation reason



Pydantic schemas validate the response structure.



Swagger documentation is available at:



`http://127.0.0.1:8000/docs`



\---



\## 10. Frontend Architecture — Streamlit



Streamlit provides the interactive dashboard.



The frontend communicates with FastAPI using HTTP requests.



It does not independently calculate recommendations or directly modify PostgreSQL.



\### Dashboard components



1\. API and database connection status.

2\. Customer ID selection.

3\. Customer profile display.

4\. Recommendation algorithm selection.

5\. Recommended product table.

6\. Individual product cards.

7\. CSV and JSON downloads.

8\. Model comparison table.

9\. Ranking quality charts.

10\. Catalog coverage comparison.

11\. Individual model performance metrics.

12\. Availability validation.



Dashboard execution:



```powershell

python -m streamlit run .\\dashboard\\dashboard.py

```



Dashboard URL:



`http://localhost:8501`



\---



\## 11. Testing Architecture



Pytest and HTTPX are used to validate application behaviour.



The test suite includes:



\### API tests



\- Home endpoint.

\- Health endpoint.

\- Existing customer retrieval.

\- Nonexistent customer handling.

\- Product retrieval.

\- Baseline recommendation retrieval.

\- Personalized recommendation retrieval.

\- Invalid customer recommendation handling.

\- Model evaluation endpoint.

\- JSON export.

\- CSV export.



\### Evaluation metric tests



\- Hand-calculated ranking metric example.

\- Catalog coverage.

\- Availability violations.

\- Exclusion of customers without relevant ground-truth items.

\- Invalid ranking cutoff handling.

\- Empty ground-truth validation.

\- Empty catalog validation.



\### Verified result



The complete automated test suite contains 18 tests.



Verified execution result:



`18 passed, 1 warning`



The warning relates to the Starlette TestClient and HTTPX integration deprecation. It did not cause test failures.



\---



\## 12. Project Directory Structure



The main project structure is:



```text

yottaflex-recommendation-system/

│

├── app/

│   ├── main.py

│   ├── models.py

│   ├── database.py

│   ├── config.py

│   ├── schemas.py

│   ├── evaluation/

│   │   └── metrics.py

│   ├── generate\_evaluation\_recommendations.py

│   ├── generate\_personalized\_recommendations.py

│   └── ...

│

├── dashboard/

│   └── dashboard.py

│

├── data/

│

├── docs/

│   ├── algorithm\_explanation.md

│   ├── evaluation\_report.md

│   └── project\_architecture.md

│

├── generator/

│

├── reports/

│   ├── temporal\_split/

│   └── evaluation/

│

├── tests/

│   ├── test\_api.py

│   └── test\_metrics.py

│

├── venv/

│

├── .env

├── .env.example

├── .gitignore

├── requirements.txt

└── README.md

```



The ellipsis represents additional existing project files and scripts.



\---



\## 13. End-to-End Application Workflow



The complete workflow is:



1\. Generate synthetic e-commerce data.

2\. Store the generated records in PostgreSQL.

3\. Extract browsing and purchase history.

4\. Apply the chronological train-test split.

5\. Generate baseline recommendations.

6\. Generate personalized recommendations.

7\. Validate recommendation eligibility.

8\. Evaluate both algorithms against test-period purchases.

9\. Save recommendation and evaluation outputs.

10\. Start the FastAPI backend.

11\. Start the Streamlit dashboard.

12\. Retrieve customer-specific recommendations.

13\. Compare model performance.

14\. Export recommendation results in CSV or JSON.

15\. Execute automated tests.



\---



\## 14. Design Considerations



\### Separation of concerns



Data generation, database access, recommendation processing, evaluation, backend delivery, and dashboard presentation are maintained as separate responsibilities.



\### Reproducible evaluation



Recommendation outputs and evaluation results are stored separately from the original database.



\### Chronological evaluation



Training and testing are separated by event timestamps to reduce future-information leakage.



\### Availability filtering



The recommendation engine and evaluation process validate product availability using the configured inventory eligibility rules.



\### API-driven frontend



The Streamlit dashboard consumes the FastAPI backend instead of duplicating recommendation logic.



\---



\## 15. Future Architecture Enhancements



Potential improvements include:



\- Background recommendation generation jobs.

\- Redis caching.

\- Asynchronous API endpoints.

\- Docker-based deployment.

\- Cloud-hosted PostgreSQL.

\- Authentication and role-based access control.

\- Scheduled recommendation refresh.

\- Real-time browsing event ingestion.

\- Monitoring and logging.

\- Collaborative and hybrid recommendation services.

\- Online A/B testing infrastructure.



\---



\## 16. Conclusion



YottaFlex.ai demonstrates a modular, end-to-end e-commerce recommendation architecture.



The system integrates synthetic data generation, relational database storage, chronological evaluation, two recommendation algorithms, REST API development, and interactive dashboard delivery.



The architecture provides a foundation for extending the current heuristic-based recommendation engine into a scalable hybrid recommendation platform.



