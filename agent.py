import streamlit as st
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from utils import get_policy_recommendations_enhanced, calculate_risk_score
import os

# Load TinyLlama Model & Tokenizer with error handling
@st.cache_resource
def load_tinyllama_pipeline():
    """Load TinyLlama model with proper error handling"""
    try:
        model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
        
        with st.spinner("🤖 Loading AI model... This may take a moment..."):
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            
            # Add padding token if not present
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                device_map="auto",
                torch_dtype="auto"
            )
            
            llm_pipeline = pipeline(
                "text-generation", 
                model=model, 
                tokenizer=tokenizer,
                return_full_text=False
            )
            
        return llm_pipeline
        
    except Exception as e:
        st.error(f"❌ Error loading AI model: {str(e)}")
        st.info("💡 The app will continue with basic recommendations without AI reasoning.")
        return None

# Load the model only once
llm_pipeline = load_tinyllama_pipeline()

def generate_llm_reasoning(age: int, income: float, health: str, goal: str, recommended_policy: dict, risk_score: float) -> str:
    """Generate AI-powered reasoning for policy recommendation"""
    
    if llm_pipeline is None:
        return f"""
        Based on your profile analysis:
        
        🎯 **Why this policy fits you:**
        - Age: {age} years matches the typical age group for {recommended_policy.get('Policy_Type', 'this policy')}
        - Coverage: ₹{recommended_policy.get('Coverage_Lakhs', 'N/A')} lakhs provides adequate protection
        - Premium: ₹{recommended_policy.get('Premium_INR', 'N/A')} is within reasonable range for your income
        - Risk Score: {risk_score}/10 indicates your risk profile
        
        This recommendation is based on data analysis of similar customer profiles.
        """
    
    try:
        prompt = f"""<|system|>
You are an expert Indian insurance advisor. Provide clear, concise advice.

<|user|>
Customer Profile:
- Age: {age} years
- Annual Income: ₹{income} LPA  
- Health: {health}
- Goal: {goal}
- Risk Score: {risk_score}/10

Recommended Policy: {recommended_policy.get('Policy_Type')} with ₹{recommended_policy.get('Coverage_Lakhs')} lakhs coverage for ₹{recommended_policy.get('Premium_INR')} premium.

Explain in 2-3 sentences why this policy is suitable. Focus on benefits and value.

<|assistant|>"""

        with st.spinner("🤖 AI is analyzing your profile..."):
            output = llm_pipeline(
                prompt,
                max_new_tokens=100,
                do_sample=True,
                temperature=0.7,
                top_k=50,
                top_p=0.9,
                repetition_penalty=1.1
            )
        
        reasoning = output[0]['generated_text'].strip()
        
        # Clean up the response
        if reasoning:
            return f"🤖 **AI Analysis:** {reasoning}"
        else:
            return "AI analysis completed. This policy matches your profile requirements."
            
    except Exception as e:
        st.warning(f"⚠️ AI reasoning temporarily unavailable: {str(e)}")
        return f"""
        **Profile Analysis:**
        This {recommended_policy.get('Policy_Type')} policy is recommended based on your age ({age}), 
        health status ({health}), and financial profile (₹{income} LPA income).
        """

def get_policy_recommendation_with_ai(age: int, income: float, health: str, goal: str) -> dict:
    """Get policy recommendation with AI reasoning"""
    
    # Get enhanced recommendations
    recommendation_data = get_policy_recommendations_enhanced(age, income, health, goal)
    
    if "error" in recommendation_data:
        return recommendation_data
    
    best_policy = recommendation_data["best_policy"]
    
    # Generate AI reasoning
    ai_reasoning = generate_llm_reasoning(
        age, income, health, goal, 
        best_policy, recommendation_data["risk_score"]
    )
    
    recommendation_data["ai_reasoning"] = ai_reasoning
    
    return recommendation_data

def answer_insurance_question(question: str) -> str:
    """Answer insurance-related questions using AI"""
    
    if llm_pipeline is None:
        return "❌ AI assistant is currently unavailable. Please try again later or contact our support team."
    
    if not question.strip():
        return "❓ Please ask a specific insurance-related question."
    
    try:
        prompt = f"""<|system|>
You are a helpful Indian insurance expert. Answer questions clearly and concisely in 2-3 sentences. Focus on practical advice for Indian customers.

<|user|>
{question}

<|assistant|>"""

        with st.spinner("🤖 AI is thinking..."):
            output = llm_pipeline(
                prompt,
                max_new_tokens=80,
                do_sample=True,
                temperature=0.6,
                top_k=40,
                top_p=0.8,
                repetition_penalty=1.1
            )
        
        answer = output[0]['generated_text'].strip()
        return answer if answer else "I'd be happy to help with your insurance question. Could you please be more specific?"
        
    except Exception as e:
        return f"⚠️ Sorry, I'm having trouble processing your question right now. Error: {str(e)}"

def calculate_premium_estimate(age: int, coverage_lakhs: int, policy_type: str, health: str) -> dict:
    """Calculate estimated premium based on various factors"""
    
    base_rates = {
        "Term Life": 0.5,      # ₹500 per lakh per year
        "Health": 0.8,         # ₹800 per lakh per year  
        "Comprehensive": 1.2,  # ₹1200 per lakh per year
        "Accident Cover": 0.3  # ₹300 per lakh per year
    }
    
    base_rate = base_rates.get(policy_type, 0.8)
    
    # Age multiplier
    if age < 25:
        age_multiplier = 0.8
    elif age < 35:
        age_multiplier = 1.0
    elif age < 45:
        age_multiplier = 1.3
    elif age < 55:
        age_multiplier = 1.7
    else:
        age_multiplier = 2.5
    
    # Health multiplier
    health_multiplier = {"Good": 1.0, "Average": 1.3, "Poor": 2.0}
    
    estimated_premium = (
        coverage_lakhs * 
        base_rate * 
        age_multiplier * 
        health_multiplier.get(health, 1.0) * 
        1000  # Convert to rupees
    )
    
    return {
        "estimated_premium": round(estimated_premium),
        "base_rate": base_rate,
        "age_factor": age_multiplier,
        "health_factor": health_multiplier.get(health, 1.0)
    }
