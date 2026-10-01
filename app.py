import streamlit as st
import google.generativeai as genai
from supabase import create_client
from apify_client import ApifyClient
import json

st.set_page_config(page_title="Strategy Mentoring AI", layout="wide")

# 1. Initialize Connections
@st.cache_resource
def init_services():
    supabase_url = st.secrets["SUPABASE_URL"]
    supabase_key = st.secrets["SUPABASE_KEY"]
    gemini_key = st.secrets["GEMINI_API_KEY"]
    apify_key = st.secrets["APIFY_KEY"]
    
    supabase = create_client(supabase_url, supabase_key)
    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel('gemini-3.8-flash')
    apify = ApifyClient(apify_key)
    return supabase, model, apify

try:
    supabase, model, apify = init_services()
except Exception as e:
    st.warning("⚠️ الرجاء ضبط المفاتيح (Secrets) في Streamlit للبدء.")

st.title("📊 Strategy Mentoring - Audit & AI Strategy Tool")

# Sidebar
st.sidebar.header("📁 إدارة المشاريع")
project_mode = st.sidebar.radio("اختر النمط:", ["مشروع جديد", "استعراض المشاريع السابقة"])

if project_mode == "مشروع جديد":
    st.header("📝 إدخال بيانات البراند والبحث")
    
    with st.form("audit_form"):
        col1, col2 = st.columns(2)
        with col1:
            brand_name = st.text_input("اسم البراند الرئيسي *")
            brand_url = st.text_input("رابط الموقع / اللاندنج / الواتساب")
            geo_coverage = st.text_input("الدولة / المدينة / التغطية الجغرافية *")
            main_objective = st.text_input("الهدف الرئيسي اللى فى البريف (30/60/90 يوم) *")
            
        with col2:
            ig_handle = st.text_input("Instagram Username (البراند الرئيسي)")
            fb_url = st.text_input("Facebook Page URL")
            tiktok_handle = st.text_input("TikTok Username")
            ad_spend = st.number_input("الميزانية الإعلانية على Meta خلال الفترة ($) - اختياري", min_value=0.0, value=0.0)

        st.subheader("👥 بيانات المنافس")
        comp_name = st.text_input("اسم المنافس")
        comp_ig = st.text_input("Instagram Username للمنافس")
        comp_fb = st.text_input("Facebook Page URL للمنافس")
        comp_gmaps = st.text_input("Google Maps / Business Profile Link للمنافس")
        
        st.subheader("💬 عينات أبحاث السوق والتقييمات")
        market_insights = st.text_area("عينة تعليقات، اعتراضات الجمهور من الجروبات، أو تقييمات Google/Reviews")
        
        submitted = st.form_submit_button("🚀 بدء الـ Audit واستخراج الاستراتيجية الكاملة")

    if submitted and brand_name:
        st.info("🔄 جاري سحب البيانات المتاحة عبر Apify...")
        
        scraped_data = {}
        if ig_handle:
            try:
                run_input = {"directUrls": [f"https://www.instagram.com/{ig_handle}/"], "resultsType": "details"}
                run = apify.actor("apify/instagram-profile-scraper").call(run_input=run_input)
                scraped_data['brand_ig'] = apify.dataset(run["defaultDatasetId"]).list_items().items
            except Exception as e:
                scraped_data['ig_error'] = str(e)

        st.info("🧠 جاري تحليل البيانات وبناء التقرير الاستراتيجي الهيكلي...")
        
        detailed_prompt = f"""
        أنت Senior Brand Strategist & Growth Marketer. قم بإجراء Audit واستخراج استراتيجية تسويقية متكاملة ومشروحة بدقة للبراند: '{brand_name}'.

        المدخلات الأساسية:
        - البراند: {brand_name} ({brand_url})
        - الدولة/التغطية: {geo_coverage}
        - الهدف الرئيسي: {main_objective}
        - الميزانية الإعلانية على Meta: {ad_spend} $
        - حسابات البراند: Instagram ({ig_handle}), FB ({fb_url}), TikTok ({tiktok_handle})
        - المنافس: {comp_name} (IG: {comp_ig}, FB: {comp_fb}, Maps: {comp_gmaps})
        - مدخلات أبحاث السوق والكومنتات: {market_insights}
        - بيانات Scraping المتاحة: {json.dumps(scraped_data, ensure_ascii=False)}

        المطلوب: قم بتوليد التقرير بتنسيق Markdown متناسق ومنسق جداً باللغة العربية، ملتزماً بالهيكل التالي حرفياً وبكل أجزائه:

        ## 1- Situation Analysis

        ### A. Platforms Analysis
        - تحليل الحسابات والنمو والمتابعين.
        - Reach & Engagements (تقدير واستخراج بناءً على البيانات والميزانية).
        - Profile Visits / Website or WhatsApp Clicks.
        - تنوع المحتوى شهرياً (Reels, Carousels, Single Images, Text).
        - أفضل 5 Reels من حيث المشاهدات + أفضل 5 بوستات تفاعلاً.
        - إحصائيات الفيديو المتقدمة (Watch Time, Average Play Time, 3-sec Views).
        - تحليل حملات Meta Ads (الميزانية {ad_spend}$، الهدف الموصى به، عدد النتائج المتوقع، و Cost Per Result المتوقع).

        ### B. Audience Analysis
        - سلوك المستخدم وساعات الاستخدام من DataReportal (ترتيب المنصات في {geo_coverage}، نوع المحتوى المفضل).
        - الديموغرافيات (نسب الذكور/الإناث، الفئات العمرية، أهم المدن، المستوى الاقتصادي).
        - المشاكل والاعتراضات (من AnswerThePublic/الجروبات/الكومنتات).
        - الاهتمامات ودوافع الشراء وسلوك المستخدم على Facebook و Instagram و TikTok.
        - عوامل بناء الثقة واعتراضات الشراء.

        ### C. Competitor Analysis (المنافس: {comp_name})
        - الروابط ونطاق التغطية والجمهور المستهدف.
        - Positioning & Offer, USP, Proofs, Bundles, والأسعار (معلنة أم لا).
        - أقوى CTA وطريقة الوصول للـ Offer (واتساب/فورم/مكالمة).
        - تحليل الفانل (Nurture / Auto-reply).
        - تنوع المحتوى شهرياً + أفضل 5 Reels وأفضل 5 بوستات تفاعلاً عنده.
        - أكثر 3 Topics متكررة ونبرة الصوت (Tone of Voice).
        - Content Gaps (الفجوات التسويقية التي لم يغطها المنافس).
        - Meta Ad Library Analysis (الأنماط الإعلانية، الكرياتيف، والعروض).
        - تقييمات Google Ratings وملخص الإيجابيات والسلبيات وسرعة الرد.
        - ملخص المقارنة: (3 نقاط تفوقنا - 3 نقاط تفوقه - فرصة Quick Win).

        ### D. SWOT Analysis
        - Strengths (نقاط القوة).
        - Weaknesses (نقاط الضعف).
        - Opportunities (الفرص).
        - Threats (التهديدات).

        ---

        ## 2- Customer Journey
        - درجة الوعي (Awareness Levels): Unaware, Problem Aware, Solution Aware, Brand Aware مع ربطها بالسلوكيات.
        - رحلة العميل تفصيلياً: أول نقطة احتكاك -> ماذا يفعل قبل الشراء -> ما يمنعه من القرار -> ما يدفعه للقرار النهائي.

        ---

        ## 3- Objectives + Key Results (KPI)
        - ملخص الهدف والحجم والسوق والفترة (30/60/90 يوم).
        - تحديد 3 أهداف استراتيجية SMART محددة + الـ KPI الأساسي لكل هدف.

        ---

        ## 4- Customer (Segment & Buyer Persona)
        - تحديد 4 Segments تفصيلية مع توضيح: (Interest/Need + Location + Age & Gender + Pain Point + Decision Trigger).

        اجعل التقرير مليئاً بالتحليلات التخصصية، القرارات العملية، والحلول المباشرة بدون كلام إنشائي مجرد.
        """
        
        ai_response = model.generate_content(detailed_prompt)
        
        st.success("✅ تم استخراج الاستراتيجية والـ Audit بنجاح!")
        st.markdown(ai_response.text)
        
        # Save to Supabase
        db_payload = {
            "brand_name": brand_name,
            "inputs": {"geo": geo_coverage, "objective": main_objective, "ad_spend": ad_spend},
            "scraped_data": scraped_data,
            "strategy_output": ai_response.text
        }
        supabase.table("strategy_projects").insert(db_payload).execute()
        st.info("💾 تم حفظ التقرير في قاعدة البيانات بنجاح.")

elif project_mode == "استعراض المشاريع السابقة":
    st.header("📂 المشاريع المحفوظة")
    response = supabase.table("strategy_projects").select("*").order("created_at", descending=True).execute()
    projects = response.data
    
    if projects:
        project_names = [f"{p['brand_name']} - {p['created_at'][:10]}" for p in projects]
        selected_proj = st.selectbox("اختر مشروعاً لعرضه:", project_names)
        idx = project_names.index(selected_proj)
        
        st.subheader(f"📊 التقرير الاستراتيجي لـ {projects[idx]['brand_name']}")
        st.markdown(projects[idx]['strategy_output'])
    else:
        st.write("لا توجد مشاريع محفوظة حالياً.")
