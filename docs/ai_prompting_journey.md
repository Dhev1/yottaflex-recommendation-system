\# YottaFlex.ai — AI-Assisted Development and Prompt Engineering Journey



\## 1. Introduction



YottaFlex.ai was developed using an AI-assisted software engineering workflow. AI was used as a development partner to support project planning, database design, synthetic data generation, recommendation algorithm development, evaluation, backend implementation, frontend integration, testing, and technical documentation.



Rather than relying on generic code generation, the development process involved breaking the project into smaller milestones, defining technical requirements, validating generated outputs, debugging implementation issues, and refining the system incrementally.



This document presents a curated reconstruction of the key prompts used throughout the development lifecycle. The prompts have been rewritten into clear, technically structured instructions to demonstrate the engineering requirements and problem-solving approach behind the project.



\---



\## 2. Project Planning and System Architecture



\### Prompt 1 — Define the project requirements and architecture



I want to build an end-to-end e-commerce product recommendation system called YottaFlex.ai.



The objective is to simulate a realistic e-commerce environment, generate synthetic customer activity, develop recommendation algorithms, evaluate their performance, and expose the recommendations through an API and interactive dashboard.



Help me define a modular project architecture covering:



\- Synthetic data generation.

\- Relational database design.

\- Customer browsing and purchasing activity.

\- Data preprocessing and temporal splitting.

\- Recommendation algorithm development.

\- Offline recommendation evaluation.

\- REST API development.

\- Interactive dashboard development.

\- Automated testing and documentation.



Use Python, PostgreSQL, SQLAlchemy, Pandas, FastAPI, Pydantic, Pytest, HTTPX, and Streamlit.



Break the implementation into sequential milestones. For each milestone, explain its purpose, expected output, dependencies, and validation criteria.



Assume I am still developing my practical software engineering skills. Guide me through the implementation without skipping important steps.



\### Prompt 2 — Establish the development environment



Guide me through setting up the YottaFlex.ai development environment on Windows.



I need to configure:



\- Python and a virtual environment.

\- Required Python packages.

\- PostgreSQL database connectivity.

\- SQLAlchemy database configuration.

\- FastAPI application setup.

\- Project directory structure.

\- Environment variables for database credentials.



Provide the exact PowerShell commands, file paths, and configuration instructions.



Explain how to verify each component before moving to the next step. Keep sensitive credentials outside the source code.



\---



\## 3. Database Design and Synthetic Data Generation



\### Prompt 3 — Design the relational database schema



Design a relational database schema for a synthetic e-commerce platform.



The database should support:



\- Customers and their profiles.

\- Product categories and catalog information.

\- Customer browsing sessions.

\- Product page views.

\- Shopping carts and cart line items.

\- Orders and order line items.

\- Product-to-product relationships.

\- Recommendation records.



Use PostgreSQL with SQLAlchemy ORM.



Define appropriate primary keys, foreign keys, unique constraints, relationships, and data types. Explain how the entities relate to each other and ensure that the schema supports customer behaviour analysis and recommendation generation.



Organize the implementation into manageable model files or modules, and provide validation steps for each model.



\### Prompt 4 — Generate foundational synthetic e-commerce data



Implement a reproducible synthetic data generation process for the YottaFlex.ai platform.



Generate:



\- 20,000 customers.

\- 20 product categories.

\- 10,000 products.



Use Python and SQLAlchemy to persist the records in PostgreSQL.



Use a fixed random seed of 42 so that the generated dataset can be reproduced.



Ensure that customer identifiers, product SKUs, category references, and other required fields remain consistent and satisfy the database constraints.



Provide separate generation scripts where appropriate. Include validation queries to verify record counts, uniqueness, relationships, and successful database insertion.



Do not recreate or overwrite existing records unnecessarily.



\### Prompt 5 — Generate synthetic customer activity and transactions



Extend the synthetic e-commerce dataset with realistic customer interaction records.



Generate approximately:



\- 500,000 customer sessions.

\- Product page-view events associated with those sessions.

\- Shopping carts and cart line items.

\- Order records and order line items.



Use an activity date range from January 1, 2025, through October 31, 2026, with approximately 1–5 page views per session.



Model different customer behaviours, including browsing without purchasing, adding products to carts, abandoning carts, and completing purchases.



Maintain valid foreign-key relationships and consistent customer, product, session, cart, and order references.



Ensure that the generated events contain timestamps suitable for chronological recommendation evaluation.



Provide validation queries and scripts to check record counts, status distributions, missing references, duplicate records, and timestamp consistency.



\---



\## 4. Data Preparation and Chronological Evaluation



\### Prompt 6 — Implement a leakage-safe chronological train-test split



Implement a chronological data splitting pipeline for the YottaFlex.ai recommendation system.



Use the cutoff:



`2026-07-01 00:00:00 Asia/Kolkata`



Apply the following rules:



\- Training events must occur strictly before the cutoff.

\- Test events and ground-truth purchases must occur at or after the cutoff.

