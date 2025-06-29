import pandas as pd
import streamlit as st
from typing import Dict, List, Tuple
import numpy as np

@st.cache_data
def load_clean_data():
    """Load and cache the insurance dataset"""
    try:
        df = pd.read_csv('cleaned_insurance_data.csv')
        return df
    except FileNotFoundError:
        st.error("❌ Insurance data file not found. Please ensure 'cleaned_insurance_data.csv' exists.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        return pd.DataFrame()

def validate_user_input(age: int, income: float, health: str, goal: str) -> Tuple[bool, str]:
    """Validate user input parameters"""
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

def calculate_risk_score(age: int, health: str, income: float) -> float:
    """Calculate risk score based on user profile"""
    risk_score = 0.0
    
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

def get_policy_recommendations_enhanced(age: int, income: float, health: str, goal: str) -> Dict:
    """Enhanced recommendation algorithm with multiple factors"""
    df = load_clean_data()
    
    if df.empty:
        return {"error": "Unable to load insurance data"}
    
    # Calculate risk score
    risk_score = calculate_risk_score(age, income, health)
    
    # Filter policies based on age range and coverage
    age_filtered = df[
        (df['Age'] >= age - 10) & 
        (df['Age'] <= age + 10) & 
        (df['Coverage_Lakhs'] >= 10)
    ].copy()
    
    if age_filtered.empty:
        # Fallback to broader age range
        age_filtered = df[df['Coverage_Lakhs'] >= 10].copy()
    
    # Health-based filtering
    if health.lower() == 'poor':
        health_policies = ['Health', 'Comprehensive']
        age_filtered = age_filtered[age_filtered['Policy_Type'].isin(health_policies)]
    
    # Goal-based recommendations
    goal_lower = goal.lower()
    if 'family' in goal_lower or 'dependent' in goal_lower:
        age_filtered = age_filtered[age_filtered['Coverage_Lakhs'] >= 15]
    elif 'critical' in goal_lower or 'serious' in goal_lower:
        preferred_types = ['Health', 'Comprehensive']
        age_filtered = age_filtered[age_filtered['Policy_Type'].isin(preferred_types)]
    elif 'save' in goal_lower or 'investment' in goal_lower:
        preferred_types = ['Term Life', 'Comprehensive']
        age_filtered = age_filtered[age_filtered['Policy_Type'].isin(preferred_types)]
    
    if age_filtered.empty:
        return {"error": "No suitable policies found for your profile. Please consult with an insurance advisor."}
    
    # Sort by multiple factors
    age_filtered['age_diff'] = abs(age_filtered['Age'] - age)
    age_filtered['affordability_score'] = age_filtered['Premium_INR'] / (income * 1000) * 12  # Monthly premium as % of income
    
    # Prioritize affordable and age-appropriate policies
    recommended = age_filtered.sort_values(['affordability_score', 'age_diff', 'Coverage_Lakhs'], 
                                         ascending=[True, True, False])
    
    top_policies = recommended.head(5)
    best_policy = recommended.iloc[0]
    
    return {
        "best_policy": best_policy,
        "top_policies": top_policies,
        "risk_score": risk_score,
        "total_available": len(age_filtered)
    }

def format_currency(amount: float) -> str:
    """Format currency in Indian format"""
    if amount >= 10000000:  # 1 crore
        return f"₹{amount/10000000:.1f}Cr"
    elif amount >= 100000:  # 1 lakh
        return f"₹{amount/100000:.1f}L"
    else:
        return f"₹{amount:,.0f}"

def get_faq_categories() -> Dict[str, List[Dict[str, str]]]:
    """Get categorized FAQ data"""
    return {
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
        ],
        "Claims & Benefits": [
            {
                "question": "How to claim insurance?",
                "answer": "Contact your insurer immediately, submit required documents (medical bills, discharge summary, claim form), and follow up regularly. Most claims are processed within 30 days."
            },
            {
                "question": "What is waiting period?",
                "answer": "Waiting period is the time you must wait before claiming certain benefits. It's typically 30 days for accidents and 2-4 years for pre-existing diseases."
            },
            {
                "question": "Can I have multiple policies?",
                "answer": "Yes, you can have multiple life insurance policies. For health insurance, you can claim from multiple policies but total claim cannot exceed actual expenses."
            }
        ]
    }
