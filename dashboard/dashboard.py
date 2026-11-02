
import json
import requests
import pandas as pd
import streamlit as st


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="YottaFlex.ai | Recommendation System",
    page_icon="🛍️",
    layout="wide",
)

API_URL = "http://127.0.0.1:8000"


# ============================================================
# HEADER
# ============================================================

st.title("🛍️ YottaFlex.ai")

st.subheader("E-commerce Recommendation & Evaluation Dashboard")

st.markdown(
    """
    Explore customer-specific product recommendations,
    compare recommendation algorithms, and evaluate
    recommendation performance.
    """
)

st.divider()


# ============================================================
# API CONNECTION FUNCTION
# ============================================================

def call_api(endpoint, params=None):

    try:

        response = requests.get(
            f"{API_URL}{endpoint}",
            params=params,
            timeout=15,
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException as error:

        st.error(f"API connection error: {error}")

        return None


# ============================================================
# API AND DATABASE STATUS
# ============================================================

st.header("System Status")

health = call_api("/health")

if health and health.get("database") == "connected":

    st.success("API and PostgreSQL database connected")

else:

    st.warning("API or database connection unavailable")

st.divider()


# ============================================================
# CUSTOMER SELECTION
# ============================================================

st.header("Customer Recommendations")

customer_id = st.number_input(
    "Enter Customer ID",
    min_value=1,
    max_value=20000,
    value=1,
    step=1,
)

model_choice = st.selectbox(
    "Select Recommendation Algorithm",
    options=["baseline", "personalized"],
    format_func=lambda model: (
        "Baseline — Category Popularity"
        if model == "baseline"
        else "Personalized — Customer Product Affinity"
    ),
)


# ============================================================
# CUSTOMER PROFILE
# ============================================================

customer = call_api(f"/customers/{customer_id}")

if customer:

    st.subheader("Customer Profile")

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Customer ID",
            customer["id"],
        )

    with col2:

        st.write("**Customer Name**")

        st.write(
            f"{customer['first_name']} {customer['last_name']}"
        )

    with col3:

        st.write("**Account Status**")

        if customer["is_active"]:
            st.success("Active")
        else:
            st.warning("Inactive")

    st.write(f"**Email:** {customer['email']}")

    st.write(
        f"**Location:** {customer.get('city') or 'N/A'}, "
        f"{customer.get('country') or 'N/A'}"
    )

else:

    st.warning("Customer profile could not be loaded.")

st.divider()


# ============================================================
# GENERATE RECOMMENDATIONS
# ============================================================

if st.button("Generate Recommendations", type="primary"):

    result = call_api(
        f"/recommendations/{customer_id}",
        params={"model": model_choice},
    )

    if result:

        st.subheader(
            f"Recommendations for Customer {customer_id}"
        )

        st.write(
            f"**Algorithm:** {result['model_name']}"
        )

        st.metric(
            "Number of Recommendations",
            result["recommendation_count"],
        )

        recommendation_rows = []

        for item in result["recommendations"]:

            product = item["product"]

            recommendation_rows.append({

                "Rank": item["rank"],

                "Product ID": product["id"],

                "Product Name": product["name"],

                "Category": product["category_name"],

                "Price": float(product["price"]),

                "Stock": product["stock_quantity"],

                "Score": item["score"],

                "Reason": item["reason"],

            })

        if recommendation_rows:

            df = pd.DataFrame(recommendation_rows)

            # --------------------------------------------
            # RECOMMENDATION TABLE
            # --------------------------------------------

            st.subheader("Recommended Products Table")

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
            )

            # --------------------------------------------
            # INDIVIDUAL PRODUCT CARDS
            # --------------------------------------------

            st.subheader("Recommended Product Details")

            for item in result["recommendations"]:

                product = item["product"]

                with st.container(border=True):

                    st.markdown(
                        f"### #{item['rank']} — {product['name']}"
                    )

                    col1, col2, col3 = st.columns(3)

                    with col1:

                        st.write(
                            f"**Product ID:** {product['id']}"
                        )

                        st.write(
                            f"**Category:** "
                            f"{product['category_name'] or 'N/A'}"
                        )

                    with col2:

                        st.write(
                            f"**Price:** {product['price']}"
                        )

                        st.write(
                            f"**Available Stock:** "
                            f"{product['stock_quantity']}"
                        )

                    with col3:

                        st.metric(
                            "Recommendation Score",
                            item["score"],
                        )

                    st.caption(
                        f"Recommendation reason: {item['reason'] or 'N/A'}"
                    )

            # --------------------------------------------
            # CSV EXPORT
            # --------------------------------------------

            csv_data = df.to_csv(
                index=False
            ).encode("utf-8")

            st.download_button(
                label="Download Recommendations as CSV",

                data=csv_data,

                file_name=(
                    f"customer_{customer_id}_{model_choice}.csv"
                ),

                mime="text/csv",
            )

            # --------------------------------------------
            # JSON EXPORT
            # --------------------------------------------

            json_data = json.dumps(
                result,
                indent=4,
                ensure_ascii=False,
            )

            st.download_button(
                label="Download Recommendations as JSON",

                data=json_data,

                file_name=(
                    f"customer_{customer_id}_{model_choice}.json"
                ),

                mime="application/json",
            )

        else:

            st.info("No available recommendations found.")