\- Customer preference calculations must use training-period information only.

\- Future purchases must not influence recommendation generation.

\- Previously purchased products must be excluded using training-period purchase history.



Generate separate CSV files for:



\- Training page views.

\- Training order lines.

\- Test orders.

\- Test ground truth.



Create a manifest documenting the cutoff, data sources, row counts, and splitting rules.



Validate the chronological boundaries and ensure the original PostgreSQL database is not modified by the export process.



Use explicit checks to detect accidental future-information leakage.



\### Prompt 7 — Validate the prepared dataset and evaluation ground truth



Perform a data quality audit on the generated training and test datasets.



Verify:



\- Record counts.

\- Customer and product identifier validity.

\- Missing values.

\- Duplicate customer-product purchase pairs.

\- Purchase status distributions.

\- Timestamp boundaries.

\- Training and test separation.

\- Ground-truth relevance construction.



Treat paid, shipped, and delivered orders as positive purchase outcomes.



Use binary customer-product relevance for ranking evaluation and document how duplicate customer-product pairs are handled.



Report the validation results clearly. Do not assume that a successful CSV export automatically means the dataset is correct.



\---



\## 5. Recommendation Algorithm Development



\### Prompt 8 — Build a category-aware popularity baseline



Implement a baseline product recommendation algorithm using only training-period information.



The algorithm should:



1\. Identify each customer's preferred product category from training-period browsing activity.

2\. Calculate global product popularity using training-period page views.

3\. Rank eligible products in the preferred category using global popularity.

4\. Use fallback candidates when the preferred category does not contain enough eligible products.

5\. Exclude products already purchased by the customer during the training period.

6\. Exclude inactive and out-of-stock products.

7\. Generate five recommendations per customer whenever sufficient eligible candidates exist.



Use a deterministic ranking strategy so that the same input data produces the same recommendations.



Save the output separately from the original database as a CSV file.



Include recommendation scores, customer identifiers, product identifiers, ranking positions, and relevant metadata.



Create a manifest describing the algorithm, input datasets, cutoff, and output statistics.



\### Prompt 9 — Build a personalized category-affinity recommendation algorithm



Implement a personalized recommendation algorithm that improves on the category-aware popularity baseline.



Use training-period browsing history to understand individual customer preferences.



The algorithm should:



1\. Identify the customer's preferred product category.

2\. Calculate individual product-view frequencies.

3\. Prioritize products based on the customer's own browsing behaviour.

4\. Use category popularity and global popularity as supporting ranking and fallback signals.

5\. Exclude products already purchased during the training period.

6\. Filter inactive and out-of-stock products.

7\. Generate up to five recommendations per customer.



Keep the implementation deterministic and ensure that no test-period information is used.



Save the results in a separate CSV file with recommendation scores and ranking information.



Document the algorithm's scoring logic, fallback behaviour, filtering rules, and limitations.



\### Prompt 10 — Validate recommendation quality and eligibility



Create a validation process for both recommendation algorithms.



Verify that:



\- Each customer receives no more than five recommendations.

\- Recommendation records contain valid customer and product identifiers.

\- Ranking positions are valid and ordered correctly.

\- Previously purchased products are excluded.

\- Inactive products are excluded.

\- Out-of-stock products are excluded.

\- Recommendation scores are valid.

\- Duplicate recommendations are not generated for the same customer.

\- Sufficient candidates are available where expected.



Generate a validation summary with explicit pass/fail results.



Keep validation independent of the original database and do not modify the source recommendation or training data.



\---



\## 6. Recommendation Evaluation and Model Comparison



\### Prompt 11 — Implement offline ranking evaluation metrics



Build a reusable recommendation evaluation module in Python.



Implement the following metrics:



\- Precision@K.

\- Recall@K.

\- Normalized Discounted Cumulative Gain (NDCG@K).

\- Catalog Coverage.

\- Availability Violations.



Use binary purchase relevance from the chronological test ground truth.



Calculate customer-level ranking metrics and macro-average them across customers with at least one relevant test-period purchase.



Use the same evaluation cutoff, ground truth, eligible product catalog, and ranking depth for both algorithms.



Create small, hand-checkable examples to verify the mathematical correctness of the metrics before running full-dataset evaluation.



Handle edge cases such as empty recommendations, invalid K values, missing relevant items, and empty catalogs.



Add automated unit tests for the metric calculations.



\### Prompt 12 — Compare the baseline and personalized models



Evaluate both recommendation algorithms using the same training and test datasets.



Generate a comparison covering:



\- Precision@5.

\- Recall@5.

\- NDCG@5.

\- Catalog Coverage.

\- Availability Violations.



Report the number of evaluated customers, recommendation records, eligible catalog products, and distinct recommended products.



Save the comparison in machine-readable JSON and CSV formats.



Explain the trade-offs between ranking quality and catalog diversity.



Do not assume that the personalized algorithm is automatically better. Interpret the actual measured results and clearly identify the strengths and limitations of each model.



\---



\## 7. Backend Development and API Integration



