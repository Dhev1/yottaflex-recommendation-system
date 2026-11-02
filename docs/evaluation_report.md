\# YottaFlex.ai — Recommendation Model Evaluation Report



\## 1. Executive Summary



This report evaluates two e-commerce product recommendation algorithms developed as part of YottaFlex.ai:



1\. Baseline Category-Popularity Recommendation

2\. Personalized Category-Affinity Recommendation



Both algorithms were evaluated using a chronological train-test split to prevent future purchase information from influencing recommendation generation.



The evaluation compares recommendation relevance, ranking quality, catalog coverage, and product availability.



\### Key findings



\- The baseline model achieved higher Precision@5, Recall@5, and NDCG@5.

\- The personalized model achieved significantly higher catalog coverage.

\- Both models recorded zero availability violations in the offline evaluation.

\- Neither model outperformed the other across every evaluation dimension.



\---



\## 2. Dataset Overview



The synthetic e-commerce dataset contains:



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



The original database contains additional all-time recommendation records. These were not used as the train-only recommendation source for this evaluation.



\---



\## 3. Chronological Train-Test Split



\### 3.1 Cutoff definition



The evaluation cutoff was:



`2026-07-01T00:00:00+05:30`



This corresponds to the Asia/Kolkata timezone.



\### 3.2 Split rules



\- Training events occurred strictly before the cutoff.

\- Test events occurred at or after the cutoff.

\- Training browsing history was used to construct customer preferences.

\- Test purchases were reserved for ground-truth evaluation.

\- Future test-period information was not used to generate recommendations.



\### 3.3 Split results



| Dataset | Training / Test Records |

|---|---:|

| Training Page Views | 1,223,085 |

| Training Order Lines | 142,144 |

| Test Orders | 18,151 |

| Test Ground-Truth Lines | 31,502 |



\### 3.4 Positive test purchases



Only orders with the following statuses were considered positive purchases:



\- Paid

\- Shipped

\- Delivered



Results:



| Measurement | Count |

|---|---:|

| Positive Test Orders | 13,523 |

| Positive Ground-Truth Lines | 23,477 |

| Unique Positive Customer-Product Pairs | 23,476 |

| Customers with Positive Test Purchases | 9,869 |

| Customers without Positive Test Purchases | 10,131 |



One duplicate customer-product pair was present in the positive ground-truth data.



The evaluation uses binary relevance: a customer-product pair is considered relevant if that customer purchased the product during the test period. Purchase quantity is not used as an additional relevance weight.



\---



\## 4. Evaluation Configuration



Both recommendation algorithms were evaluated using the same:



\- Training-period browsing data.

\- Test-period purchase ground truth.

\- Evaluation cutoff.

\- Customer population.

\- Recommendation count.

\- Product eligibility rules.



\### Evaluation parameters



| Parameter | Value |

|---|---|

| Recommendation cutoff | 2026-07-01T00:00:00+05:30 |

| Recommendations per customer | 5 |

| Recommendation rows per model | 100,000 |

| Customers with relevant test purchases | 9,869 |

| Eligible catalog products | 7,418 |

| Relevance definition | Binary purchase relevance |

| Evaluation averaging | Macro average |

| Ranking cutoff | K = 5 |



The ranking metrics are macro-averaged across customers who have at least one relevant test purchase.



Customers without positive test purchases are excluded from Precision@5, Recall@5, and NDCG@5 averaging.



\### Product eligibility



Products were considered eligible when:



\- `is\_active = TRUE`

\- `stock\_quantity > 0`



Previously purchased products were excluded from recommendation candidates.



The eligible catalog contained 7,418 products.



\---



\## 5. Evaluation Metrics



\### 5.1 Precision@5



Precision@5 measures the proportion of the five recommended products that are relevant to a customer.



A relevant product is one purchased by that customer during the test period.



A higher value indicates that recommendations contain a greater proportion of relevant products.



\### 5.2 Recall@5



Recall@5 measures the proportion of a customer's relevant test-period products that appear among the five recommendations.



A higher value indicates that the recommendation list captures more of the customer's relevant purchases.



\### 5.3 NDCG@5



Normalized Discounted Cumulative Gain at 5 evaluates recommendation ranking quality.



Relevant products appearing at higher positions contribute more than relevant products appearing lower in the ranking.



A higher value indicates better ordering of relevant products.



\### 5.4 Catalog Coverage



Catalog Coverage measures the proportion of eligible catalog products that appear at least once in the recommendation output.



It measures recommendation diversity across the product catalog.



\### 5.5 Availability Violations



Availability Violations count recommended products that fail the current availability checks.



A violation occurs if a recommended product is inactive or has zero stock.



\---



\## 6. Baseline Model Results



Model identifier:



`category\_affinity\_train\_only`



| Metric | Result |

|---|---:|

| Precision@5 | 0.0003445131 |

| Recall@5 | 0.0006487365 |

| NDCG@5 | 0.0005469521 |

| Catalog Coverage | 0.01644648 |

| Catalog Coverage Percentage | 1.64% |

| Availability Violations | 0 |

| Availability Violation Rate | 0 |

| Evaluated Customers | 9,869 |

| Recommendation Rows | 100,000 |



\### Observations



The baseline model achieved better ranking metrics than the personalized model.



However, its recommendation diversity was limited.



Only 122 distinct products appeared across its 100,000 recommendation rows.



This indicates substantial concentration on a small number of globally popular products.



\---



\## 7. Personalized Model Results



Model identifier:



`personalized\_category\_affinity\_v2`



| Metric | Result |

|---|---:|

| Precision@5 | 0.0001621238 |

