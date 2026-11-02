\# YottaFlex.ai — Recommendation Algorithm Explanation



\## 1. Introduction



YottaFlex.ai implements two recommendation algorithms for an e-commerce platform:



1\. Baseline Category-Popularity Recommendation

2\. Personalized Category-Affinity Recommendation



Both algorithms generate up to five product recommendations for each customer using information from the training period.



The objective is to compare a popularity-based approach with a customer-specific browsing-affinity approach.



\---



\## 2. Data Used by the Algorithms



The recommendation engine uses the following data:



| Data | Purpose |

|---|---|

| Customers | Identifies recommendation recipients |

| Products | Provides product information |

| Categories | Groups products into product categories |

| Page Views | Captures customer browsing behaviour |

| Orders | Identifies previously purchased products |

| Product Inventory | Determines current product availability |



\### Training-period data



The chronological cutoff is:



`2026-07-01T00:00:00+05:30`



Only browsing and purchase history before this cutoff is used to construct recommendation history.



Test-period purchases are reserved for evaluation.



\---



\## 3. Algorithm 1 — Baseline Category-Popularity Recommendation



\### 3.1 Objective



The baseline model recommends popular products from a customer's preferred category.



It uses global product popularity rather than individual product preferences.



Model identifier:



`category\_affinity\_train\_only`



\### 3.2 Workflow



\*\*Step 1: Identify customer browsing history\*\*



Retrieve the customer's page-view activity from the training dataset.



\*\*Step 2: Determine preferred category\*\*



Calculate the customer's browsing frequency across product categories.



The category with the highest browsing activity is selected as the preferred category.



\*\*Step 3: Calculate product popularity\*\*



Calculate the global training-period page-view count for each product.



A higher page-view count indicates greater popularity in the training data.



\*\*Step 4: Rank candidate products\*\*



Prioritize popular products belonging to the customer's preferred category.



Use globally popular products as fallback candidates when the preferred category does not provide enough eligible products.



\*\*Step 5: Apply eligibility filters\*\*



Exclude:



\- Products previously purchased by the customer.

\- Inactive products.

\- Products with zero available stock.



\*\*Step 6: Generate recommendations\*\*



Return up to five products, ordered by their recommendation ranking.



\### 3.3 Scoring



The baseline recommendation score is the global training-period page-view count of a product.



Conceptually:



`Score(product) = GlobalTrainingPageViewCount(product)`



Products with higher popularity scores receive higher ranking priority.



\### 3.4 Characteristics



\- Uses customer category preference.

\- Uses global product popularity.

\- Does not calculate individual product-view affinity.

\- Can recommend the same popular products to many customers.

\- Provides a simple baseline for evaluating personalization.



\---



\## 4. Algorithm 2 — Personalized Category-Affinity Recommendation



\### 4.1 Objective



The personalized model generates recommendations using each customer's individual product-view frequency.



It prioritizes products that the customer has previously viewed, especially those within the customer's preferred category.



Model identifier:



`personalized\_category\_affinity\_v2`



\### 4.2 Workflow



\*\*Step 1: Retrieve individual browsing history\*\*



Retrieve the customer's product-view activity from the training dataset.



\*\*Step 2: Determine preferred category\*\*



Calculate the customer's browsing activity across product categories.



Select the category with the highest customer browsing frequency.



\*\*Step 3: Calculate individual product affinity\*\*



Count how many times the customer viewed each product.



A product viewed more frequently by an individual customer receives a higher personal affinity score.



\*\*Step 4: Prioritize products\*\*



Rank personally viewed products, prioritizing products belonging to the preferred category.



Use other personally viewed products as fallback candidates when necessary.



Category popularity and global popularity are used as additional ranking considerations and fallback or tie-breaking signals.



\*\*Step 5: Apply eligibility filters\*\*



Exclude:



\- Products previously purchased by the customer.

\- Inactive products.

\- Products with zero available stock.



\*\*Step 6: Generate recommendations\*\*



Return up to five eligible products based on individual product-view frequency and category affinity.



\### 4.3 Scoring



The personalized recommendation score is the individual customer's product-view count.



Conceptually:



`Score(customer, product) = CustomerProductViewCount(customer, product)`



For example:



| Customer | Product | Individual Views | Score |

|---|---|---:|---:|

| Customer A | Product 101 | 5 | 5 |

| Customer A | Product 102 | 3 | 3 |

| Customer A | Product 103 | 1 | 1 |



A higher individual view count indicates stronger observed browsing affinity.



\### 4.4 Characteristics



\- Uses individual customer browsing behaviour.

\- Prioritizes previously viewed products.

\- Considers preferred category.

\- Provides broader product catalog exposure than the baseline in this evaluation.

\- Is conversion-oriented rather than unseen-product discovery-oriented.



\---



\## 5. Common Recommendation Filtering



Both algorithms apply common product eligibility rules.



\### Previously purchased products



Products already purchased by the customer are excluded from recommendation candidates.



This prevents the system from repeatedly recommending products that the customer has already bought.



\### Product availability



Only products satisfying both conditions are eligible:



\- Product is active.

\- Stock quantity is greater than zero.



These checks use the current product inventory snapshot.



\### Recommendation count



The target recommendation count is five products per customer.



If fewer than five eligible products are available, the system may return fewer recommendations.



\---



\## 6. Algorithm Comparison



| Feature | Baseline | Personalized |

|---|---|---|

| Preferred category | Yes | Yes |

| Global popularity | Primary score | Supporting ranking signal |

| Individual product views | No | Primary score |

| Previously purchased filtering | Yes | Yes |

| Availability filtering | Yes | Yes |

| Target recommendations | 5 | 5 |

| Personalization level | Category-level | Product-level |



\---



\## 7. Evaluation Results



Both models were evaluated against the same chronological test dataset.



| Metric | Baseline | Personalized |

|---|---:|---:|

| Precision@5 | 0.000345 | 0.000162 |

| Recall@5 | 0.000649 | 0.000253 |

| NDCG@5 | 0.000547 | 0.000215 |

| Catalog Coverage | 1.64% | 99.96% |

| Availability Violations | 0 | 0 |



\### Interpretation



The baseline model performs better on the three ranking-quality metrics in this experiment.



The personalized model provides significantly greater catalog coverage.



This demonstrates that increasing recommendation diversity does not automatically improve purchase relevance.



Neither model is universally better; the choice depends on the business objective.



\---



\## 8. Known Limitations



1\. Both algorithms are heuristic-based and do not use trained machine-learning ranking models.

2\. The personalized algorithm relies on previously viewed products, limiting its ability to discover completely unseen products.

3\. Synthetic browsing and purchasing behaviour may not represent real customer behaviour.

4\. Current product inventory is used rather than historical inventory at recommendation time.

5\. The algorithms do not incorporate explicit ratings, customer satisfaction, or product review sentiment.



\---



\## 9. Potential Improvements



Future versions could introduce:



\- Collaborative filtering.

\- User-user similarity.

\- Item-item similarity.

\- Matrix factorization.

\- Content-based recommendation.

\- Hybrid recommendation models.

\- Product embeddings.

\- Time-decayed browsing preferences.

\- Purchase-intent prediction.

\- Online recommendation feedback.



\---



\## 10. Conclusion



The two algorithms establish a comparative recommendation framework.



The baseline model uses category affinity and global popularity, while the personalized model uses individual product-view frequency and category preference.



The evaluation highlights the trade-off between ranking relevance and catalog coverage, providing a foundation for future hybrid recommendation approaches.