st.divider()


# ============================================================
# MODEL EVALUATION AND COMPARISON
# ============================================================

st.header("Model Evaluation & Comparison")

evaluation = call_api("/evaluation/models")

if evaluation:

    baseline = evaluation["baseline"]

    personalized = evaluation["personalized"]

    st.write(
        f"**Evaluation Cutoff:** {evaluation['cutoff']}"
    )

    # --------------------------------------------------------
    # COMPARISON TABLE
    # --------------------------------------------------------

    st.subheader("Performance Comparison")

    comparison_data = {

        "Metric": [
            "Precision@5",
            "Recall@5",
            "NDCG@5",
            "Catalog Coverage",
            "Availability Violations",
        ],

        "Baseline": [
            baseline["precision_at_5"],
            baseline["recall_at_5"],
            baseline["ndcg_at_5"],
            baseline["catalog_coverage"],
            baseline["availability_violations"],
        ],

        "Personalized": [
            personalized["precision_at_5"],
            personalized["recall_at_5"],
            personalized["ndcg_at_5"],
            personalized["catalog_coverage"],
            personalized["availability_violations"],
        ],

    }

    comparison_df = pd.DataFrame(comparison_data)

    st.dataframe(
        comparison_df,
        use_container_width=True,
        hide_index=True,
    )

    # --------------------------------------------------------
    # RANKING QUALITY CHART
    # --------------------------------------------------------

    st.subheader("Ranking Quality Comparison")

    ranking_chart = pd.DataFrame(

        {
            "Baseline": [

                baseline["precision_at_5"],

                baseline["recall_at_5"],

                baseline["ndcg_at_5"],

            ],

            "Personalized": [

                personalized["precision_at_5"],

                personalized["recall_at_5"],

                personalized["ndcg_at_5"],

            ],

        },

        index=[
            "Precision@5",
            "Recall@5",
            "NDCG@5",
        ],

    )

    st.bar_chart(ranking_chart)

    # --------------------------------------------------------
    # CATALOG COVERAGE CHART
    # --------------------------------------------------------

    st.subheader("Catalog Coverage Comparison")

    coverage_chart = pd.DataFrame(

        {

            "Baseline": [
                baseline["catalog_coverage"] * 100
            ],

            "Personalized": [
                personalized["catalog_coverage"] * 100
            ],

        },

        index=["Catalog Coverage (%)"],

    )

    st.bar_chart(coverage_chart)

    # --------------------------------------------------------
    # INDIVIDUAL MODEL METRICS
    # --------------------------------------------------------

    st.subheader("Baseline Model")

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Precision@5",
            f"{baseline['precision_at_5']:.6f}",
        )

    with col2:

        st.metric(
            "Recall@5",
            f"{baseline['recall_at_5']:.6f}",
        )

    with col3:

        st.metric(
            "NDCG@5",
            f"{baseline['ndcg_at_5']:.6f}",
        )

    with col4:

        st.metric(
            "Catalog Coverage",
            f"{baseline['catalog_coverage'] * 100:.2f}%",
        )

    st.subheader("Personalized Model")

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Precision@5",
            f"{personalized['precision_at_5']:.6f}",
        )

    with col2:

        st.metric(
            "Recall@5",
            f"{personalized['recall_at_5']:.6f}",
        )

    with col3:

        st.metric(
            "NDCG@5",
            f"{personalized['ndcg_at_5']:.6f}",
        )

    with col4:

        st.metric(
            "Catalog Coverage",
            f"{personalized['catalog_coverage'] * 100:.2f}%",
        )

    # --------------------------------------------------------
    # AVAILABILITY VALIDATION
    # --------------------------------------------------------

    st.subheader("Recommendation Availability")

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "Baseline Availability Violations",
            baseline["availability_violations"],
        )

    with col2:

        st.metric(
            "Personalized Availability Violations",
            personalized["availability_violations"],
        )

    # --------------------------------------------------------
    # EVALUATION EXPLANATION
    # --------------------------------------------------------

    st.caption(
        """
        Precision@5 measures the proportion of relevant products
        among the five recommendations.

        Recall@5 measures how many relevant purchased products
        were successfully recommended.

        NDCG@5 evaluates the ranking quality of recommendations.

        Catalog Coverage measures the proportion of eligible
        products appearing across the recommendation results.

        Availability Violations count recommendations that are
        inactive or out of stock.
        """
    )

else:

    st.warning(
        "Model evaluation results could not be loaded."
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "YottaFlex.ai | E-commerce Recommendation System | "
    "Baseline and Personalized Recommendation Models"
)
