import streamlit as st
import google.generativeai as genai
from supabase import create_client
from apify_client import ApifyClient
import pandas as pd
import json

st.set_page_config(page_title="Strategy Mentoring AI", layout="wide")

# Initialize Connections
@st.cache_resource
def init_services():
    supabase_url = st.secrets["SUPABASE_URL"]
    supabase_key = st.secrets["SUPABASE_KEY"]
    gemini_key = st.secrets["GEMINI_API_KEY"]
    apify_key = st.secrets["APIFY_KEY"]
    
    supabase = create_client(supabase_url, supabase_key)
    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    apify = ApifyClient(apify_key)
    return supabase, model, apify

try:
    supabase, model, apify = init_services()
except Exception as e:
    st.warning("الرجاء ضبط المفاتيح (Secrets) في Streamlit للبدء.")

st.title("📊 Strategy Mentoring - Social Media Audit & Strategy Tool")

# Sidebar for Project Selection or New Audit
st.sidebar.header("📁 إدارة المشاريع")
project_mode = st.sidebar.radio("اختر النمط:", ["مشروع جديد", "استعراض المشاريع السابقة"])

if project_mode == "مشروع جديد":
    st.header("1️⃣ المدخلات الأساسية للبراند والمنافسين")
    
    with st.form("audit_form"):
        col1, col2 = st.columns(2)
        with col1:
            brand_name = st.text_input("اسم البراند الرئيسي *")
            brand_url = st.text_input("رابط الموقع / الواتساب")
            country_target = st.text_input("الدولة / التغطية الجغرافية *")
            primary_goal = st.text_input("الهدف الرئيسي للبراند *")
            
        with col2:
            ig_handle = st.text_input("Instagram Username (البراند الرئيسي)")
            fb_url = st.text_input("Facebook Page URL (البراند الرئيسي)")
            tiktok_handle = st.text_input("TikTok Username (البراند الرئيسي)")
            ad_spend = st.number_input("الميزانية الإعلانية الإجمالية ($) - اختياري", min_value=0.0, value=0.0)

        st.subheader("👥 منافسين (حتى 2 منافسين)")
        comp1_name = st.text_input("اسم المنافس الأول")
        comp1_ig = st.text_input("Instagram Username للمنافس الأول")
        
        st.subheader("💬 أبحاث الجمهور والتقييمات (Data Samples)")
        customer_comments = st.text_area("عينة من كومنتات/اعتراضات الجمهور أو تقييمات جوجل")
        
        submitted = st.form_submit_button("🚀 بدء الـ Audit واستخراج الاستراتيجية")

    if submitted and brand_name:
        st.info("جاري جلب البيانات وتحليل الحسابات...")
        
        # Data Scraping via Apify Actors (Sample fetching)
        scraped_data = {}
        if ig_handle:
            try:
                run_input = {"directUrls": [f"https://www.instagram.com/{ig_handle}/"], "resultsType": "details"}
                run = apify.actor("apify/instagram-profile-scraper").call(run_input=run_input)
                dataset_items = apify.dataset(run["defaultDatasetId"]).list_items().items
                scraped_data['instagram'] = dataset_items
            except Exception as e:
                scraped_data['instagram_error'] = str(e)
                
        # Strategic AI Prompting
        st.info("جاري تحليل البيانات بواسطة AI واستخراج القرارات الاستراتيجية...")
        
        system_prompt = f"""
        أنت استشاري تسويق إلكتروني خبير (Senior Growth & Strategy Director).
        قم بإجراء Audit كامل واستخراج استراتيجية شاملة للبراند: {brand_name}.
        
        المدخلات:
        - الدولة والجمهور المستهدف: {country_target}
        - الهدف الرئيسي: {primary_goal}
        - الميزانية الإعلانية: {ad_spend} $
        - حساب الإنستجرام: {ig_handle}
        - المنافس: {comp1_name} ({comp1_ig})
        - عينة تعليقات واعتراضات الجمهور: {customer_comments}
        - البيانات المسحوبة من المنصة: {json.dumps(scraped_data, ensure_ascii=False)}

        المطلوب مخرجات باللغة العربية مقسمة بالكامل للقطاعات التالية في صيغة JSON حصرية:
        1. "situation_analysis": {{ "platform_audit": "...", "content_gaps": "...", "ads_evaluation": "..." }}
        2. "competitor_analysis": {{ "strengths": "...", "weaknesses": "...", "positioning": "..." }}
        3. "swot_analysis": {{ "strengths": [], "weaknesses": [], "opportunities": [], "threats": [] }}
        4. "customer_journey": {{ "awareness_levels": "...", "purchase_triggers": "...", "barriers": "..." }}
        5. "smart_objectives": {{ "30_days": "...", "60_days": "...", "90_days": "...", "kpis": "..." }}
        6. "buyer_personas": [ {{ "segment_name": "...", "age_gender": "...", "location": "...", "pain_points": "...", "trigger": "..." }} ]
        
        تأكد أن كل رقم ومعلومة يتم ترجمتها إلى قرار عملي وتوصية واضحة للنمو.
        """
        
        ai_response = model.generate_content(system_prompt)
        
        st.success("تم الانتهاء من التحليل والاستراتيجية بنجاح!")
        st.markdown(ai_response.text)
        
        # Save results to Supabase
        db_payload = {
            "brand_name": brand_name,
            "inputs": {"country": country_target, "goal": primary_goal, "ad_spend": ad_spend},
            "scraped_data": scraped_data,
            "strategy_output": ai_response.text
        }
        supabase.table("strategy_projects").insert(db_payload).execute()
        st.info("تم حفظ المشروع في قاعدة البيانات بنجاح.")

elif project_mode == "استعراض المشاريع السابقة":
    st.header("📂 المشاريع المحفوظة")
    response = supabase.table("strategy_projects").select("*").order("created_at", descending=True).execute()
    projects = response.data
    
    if projects:
        project_names = [f"{p['brand_name']} - {p['created_at'][:10]}" for p in projects]
        selected_proj = st.selectbox("اختر مشروعاً لعرضه:", project_names)
        idx = project_names.index(selected_proj)
        
        st.subheader(f"تقرير الاستراتيجية والـ Audit لـ {projects[idx]['brand_name']}")
        st.markdown(projects[idx]['strategy_output'])
    else:
        st.write("لا توجد مشاريع محفوظة حالياً.")