\### Prompt 13 — Build the FastAPI recommendation service



Develop a FastAPI backend for the YottaFlex.ai recommendation system.



Integrate it with the existing PostgreSQL database using SQLAlchemy.



Create Pydantic response schemas for customers, products, recommendation items, recommendation responses, model evaluations, and model comparisons.



Implement endpoints for:



\- API information.

\- Database health.

\- Customer details.

\- Product details.

\- Customer recommendations.

\- Model evaluation comparison.

\- Recommendation exports.



The recommendation endpoint should support both baseline and personalized models.



Read the previously generated recommendation CSV files and evaluation JSON files instead of regenerating recommendations on every API request.



Support JSON and CSV recommendation exports.



Validate customer and product identifiers, handle invalid requests appropriately, and filter recommendations against current product availability.



Keep the API modular and avoid modifying the original database unnecessarily.



\### Prompt 14 — Add automated API testing



Create an automated API test suite using Pytest and HTTPX.



Test:



\- Root endpoint.

\- Health endpoint.

\- Existing customer retrieval.

\- Nonexistent customer handling.

\- Product retrieval.

\- Baseline recommendations.

\- Personalized recommendations.

\- Invalid customer recommendation requests.

\- Model evaluation response.

\- JSON recommendation export.

\- CSV recommendation export.



Use controlled test requests and validate response status codes, response structures, and expected data.



Ensure that tests do not accidentally regenerate the synthetic dataset or modify production-style recommendation outputs.



Run the complete test suite and report the actual number of passed and failed tests.



\---



\## 8. Interactive Dashboard Development



\### Prompt 15 — Build the Streamlit application



Develop an interactive Streamlit dashboard for YottaFlex.ai.



The dashboard should communicate with the FastAPI backend rather than duplicating recommendation logic.



Include:



1\. Application title and overview.

2\. API and database connection status.

3\. Customer ID selection.

4\. Customer profile information.

5\. Baseline and personalized model selection.

6\. Customer-specific recommendation results.

7\. Individual product cards.

8\. Recommendation ranking and scores.

9\. CSV and JSON export options.

10\. Model comparison table.

11\. Precision@5, Recall@5, and NDCG@5 comparison charts.

12\. Catalog coverage comparison.

13\. Availability violation statistics.



Use a clean, understandable layout that allows users to inspect individual recommendations and compare model performance.



Handle API connection errors, invalid customer IDs, and missing recommendation results gracefully.



Provide the complete dashboard implementation and exact instructions for running it locally.



\---



\## 9. Documentation, Verification, and Delivery



\### Prompt 16 — Create technical project documentation



Prepare professional technical documentation for the completed YottaFlex.ai project.



Create:



\- A README with project overview, features, architecture, setup instructions, API endpoints, and execution steps.

\- An algorithm explanation document describing the baseline and personalized recommendation approaches.

\- An evaluation report documenting the chronological split, metrics, actual results, comparison, and limitations.

\- A project architecture document explaining the complete data flow and application components.



Include actual verified dataset sizes, evaluation metrics, and test results.



Clearly distinguish implemented functionality from proposed future enhancements.



Avoid unsupported performance claims or invented experimental results.



\### Prompt 17 — Perform the final project audit



Conduct a final technical verification of the complete YottaFlex.ai project.



Check:



\- Project directory structure.

\- Required source files.

\- Documentation completeness.

\- Environment configuration.

\- Git ignore rules.

\- Python compilation.

\- Automated API and metric tests.

\- Recommendation output files.

\- Evaluation reports.

\- Dashboard integration.

\- API startup instructions.



Do not rerun synthetic data generation, recreate database tables, overwrite existing reports, or modify the original database during the audit.



Report verified results separately from items that still require manual confirmation.



Prepare a final project delivery checklist.



\---



\## 10. Development Approach and AI Collaboration



The project followed an iterative AI-assisted engineering approach:



1\. \*\*Requirement definition:\*\* Convert the project objective into a structured technical architecture.

2\. \*\*Incremental implementation:\*\* Break large development tasks into smaller, verifiable milestones.

3\. \*\*Technical guidance:\*\* Use AI to explain database concepts, Python implementation, recommendation logic, API design, and evaluation methodology.

4\. \*\*Validation-driven development:\*\* Execute SQL queries, inspect generated files, run test cases, and verify actual outputs.

5\. \*\*Debugging:\*\* Share errors and runtime outputs to identify implementation issues and refine the solution.

6\. \*\*Documentation:\*\* Convert implementation details and verified results into professional technical documentation.

7\. \*\*Final verification:\*\* Run compilation and automated tests before delivery.



\## 11. Responsible Use of AI



AI was used as an engineering assistance tool, not as a replacement for implementation and verification.



Generated code and recommendations were reviewed through execution, database validation, output inspection, and automated testing.



The final implementation was evaluated using actual generated data and measured evaluation results.



This approach demonstrates how structured prompting, iterative development, and technical validation can be combined to build a complete software application.

