import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from agent import get_policy_recommendation_with_ai, answer_insurance_question, calculate_premium_estimate
from utils import validate_user_input, format_currency, get_faq_categories, load_clean_data
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
import base64
import io
import datetime

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
st.sidebar.title("🧭 Navigation")
page = st.sidebar.selectbox(
    "Choose a section:",
    ["🏠 Get Recommendation", "📊 Policy Comparison", "💰 Premium Calculator", "❓ Insurance FAQ", "📈 Market Insights"]
)

if page == "🏠 Get Recommendation":
    st.header("🎯 Get Your Personalized Insurance Recommendation")
    
    # User input form with better validation
    with st.form(key='user_input_form'):
        col1, col2 = st.columns(2)
        
        with col1:
            age = st.slider("👤 Your Age", 18, 80, 30, help="Your current age affects premium and policy options")
            health = st.selectbox(
                "🏥 Health Status", 
                ["Good", "Average", "Poor"],
                help="Self-assessment of your current health condition"
            )
        
        with col2:
            income = st.number_input(
                "💰 Annual Income (₹ in LPA)", 
                min_value=1.0, 
                max_value=1000.0, 
                value=8.0, 
                step=0.5,
                help="Your annual income in Lakhs Per Annum"
            )
            goal = st.text_area(
                "🎯 Insurance Goal", 
                placeholder="E.g., Family protection, Critical illness cover, Retirement planning, Child education...",
                help="Describe what you want to achieve with insurance"
            )
        
        submit_button = st.form_submit_button(label='✅ Get My AI-Powered Recommendation', use_container_width=True)
    
    if submit_button:
        # Validate input
        is_valid, validation_message = validate_user_input(age, income, health, goal)
        
        if not is_valid:
            st.error(f"❌ {validation_message}")
        else:
            # Store user profile
            st.session_state.user_profile = {
                'age': age, 'income': income, 'health': health, 'goal': goal
            }
            
            with st.spinner("🔍 AI is analyzing your profile and market data..."):
                recommendation_data = get_policy_recommendation_with_ai(age, income, health, goal)
                st.session_state.recommendation_data = recommendation_data
            
            if "error" in recommendation_data:
                st.error(f"❌ {recommendation_data['error']}")
            else:
                st.success("🎉 Here's Your AI-Powered Insurance Recommendation!")
                
                # Display recommendation
                best_policy = recommendation_data["best_policy"]
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Policy Type", best_policy['Policy_Type'])
                with col2:
                    st.metric("Coverage", f"₹{best_policy['Coverage_Lakhs']}L")
                with col3:
                    st.metric("Premium", format_currency(best_policy['Premium_INR']))
                with col4:
                    st.metric("Risk Score", f"{recommendation_data['risk_score']}/10")
                
                # AI Reasoning
                st.info(recommendation_data["ai_reasoning"])
                
                # Top recommendations chart
                top_policies = recommendation_data["top_policies"]
                
                fig = px.bar(
                    top_policies, 
                    x='Policy_Type', 
                    y='Premium_INR',
                    color='Coverage_Lakhs',
                    title='Top 5 Recommended Policies - Premium vs Coverage',
                    labels={'Premium_INR': 'Annual Premium (₹)', 'Coverage_Lakhs': 'Coverage (Lakhs)'}
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
                
                # Generate and offer PDF download
                if st.button("📄 Download Detailed Report", use_container_width=True):
                    pdf_data = generate_detailed_pdf_report(
                        st.session_state.user_profile, 
                        recommendation_data
                    )
                    
                    b64_pdf = base64.b64encode(pdf_data).decode('utf-8')
                    href = f'<a href="data:application/pdf;base64,{b64_pdf}" download="Insurance_Recommendation_Report.pdf">📄 Click here to download your report</a>'
                    st.markdown(href, unsafe_allow_html=True)

elif page == "📊 Policy Comparison":
    st.header("📊 Compare Insurance Policies")
    
    if st.session_state.recommendation_data is None:
        st.warning("⚠️ Please get your recommendation first to see detailed comparisons.")
        st.info("👈 Go to 'Get Recommendation' section to start.")
    else:
        recommendation_data = st.session_state.recommendation_data
        top_policies = recommendation_data["top_policies"]
        
        st.subheader("📈 Policy Comparison Dashboard")
        
        # Comparison metrics
        col1, col2 = st.columns(2)
        
        with col1:
            # Premium comparison
            fig_premium = px.pie(
                top_policies, 
                values='Premium_INR', 
                names='Policy_Type',
                title='Premium Distribution Among Top Policies'
            )
            st.plotly_chart(fig_premium, use_container_width=True)
        
        with col2:
            # Coverage comparison
            fig_coverage = px.scatter(
                top_policies, 
                x='Coverage_Lakhs', 
                y='Premium_INR',
                color='Policy_Type',
                size='Coverage_Lakhs',
                title='Coverage vs Premium Analysis'
            )
            st.plotly_chart(fig_coverage, use_container_width=True)
        
        # Detailed comparison table
        st.subheader("📋 Detailed Policy Comparison")
        
        comparison_df = top_policies[['Policy_Type', 'Coverage_Lakhs', 'Premium_INR', 'Age']].copy()
        comparison_df['Value Score'] = comparison_df['Coverage_Lakhs'] / (comparison_df['Premium_INR'] / 1000)
        comparison_df['Value Score'] = comparison_df['Value Score'].round(2)
        
        st.dataframe(
            comparison_df.style.highlight_max(axis=0, subset=['Coverage_Lakhs', 'Value Score']).highlight_min(axis=0, subset=['Premium_INR']),
            use_container_width=True
        )

elif page == "💰 Premium Calculator":
    st.header("💰 Premium Calculator")
    
    st.info("🧮 Calculate estimated premiums for different insurance scenarios")
    
    col1, col2 = st.columns(2)
    
    with col1:
        calc_age = st.slider("Age", 18, 80, 30)
        calc_coverage = st.selectbox("Coverage Amount (Lakhs)", [5, 10, 15, 20, 25, 30, 50])
    
    with col2:
        calc_policy_type = st.selectbox("Policy Type", ["Term Life", "Health", "Comprehensive", "Accident Cover"])
        calc_health = st.selectbox("Health Status", ["Good", "Average", "Poor"])
    
    if st.button("Calculate Premium", use_container_width=True):
        estimate = calculate_premium_estimate(calc_age, calc_coverage, calc_policy_type, calc_health)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Estimated Annual Premium", format_currency(estimate['estimated_premium']))
        with col2:
            st.metric("Age Factor", f"{estimate['age_factor']}x")
        with col3:
            st.metric("Health Factor", f"{estimate['health_factor']}x")
        
        # Premium breakdown chart
        factors_data = pd.DataFrame({
            'Factor': ['Base Rate', 'Age Impact', 'Health Impact'],
            'Multiplier': [estimate['base_rate'], estimate['age_factor'], estimate['health_factor']]
        })
        
        fig = px.bar(factors_data, x='Factor', y='Multiplier', title='Premium Calculation Factors')
        st.plotly_chart(fig, use_container_width=True)

elif page == "❓ Insurance FAQ":
    st.header("❓ Frequently Asked Questions")
    
    # AI Chat Section
    st.subheader("🤖 Ask AI Insurance Advisor")
    
    user_question = st.text_input(
        "💬 Ask any insurance question:", 
        placeholder="E.g., What's the difference between term and whole life insurance?"
    )
    
    if st.button("Ask AI", use_container_width=True):
        if user_question.strip():
            answer = answer_insurance_question(user_question)
            st.success("🤖 **AI Advisor:**")
            st.write(answer)
        else:
            st.warning("❗ Please enter a question first.")
    
    st.divider()
    
    # Categorized FAQ
    st.subheader("📚 Knowledge Base")
    
    faq_categories = get_faq_categories()
    
    for category, faqs in faq_categories.items():
        with st.expander(f"📂 {category}"):
            for faq in faqs:
                st.write(f"**Q: {faq['question']}**")
                st.write(f"A: {faq['answer']}")
                st.write("---")

elif page == "📈 Market Insights":
    st.header("📈 Insurance Market Insights")
    
    df = load_clean_data()
    
    if not df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            # Policy type distribution
            policy_dist = df['Policy_Type'].value_counts()
            fig_dist = px.pie(values=policy_dist.values, names=policy_dist.index, 
                            title='Market Share by Policy Type')
            st.plotly_chart(fig_dist, use_container_width=True)
        
        with col2:
            # Age vs Premium trends
            age_premium = df.groupby('Age')['Premium_INR'].mean().reset_index()
            fig_trend = px.line(age_premium, x='Age', y='Premium_INR', 
                              title='Average Premium by Age')
            st.plotly_chart(fig_trend, use_container_width=True)
        
        # Coverage analysis
        st.subheader("📊 Coverage Analysis")
        coverage_stats = df.groupby('Policy_Type').agg({
            'Coverage_Lakhs': ['mean', 'min', 'max'],
            'Premium_INR': 'mean'
        }).round(2)
        
        st.dataframe(coverage_stats, use_container_width=True)
        
        # Regional insights
        if 'Region' in df.columns:
            st.subheader("🗺️ Regional Insights")
            regional_data = df.groupby('Region').agg({
                'Premium_INR': 'mean',
                'Coverage_Lakhs': 'mean'
            }).reset_index()
            
            fig_regional = px.scatter(regional_data, x='Premium_INR', y='Coverage_Lakhs', 
                                    color='Region', title='Regional Premium vs Coverage Analysis')
            st.plotly_chart(fig_regional, use_container_width=True)
    else:
        st.error("❌ Unable to load market data for insights.")

def generate_detailed_pdf_report(user_profile: dict, recommendation_data: dict) -> bytes:
    """Generate detailed PDF report using ReportLab"""
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor=HexColor('#2E86AB'),
        alignment=1  # Center
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=12,
        textColor=HexColor('#A23B72')
    )
    
    # Title
    story.append(Paragraph("🛡️ Insurance Policy Recommendation Report", title_style))
    story.append(Spacer(1, 20))
    
    # Date
    story.append(Paragraph(f"Generated on: {datetime.datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Customer Profile
    story.append(Paragraph("👤 Customer Profile", heading_style))
    profile_data = [
        ['Age', f"{user_profile['age']} years"],
        ['Annual Income', f"₹{user_profile['income']} LPA"],
        ['Health Status', user_profile['health']],
        ['Insurance Goal', user_profile['goal']],
        ['Risk Score', f"{recommendation_data['risk_score']}/10"]
    ]
    
    profile_table = Table(profile_data, colWidths=[2*inch, 3*inch])
    profile_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#f0f8ff')),
        ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#2E86AB')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), HexColor('#ffffff')),
        ('GRID', (0, 0), (-1, -1), 1, HexColor('#cccccc'))
    ]))
    
    story.append(profile_table)
    story.append(Spacer(1, 20))
    
    # Recommended Policy
    best_policy = recommendation_data["best_policy"]
    story.append(Paragraph("🎯 Recommended Policy", heading_style))
    
    policy_data = [
        ['Policy Type', best_policy['Policy_Type']],
        ['Coverage Amount', f"₹{best_policy['Coverage_Lakhs']} Lakhs"],
        ['Annual Premium', format_currency(best_policy['Premium_INR'])],
        ['Premium as % of Income', f"{(best_policy['Premium_INR'] / (user_profile['income'] * 1000)) * 100:.1f}%"]
    ]
    
    policy_table = Table(policy_data, colWidths=[2*inch, 3*inch])
    policy_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#e8f5e8')),
        ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#2d5a2d')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), HexColor('#ffffff')),
        ('GRID', (0, 0), (-1, -1), 1, HexColor('#cccccc'))
    ]))
    
    story.append(policy_table)
    story.append(Spacer(1, 20))
    
    # AI Reasoning
    story.append(Paragraph("🤖 AI Analysis", heading_style))
    story.append(Paragraph(recommendation_data.get("ai_reasoning", "Analysis completed"), styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Alternative Options
    story.append(Paragraph("📋 Alternative Options", heading_style))
    top_policies = recommendation_data["top_policies"].head(3)
    
    alt_data = [['Policy Type', 'Coverage (Lakhs)', 'Premium (₹)', 'Value Score']]
    for _, policy in top_policies.iterrows():
        value_score = policy['Coverage_Lakhs'] / (policy['Premium_INR'] / 1000)
        alt_data.append([
            policy['Policy_Type'],
            f"₹{policy['Coverage_Lakhs']}L",
            format_currency(policy['Premium_INR']),
            f"{value_score:.1f}"
        ])
    
    alt_table = Table(alt_data, colWidths=[1.5*inch, 1.2*inch, 1.2*inch, 1.1*inch])
    alt_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#f0f0f0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#333333')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), HexColor('#ffffff')),
        ('GRID', (0, 0), (-1, -1), 1, HexColor('#cccccc'))
    ]))
    
    story.append(alt_table)
    story.append(Spacer(1, 20))
    
    # Disclaimer
    story.append(Paragraph("⚠️ Important Disclaimer", heading_style))
    disclaimer_text = """
    This recommendation is based on AI analysis of your profile and market data. 
    Please consult with a licensed insurance advisor before making final decisions. 
    Terms and conditions apply. Premium rates may vary based on medical underwriting.
    """
    story.append(Paragraph(disclaimer_text, styles['Normal']))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666; font-size: 14px;'>"
    "🛡️ Insurance Policy Optimizer | Powered by AI | Made with ❤️ using Streamlit"
    "</div>", 
    unsafe_allow_html=True
)