| Recall@5 | 0.0002533185 |

| NDCG@5 | 0.0002154185 |

| Catalog Coverage | 0.99959558 |

| Catalog Coverage Percentage | 99.96% |

| Availability Violations | 0 |

| Availability Violation Rate | 0 |

| Evaluated Customers | 9,869 |

| Recommendation Rows | 100,000 |



\### Observations



The personalized model achieved much higher catalog coverage.



It recommended 7,415 distinct products across its 100,000 recommendation rows, exposing customers to a much broader range of the eligible catalog.



However, its ranking metrics were lower than those of the baseline.



The model uses individual product-view frequency, so it is primarily oriented toward recommending products the customer has already explored.



It is not an unseen-product discovery algorithm.



\---



\## 8. Side-by-Side Model Comparison



| Metric | Baseline | Personalized | Better Result |

|---|---:|---:|---|

| Precision@5 | 0.000345 | 0.000162 | Baseline |

| Recall@5 | 0.000649 | 0.000253 | Baseline |

| NDCG@5 | 0.000547 | 0.000215 | Baseline |

| Catalog Coverage | 1.64% | 99.96% | Personalized |

| Availability Violations | 0 | 0 | Tie |



\### 8.1 Ranking quality



The baseline achieved higher Precision@5, Recall@5, and NDCG@5.



Its global popularity signal appears more aligned with the observed test-period purchase ground truth in this experiment.



\### 8.2 Catalog diversity



The personalized model achieved nearly complete eligible catalog coverage.



This demonstrates a substantial improvement in the variety of products appearing across customer recommendation lists.



\### 8.3 Availability



Both algorithms recorded zero availability violations in the evaluation.



This indicates that all generated recommendations passed the availability validation applied during the offline evaluation.



\---



\## 9. Interpretation and Business Implications



The results demonstrate a trade-off between purchase relevance and product catalog exposure.



\### Baseline model



Potentially more suitable when the primary objective is to recommend products with stronger aggregate purchase relevance under the current evaluation setup.



Its limitation is low catalog coverage and concentration on popular products.



\### Personalized model



Potentially more suitable when the objective is to expose customers to a broader range of products based on their individual browsing activity.



Its limitation is lower measured purchase relevance and dependence on previously viewed products.



\### Overall conclusion



The personalized model should not automatically be considered superior simply because it has higher catalog coverage.



Similarly, the baseline model should not be considered universally superior simply because it achieved better ranking metrics.



The appropriate model depends on the intended business objective.



A hybrid recommendation approach may help balance relevance and catalog diversity in future versions.



\---



\## 10. Evaluation Limitations



The following limitations must be considered when interpreting the results.



\### 10.1 Synthetic dataset



The dataset is synthetically generated. It may not reproduce the complexity and distribution of real e-commerce customer behaviour.



\### 10.2 Low purchase overlap



The measured Precision@5, Recall@5, and NDCG@5 values are very low.



This indicates limited overlap between the generated recommendation lists and the observed test-period purchase ground truth.



The results should not be presented as evidence of strong commercial recommendation performance.



\### 10.3 Current inventory snapshot



Product availability is evaluated using the current active and in-stock product state rather than inventory at the historical recommendation timestamp.



\### 10.4 Product creation timestamps



Product creation timestamps were not used as historical eligibility filters because the synthetic catalog records were created after the evaluation cutoff.



\### 10.5 Purchase-based relevance



The evaluation measures historical purchase relevance only.



It does not measure clicks, add-to-cart behaviour, customer satisfaction, revenue, or long-term retention.



\### 10.6 No online experiment



The evaluation is offline. No live A/B test was conducted to measure the actual business impact of either recommendation algorithm.



\---



\## 11. Reproducibility and Output Files



The evaluation outputs are maintained separately from the original PostgreSQL database.



Important files:



| File | Purpose |

|---|---|

| `reports/temporal\_split/training\_page\_views.csv` | Training browsing data |

| `reports/temporal\_split/training\_order\_lines.csv` | Training purchase data |

| `reports/temporal\_split/test\_orders.csv` | Test-period orders |

| `reports/temporal\_split/test\_ground\_truth.csv` | Test evaluation ground truth |

| `reports/evaluation/evaluation\_recommendations.csv` | Baseline recommendations |

| `reports/evaluation/personalized\_recommendations.csv` | Personalized recommendations |

| `reports/evaluation/evaluation\_results.json` | Baseline evaluation metrics |

| `reports/evaluation/personalized\_evaluation\_results.json` | Personalized evaluation metrics |

| `reports/evaluation/model\_comparison.json` | Combined model comparison |

| `reports/evaluation/model\_comparison.csv` | Tabular model comparison |



Both recommendation files contain 100,000 rows and were generated separately from the original all-time recommendation records.



\---



\## 12. Future Improvements



Potential improvements include:



1\. Collaborative filtering.

2\. User-user and item-item similarity.

3\. Matrix factorization.

4\. Content-based product recommendations.

5\. Hybrid recommendation models.

6\. Time-decayed browsing preferences.

7\. Purchase-intent prediction.

8\. Improved candidate generation.

9\. Historical inventory snapshots.

10\. Online A/B testing.



\---



\## 13. Final Conclusion



The evaluation establishes a reproducible comparison between a global category-popularity baseline and a customer-specific category-affinity recommender.



The baseline performs better on the measured ranking metrics, while the personalized model provides substantially higher catalog coverage.



Both models satisfy the evaluated availability constraints.



The experiment provides a foundation for further work on hybrid recommendation systems that balance purchase relevance, personalization, and product diversity.



