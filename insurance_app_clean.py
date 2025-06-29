import streamlit as st
import pandas as pd
from datetime import datetime
import base64
import io

# Page configuration
st.set_page_config(
    page_title="Insurance Policy Optimizer", 
    page_icon="🛡️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #2E86AB 0%, #A23B72 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f0f8ff;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #2E86AB;
    }
    .policy-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Load insurance data
@st.cache_data
def load_clean_data():
    try:
        df = pd.read_csv('cleaned_insurance_data.csv')
        return df
    except FileNotFoundError:
        st.error("Insurance data file not found. Please ensure 'cleaned_insurance_data.csv' exists.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()

def validate_user_input(age, income, health, goal):
    try:
        age = int(age)
        income = float(income)
        
        if age < 18 or age > 100:
            return False, "Age must be between 18 and 100 years."
        
        if income <= 0 or income > 1000:
            return False, "Annual income must be between 1 and 1000 LPA."
        
        if health not in ["Good", "Average", "Poor"]:
            return False, "Please select a valid health status."
        
        if not goal.strip():
            return False, "Please provide your insurance goal."
        
        if len(goal.strip()) < 5:
            return False, "Please provide a more detailed insurance goal (at least 5 characters)."
        
        return True, "Valid input"
    except (ValueError, TypeError):
        return False, "Please enter valid numeric values for age and income."

def calculate_risk_score(age, health, income):
    risk_score = 0.0
    
    # Convert inputs to proper types
    age = int(age)
    income = float(income)
    
    # Age factor
    if age < 25:
        risk_score += 1.0
    elif age < 35:
        risk_score += 1.5
    elif age < 50:
        risk_score += 2.0
    else:
        risk_score += 3.0
    
    # Health factor
    health_multiplier = {"Good": 1.0, "Average": 1.5, "Poor": 2.5}
    risk_score *= health_multiplier.get(health, 1.0)
    
    # Income factor (lower income = higher risk)
    if income < 5:
        risk_score *= 1.3
    elif income < 15:
        risk_score *= 1.1
    else:
        risk_score *= 0.9
    
    return round(risk_score, 2)

def get_policy_recommendations(age, income, health, goal):
    df = load_clean_data()
    
    if df.empty:
        return {"error": "Unable to load insurance data"}
    
    # Calculate risk score
    risk_score = calculate_risk_score(age, health, income)
    
    # Filter policies based on age range and coverage
    age_filtered = df[
        (df['Age'] >= age - 5) & 
        (df['Age'] <= age + 5)
    ]
    
    # Health-based filtering
    if health == "Poor":
        # For poor health, recommend comprehensive coverage
        health_filtered = age_filtered[age_filtered['Policy_Type'].isin(['Health', 'Comprehensive'])]
    elif health == "Good":
        # For good health, all options available
        health_filtered = age_filtered
    else:
        # For average health, exclude high-risk policies
        health_filtered = age_filtered[age_filtered['Policy_Type'].isin(['Health', 'Term Life', 'Comprehensive'])]
    
    if health_filtered.empty:
        health_filtered = age_filtered  # Fallback to age-filtered data
    
    # Sort by value (coverage/premium ratio) and premium
    if not health_filtered.empty:
        health_filtered = health_filtered.sort_values(
            ['Coverage_Lakhs', 'Premium_INR'], 
            ascending=[False, True]
        )
        
        top_policies = health_filtered.head(3).to_dict('records')
        
        return {
            "policies": top_policies,
            "risk_score": risk_score,
            "total_policies_found": len(health_filtered),
            "recommendation_basis": f"Based on age {age}, {health.lower()} health, and income ₹{income}L"
        }
    else:
        return {"error": "No suitable policies found for your profile"}

def format_currency(amount):
    if amount >= 10000000:  # 1 crore
        return f"₹{amount/10000000:.1f}Cr"
    elif amount >= 100000:  # 1 lakh
        return f"₹{amount/100000:.1f}L"
    else:
        return f"₹{amount:,.0f}"

def generate_ai_reasoning(age, income, health, goal, recommended_policy, risk_score):
    return f"""
    Based on your profile analysis:
    
    **Why this policy fits you:**
    - Age: {age} years matches the typical age group for {recommended_policy.get('Policy_Type', 'this policy')}
    - Coverage: ₹{recommended_policy.get('Coverage_Lakhs', 'N/A')} lakhs provides adequate protection
    - Premium: ₹{recommended_policy.get('Premium_INR', 'N/A')} is within reasonable range for your income
    - Risk Score: {risk_score}/10 indicates your risk profile
    
    This recommendation is based on data analysis of similar customer profiles in our database.
    """

# Initialize session state
if 'recommendation_data' not in st.session_state:
    st.session_state.recommendation_data = None
if 'user_profile' not in st.session_state:
    st.session_state.user_profile = None

# Header
st.markdown("""
<div class="main-header">
    <h1>🛡️ Insurance Policy Optimizer</h1>
    <p>AI-Powered Personalized Insurance Recommendations</p>
</div>
""", unsafe_allow_html=True)

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.selectbox(
    "Choose a section:",
    ["Get Recommendation", "Policy Comparison", "Insurance FAQ", "Market Insights"]
)

if page == "Get Recommendation":
    st.header("Get Your Personalized Insurance Recommendation")
    
    # User input form with better validation
    with st.form(key='user_input_form'):
        col1, col2 = st.columns(2)
        
        with col1:
            age = st.slider("Your Age", 18, 80, 30, help="Your current age affects premium and policy options")
            health = st.selectbox(
                "Health Status", 
                ["Good", "Average", "Poor"],
                help="Your current health condition affects policy eligibility and premiums"
            )
        
        with col2:
            income = st.number_input(
                "Annual Income (LPA)", 
                min_value=1, max_value=500, value=10, step=1,
                help="Your annual income in Lakhs Per Annum"
            )
            goal = st.text_area(
                "Insurance Goal", 
                placeholder="e.g., Family protection, Health coverage, Investment planning",
                help="Describe what you want to achieve with insurance"
            )
        
        submit_button = st.form_submit_button(label='Get Recommendation', use_container_width=True)
    
    if submit_button:
        # Validate input
        is_valid, validation_message = validate_user_input(age, income, health, goal)
        
        if is_valid:
            # Store user profile
            st.session_state.user_profile = {
                'age': age,
                'income': income,
                'health': health,
                'goal': goal
            }
            
            # Get recommendations
            with st.spinner("Analyzing your profile and finding the best policies..."):
                recommendation_data = get_policy_recommendations(age, income, health, goal)
                st.session_state.recommendation_data = recommendation_data
            
            if "error" in recommendation_data:
                st.error(recommendation_data["error"])
            else:
                st.success("Found personalized recommendations for you!")
                
                # Display risk score
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Risk Score", f"{recommendation_data['risk_score']}/10")
                with col2:
                    st.metric("Policies Found", recommendation_data['total_policies_found'])
                with col3:
                    risk_level = "Low" if recommendation_data['risk_score'] <= 3 else "Medium" if recommendation_data['risk_score'] <= 6 else "High"
                    st.metric("Risk Level", risk_level)
                
                # Display recommendations
                st.subheader("Recommended Policies")
                
                for i, policy in enumerate(recommendation_data['policies']):
                    with st.expander(f"Option {i+1}: {policy['Policy_Type']} - ₹{policy['Coverage_Lakhs']}L Coverage", expanded=(i==0)):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**Coverage:** ₹{policy['Coverage_Lakhs']} Lakhs")
                            st.write(f"**Annual Premium:** ₹{policy['Premium_INR']:,.0f}")
                            st.write(f"**Policy Type:** {policy['Policy_Type']}")
                            st.write(f"**Target Age:** {policy['Age']} years")
                        
                        with col2:
                            # Value metrics
                            value_ratio = policy['Coverage_Lakhs'] / policy['Premium_INR'] * 100000
                            st.metric("Value Ratio", f"{value_ratio:.2f}")
                            st.metric("Premium per Lakh", f"₹{policy['Premium_INR']/policy['Coverage_Lakhs']:,.0f}")
                            
                            if i == 0:  # Best recommendation
                                best_policy = policy
                                
                                # AI Reasoning
                                ai_reasoning = generate_ai_reasoning(
                                    age, income, health, goal, 
                                    best_policy, recommendation_data["risk_score"]
                                )
                                st.markdown("**AI Analysis:**")
                                st.info(ai_reasoning)
        else:
            st.error(validation_message)

elif page == "Policy Comparison":
    st.header("⚖️ Policy Comparison Tool")
    st.write("Compare different insurance policies to find the best fit for your needs")
    
    df = load_clean_data()
    if not df.empty:
        # Policy selection
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Select First Policy")
            policy_types_1 = st.selectbox("Policy Type", df['Policy_Type'].unique(), key="policy1")
            filtered_df_1 = df[df['Policy_Type'] == policy_types_1]
            
            if not filtered_df_1.empty:
                policy_1_options = [f"{row['Policy_Type']} - ₹{row['Coverage_Lakhs']}L (₹{row['Premium_INR']})" 
                                  for _, row in filtered_df_1.iterrows()]
                selected_1 = st.selectbox("Choose Policy", policy_1_options, key="select1")
                policy_1_idx = policy_1_options.index(selected_1)
                policy_1 = filtered_df_1.iloc[policy_1_idx]
        
        with col2:
            st.subheader("Select Second Policy")
            policy_types_2 = st.selectbox("Policy Type", df['Policy_Type'].unique(), key="policy2")
            filtered_df_2 = df[df['Policy_Type'] == policy_types_2]
            
            if not filtered_df_2.empty:
                policy_2_options = [f"{row['Policy_Type']} - ₹{row['Coverage_Lakhs']}L (₹{row['Premium_INR']})" 
                                  for _, row in filtered_df_2.iterrows()]
                selected_2 = st.selectbox("Choose Policy", policy_2_options, key="select2")
                policy_2_idx = policy_2_options.index(selected_2)
                policy_2 = filtered_df_2.iloc[policy_2_idx]
        
        # Comparison table
        if 'policy_1' in locals() and 'policy_2' in locals():
            st.subheader("Detailed Comparison")
            
            comparison_data = {
                "Feature": ["Policy Type", "Coverage Amount", "Annual Premium", "Age Group", "Health Requirements"],
                "Policy 1": [
                    policy_1['Policy_Type'],
                    f"₹{policy_1['Coverage_Lakhs']} Lakhs",
                    f"₹{policy_1['Premium_INR']:,.0f}",
                    f"{policy_1['Age']} years",
                    "Standard"
                ],
                "Policy 2": [
                    policy_2['Policy_Type'],
                    f"₹{policy_2['Coverage_Lakhs']} Lakhs", 
                    f"₹{policy_2['Premium_INR']:,.0f}",
                    f"{policy_2['Age']} years",
                    "Standard"
                ]
            }
            
            comparison_df = pd.DataFrame(comparison_data)
            st.table(comparison_df)
            
            # Value analysis
            st.subheader("Value Analysis")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                premium_diff = policy_2['Premium_INR'] - policy_1['Premium_INR']
                st.metric("Premium Difference", f"₹{premium_diff:,.0f}", 
                         delta=f"Policy 2 {'higher' if premium_diff > 0 else 'lower'}")
            
            with col2:
                coverage_diff = policy_2['Coverage_Lakhs'] - policy_1['Coverage_Lakhs']
                st.metric("Coverage Difference", f"₹{coverage_diff} Lakhs",
                         delta=f"Policy 2 {'higher' if coverage_diff > 0 else 'lower'}")
            
            with col3:
                value_ratio_1 = policy_1['Coverage_Lakhs'] / policy_1['Premium_INR'] * 100000
                value_ratio_2 = policy_2['Coverage_Lakhs'] / policy_2['Premium_INR'] * 100000
                better_value = "Policy 1" if value_ratio_1 > value_ratio_2 else "Policy 2"
                st.metric("Better Value", better_value)
            
            # Recommendation
            if premium_diff < 0 and coverage_diff >= 0:
                st.success("🎯 Policy 2 offers better or equal coverage at a lower premium!")
            elif premium_diff > 0 and coverage_diff > 0:
                st.info(f"Policy 2 costs ₹{premium_diff:,.0f} more but provides ₹{coverage_diff} Lakhs additional coverage")
            else:
                st.warning("Consider your specific needs when choosing between these policies")
    
    else:
        st.error("Unable to load policy data for comparison.")

elif page == "Insurance FAQ":
    st.header("Frequently Asked Questions")
    
    # FAQ sections
    faq_categories = {
        "Basic Insurance": [
            {
                "question": "What is term insurance?",
                "answer": "Term insurance provides life coverage for a specific period. It's pure protection with no investment component, making it affordable for high coverage amounts."
            },
            {
                "question": "What is health insurance?",
                "answer": "Health insurance covers medical expenses including hospitalization, surgery, and treatments. It protects you from high healthcare costs in India."
            },
            {
                "question": "What is comprehensive insurance?",
                "answer": "Comprehensive insurance combines multiple coverages like life, health, and accident protection in one policy, offering complete family protection."
            }
        ],
        "Policy Selection": [
            {
                "question": "How much coverage do I need?",
                "answer": "Generally, life coverage should be 10-15 times your annual income. For health insurance, start with ₹5-10 lakhs and increase based on family size and medical history."
            },
            {
                "question": "When should I buy insurance?",
                "answer": "Buy insurance as early as possible. Premiums are lower when you're young and healthy. Don't wait for life events like marriage or having children."
            },
            {
                "question": "What factors affect premium?",
                "answer": "Age, health status, lifestyle habits, coverage amount, policy type, and family medical history are key factors that determine your insurance premium."
            }
        ]
    }
    
    for category, faqs in faq_categories.items():
        st.subheader(category)
        for faq in faqs:
            with st.expander(faq["question"]):
                st.write(faq["answer"])

elif page == "Market Insights":
    st.header("📊 Insurance Market Insights")
    st.write("Analysis of insurance trends and market data")
    
    df = load_clean_data()
    if not df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            # Policy type distribution
            policy_distribution = df['Policy_Type'].value_counts()
            st.subheader("Policy Type Distribution")
            st.bar_chart(policy_distribution)
        
        with col2:
            # Age vs Premium trends
            age_premium = df.groupby('Age')['Premium_INR'].mean().reset_index()
            st.subheader("Average Premium by Age")
            st.line_chart(age_premium.set_index('Age'))
        
        # Coverage analysis
        st.subheader("Coverage Analysis")
        coverage_stats = df.groupby('Policy_Type').agg({
            'Coverage_Lakhs': ['mean', 'min', 'max'],
            'Premium_INR': 'mean'
        }).round(2)
        
        st.dataframe(coverage_stats, use_container_width=True)
    else:
        st.error("Unable to load market data for insights.")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem 0;">
    <p>Insurance Policy Optimizer - Making insurance accessible and understandable for everyone</p>
    <p>Analyze • Compare • Protect • Save</p>
</div>
""", unsafe_allow_html=True)