import streamlit as st
import google.generativeai as genai
from supabase import create_client
from apify_client import ApifyClient
import json

# 1. Page Configuration
st.set_page_config(
    page_title="Strategy Mentoring - 90 Days Multi-Competitor Audit",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Inject Custom CSS for Full RTL & Professional UI
def inject_custom_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');

    html, body, [class*="css"], .stMarkdown, p, div, input, textarea, label, span {
        font-family: 'Cairo', sans-serif !important;
        direction: rtl !important;
        text-align: right !important;
    }

    .stApp {
        direction: rtl !important;
        text-align: right !important;
        background-color: #F8FAFC;
    }

    section[data-testid="stSidebar"] {
        direction: rtl !important;
        text-align: right !important;
        background-color: #FFFFFF !important;
        border-left: 1px solid #E2E8F0 !important;
    }

    section[data-testid="stSidebar"] * {
        direction: rtl !important;
        text-align: right !important;
    }

    .main-header {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        padding: 24px 32px;
        border-radius: 12px;
        color: #FFFFFF;
        margin-bottom: 24px;
        box-shadow: 0 10px 15px -3px rgba(15, 23, 42, 0.08);
    }
    
    .main-header h1 {
        color: #FFFFFF !important;
        font-weight: 800 !important;
        font-size: 1.8rem !important;
        margin: 0 0 8px 0 !important;
    }

    .main-header p {
        color: #94A3B8 !important;
        margin: 0 !important;
        font-size: 1rem !important;
    }

    .stTextInput label, .stNumberInput label, .stTextArea label, .stRadio label {
        font-size: 0.95rem !important;
        font-weight: 700 !important;
        color: #1E293B !important;
        margin-bottom: 6px !important;
    }

    .stTextInput input, .stNumberInput input, .stTextArea textarea {
        border-radius: 8px !important;
        border: 1px solid #CBD5E1 !important;
        padding: 10px 14px !important;
        background-color: #FFFFFF !important;
        color: #0F172A !important;
    }

    div[data-testid="stForm"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 12px !important;
        padding: 24px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.03) !important;
    }

    div.stButton > button, div[data-testid="stForm"] button {
        width: 100% !important;
        background-color: #FF94BD !important;
        color: #000000 !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
        border-radius: 8px !important;
        padding: 12px 24px !important;
        border: none !important;
        box-shadow: 0 4px 6px -1px rgba(255, 182, 193, 0.2) !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px !important;
        direction: rtl !important;
        border-bottom: 2px solid #E2E8F0 !important;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0 !important;
        padding: 10px 20px !important;
        font-weight: 700 !important;
        color: #64748B !important;
    }

    .stTabs [aria-selected="true"] {
        color: #2563EB !important;
        border-bottom-color: #2563EB !important;
    }

    .section-title {
        color: #0F172A;
        font-size: 1.25rem;
        font-weight: 700;
        margin-top: 16px;
        margin-bottom: 16px;
        padding-bottom: 8px;
        border-bottom: 2px solid #F1F5F9;
    }
    </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# 3. Initialize Connections
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
    st.warning("⚠️ الرجاء ضبط المفاتيح السرية (Secrets) في Streamlit للبدء.")

# Custom Header Banner
st.markdown("""
<div class="main-header">
    <h1>📊 Marketing Strategy Audit Tool</h1>
    <p>MADE BY YASMINE 🩷</p>
</div>
""", unsafe_allow_html=True)

# Helper function to extract top reels/posts with explicit links
def parse_and_extract_links(items):
    if not items:
        return {"error": "لا توجد بيانات مسحوبة"}
    
    reels = []
    posts = []
    
    for item in items:
        url = item.get('url') or item.get('postUrl') or ''
        p_type = item.get('type', '')
        is_video = item.get('isVideo', False) or p_type in ['Video', 'Reel']
        
        if is_video and url:
            views = item.get('playCount') or item.get('videoViewCount') or item.get('likesCount', 0)
            reels.append({'url': url, 'views': views, 'caption': (item.get('caption') or '')[:80]})
        elif url:
            engagements = (item.get('likesCount', 0) or 0) + (item.get('commentsCount', 0) or 0)
            posts.append({'url': url, 'engagements': engagements, 'caption': (item.get('caption') or '')[:80]})
            
    top_5_reels = sorted(reels, key=lambda x: x['views'], reverse=True)[:5]
    top_5_posts = sorted(posts, key=lambda x: x['engagements'], reverse=True)[:5]
    
    return {
        "top_5_reels": top_5_reels,
        "top_5_posts": top_5_posts
    }

# Navigation Sidebar
st.sidebar.markdown("### 📁 Projects Management")
project_mode = st.sidebar.radio("?! 🙄", ["New Project", "View History"])

if project_mode == "New Project":
    with st.form("audit_form_90days_links"):
        
        tab1, tab2, tab3 = st.tabs(["1️⃣ بيانات البراند الرئيسي", "2️⃣ المنافسين (1 و 2)", "3️⃣ أداء الإعلانات والجمهور"])
        
        # --- TAB 1: BRAND INPUTS ---
        with tab1:
            st.markdown("<div class='section-title'>بيانات البراند الرئيسي</div>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                brand_name = st.text_input("اسم البراند الرئيسي *")
                product_service = st.text_input("المنتج / الخدمة *")
                geo_coverage = st.text_input("الدولة / التغطية الجغرافية *")
                main_objective = st.text_input("الهدف الرئيسي خلال الـ 90 يومًا *")
                expected_audience = st.text_input("حجم الجمهور المتوقع")
                brand_website = st.text_input("رابط موقع البراند / اللاندنج / الواتساب")
            with col2:
                st.markdown("**المنصات الأساسية:**")
                brand_ig = st.text_input("حساب/رابط إنستجرام للبراند (أساسي) *", placeholder="brand_username")
                brand_fb = st.text_input("رابط صفحة فيسبوك للبراند (أساسي) *", placeholder="https://facebook.com/...")
                st.markdown("**المنصات الاختيارية:**")
                brand_tiktok = st.text_input("حساب/رابط تيك توك للبراند (اختياري)")
                brand_linkedin = st.text_input("رابط لينكدإن للبراند (اختياري)")
                brand_yt = st.text_input("رابط قناة يوتيوب للبراند (اختياري)")

        # --- TAB 2: COMPETITORS INPUTS ---
        with tab2:
            st.markdown("<div class='section-title'>بيانات المنافس الأول (Competitor 1)</div>", unsafe_allow_html=True)
            c1_a, c1_b = st.columns(2)
            with c1_a:
                comp1_name = st.text_input("اسم المنافس الأول *")
                comp1_website = st.text_input("رابط موقع/لاندنج المنافس الأول")
                comp1_ig = st.text_input("رابط/حساب إنستجرام للمنافس الأول (أساسي) *")
            with c1_b:
                comp1_fb = st.text_input("رابط صفحة فيسبوك للمنافس الأول (أساسي) *")
                comp1_tiktok = st.text_input("رابط تيك توك للمنافس الأول (اختياري)")
                comp1_gmaps = st.text_input("رابط Google Maps للمنافس الأول")

            st.markdown("<div class='section-title'>بيانات المنافس الثاني (Competitor 2)</div>", unsafe_allow_html=True)
            c2_a, c2_b = st.columns(2)
            with c2_a:
                comp2_name = st.text_input("اسم المنافس الثاني *")
                comp2_website = st.text_input("رابط موقع/لاندنج المنافس الثاني")
                comp2_ig = st.text_input("رابط/حساب إنستجرام للمنافس الثاني (أساسي) *")
            with c2_b:
                comp2_fb = st.text_input("رابط صفحة فيسبوك للمنافس الثاني (أساسي) *")
                comp2_tiktok = st.text_input("رابط تيك توك للمنافس الثاني (اختياري)")
                comp2_gmaps = st.text_input("رابط Google Maps للمنافس الثاني")

        # --- TAB 3: ADS & MARKET RESEARCH ---
        with tab3:
            st.markdown("<div class='section-title'>بيانات الحملات وأبحاث السوق (خلال آخر 90 يومًا)</div>", unsafe_allow_html=True)
            c_m1, c_m2 = st.columns(2)
            with c_m1:
                ad_spend = st.number_input("صرف Meta Ads خلال آخر 90 يومًا ($) - اختياري", min_value=0.0, value=0.0)
                ad_objective_results = st.text_input("هدف الحملات، عدد النتائج، وتكلفة النتيجة (Cost per result)")
            with c_m2:
                market_notes = st.text_area("أبحاث الجمهور، الكومنتات، المشاكل، والاعتراضات من الجروبات والتقييمات")

        submitted = st.form_submit_button("🚀 RUN TASK")

    if submitted and brand_name and brand_ig and comp1_name and comp2_name:
        st.info("🔄 WORKING ON IT 🫩...")
        
        brand_parsed_links = {}
        try:
            run_input = {"directUrls": [f"https://www.instagram.com/{brand_ig.replace('https://instagram.com/','').replace('/','')}/"], "resultsType": "posts"}
            run = apify.actor("apify/instagram-post-scraper").call(run_input=run_input, timeout_secs=25)
            b_items = apify.dataset(run["defaultDatasetId"]).list_items().items
            brand_parsed_links = parse_and_extract_links(b_items)
        except Exception as e:
            brand_parsed_links['error'] = str(e)

        # Generate Meta Ad Library links automatically
        comp1_ad_library_url = f"https://www.facebook.com/ads/library/?active_status=all&ad_type=all&q={comp1_name.replace(' ', '%20')}"
        comp2_ad_library_url = f"https://www.facebook.com/ads/library/?active_status=all&ad_type=all&q={comp2_name.replace(' ', '%20')}"

        st.info("🧠 REPORT WILL BE DONE 🤌🏻...")

        strict_prompt_with_links = f"""
        أنت Senior Brand Strategist & Growth Director. قم بإجراء Audit كامل واستخراج استراتيجية متكاملة للبراند '{brand_name}' عن فترة **آخر 90 يومًا فقط**.

        شرط صارم جداً: في كل بند يتطلب روابط (مثل روابط الحسابات، أرفع 5 Reels مشاهدة، أعلى 5 بوستات تفاعلاً، Meta Ad Library، وGoogle Maps)، يجب طباعة الرابط كاملاً بتنسيق Markdown قابل للنقر كـ `[عرض الرابط](URL)` أو كتابة الرابط صراحة بدون إخفائه.

        البيانات والروابط المتاحة:
        - البراند الرئيسي: {brand_name} | الموقع: {brand_website}
        - روابط البراند: FB: {brand_fb} | IG: https://instagram.com/{brand_ig} | TikTok: {brand_tiktok} | LinkedIn: {brand_linkedin} | YT: {brand_yt}
        - المنافس الأول: {comp1_name} | الموقع: {comp1_website} | IG: {comp1_ig} | FB: {comp1_fb} | TikTok: {comp1_tiktok} | Maps: {comp1_gmaps} | Ad Library Link: {comp1_ad_library_url}
        - المنافس الثاني: {comp2_name} | الموقع: {comp2_website} | IG: {comp2_ig} | FB: {comp2_fb} | TikTok: {comp2_tiktok} | Maps: {comp2_gmaps} | Ad Library Link: {comp2_ad_library_url}
        - الروابط المسحوبة أوتوماتيكياً لأعلى ريلز وبوستات البراند: {json.dumps(brand_parsed_links, ensure_ascii=False)}
        - أداء الإعلانات (آخر 90 يوم): صرف Meta Ads: {ad_spend} $ | النتائج والأهداف: {ad_objective_results}
        - أبحاث السوق والكومنتات: {market_notes}

        المطلوب: التزم حرفياً بالهيكل التالي وقوائمه ومجالاته الـ 50+ باللغة العربية، ودون حذف أي رابط أو بند:

        Strategy Mentoring - {brand_name}

        1- Situation Analysis 

         - platforms analysis 
        * لينك/يوزر الحساب: 
          - Facebook: [{brand_fb}]({brand_fb})
          - Instagram: [https://instagram.com/{brand_ig}](https://instagram.com/{brand_ig})
          - TikTok: {brand_tiktok}
          - LinkedIn: {brand_linkedin}
          - YouTube: {brand_yt}
        * عدد المتابعين الحالي ونمو المتابعين خلال آخر 90 يوم (زيادة/نقص)
        * Reach والـ Engagements خلال آخر 90 يوم
        * Profile visits و Website/WhatsApp clicks (رابط البراند: [{brand_website}]({brand_website}))
        * تنوع المحتوى: كام ريل في الشهر - كام كاروسيل في الشهر - كام بوست صورة - كام بوست تكست
        * أفضل ٥ Reels من حيث المشاهدات خلال آخر 90 يوم (استخدم الروابط المسحوبة المتاحة بصيغة Markdown قابل للنقر `[شاهد الريل](رابط)` مع المشاهدات)
        * أفضل ٥ بوستات من حيث التفاعل خلال آخر 90 يوم (استخدم الروابط المسحوبة المتاحة بصيغة Markdown `[شاهد البوست](رابط)` مع التفاعلات)
        * إحصائيات متقدمة بالفيديو: Watch Time و Average Play Time و 3-second Views
        * الجمهور الأساسي وعدد الجمهور المتوقع للبراند: {expected_audience}
        * اتصرف كام على Meta Ads خلال الفترة؟ ({ad_spend} $)
        * Objective للحملات، عدد النتائج، و Cost per result

         - Audience Analysis 
        * كم ساعة يقضي المستخدم على السوشيال ميديا؟ من DataReportal (لدولة {geo_coverage})
        * ترتيب المنصات ونوع المحتوى المفضل في البلد؟ من DataReportal
        * نسبة ذكور / إناث، الفئة العمرية، أهم المدن، والمستوى الإقتصادي
        * المشاكل والاعتراضات من AnswerThePublic والجروبات والكومنتات
        * الاهتمامات ودوافع الشراء والمؤثرين المناسبين
        * سلوك المستخدم على FB، نوع المحتوى المفضل على IG Explore، وتريندات TikTok Creative Center
        * طريقة الشراء أونلاين/أوفلاين، سرعة القرار، وعوامل بناء الثقة والمراجعات

         - competitor analysis

        [المنافس الأول: {comp1_name}]
        * اسم المنافس: {comp1_name}
        * لينك الموقع/اللاندنج: [{comp1_website}]({comp1_website})
        * لينك Instagram: [{comp1_ig}]({comp1_ig})
        * لينك Facebook: [{comp1_fb}]({comp1_fb})
        * لينك TikTok: {comp1_tiktok}
        * Google Business Profile / Maps link: [{comp1_gmaps}]({comp1_gmaps})
        * التغطية الجغرافية والجمهور المستهدف وأقرب 3 خدمات شبهنا
        * Positioning & Offer, USP, Proofs, الباقات، وهل الأسعار معلنة أم لا
        * أقوى CTA وطريقة الوصول للـ Offer (واتساب/فورم/مكالمة/حجز أونلاين) وهل بيطلب بيانات؟
        * Nurture وميزة الفانل عنده
        * تنوع المحتوى شهرياً ونبرة الصوت Tone of Voice
        * أفضل ٥ Reels من حيث المشاهدات (استخرج أمثلة وروابط مفترضة/فعلية من الحساب)
        * أفضل ٥ بوستات من حيث التفاعل (استخرج أمثلة وروابط مفترضة/فعلية من الحساب)
        * أكثر 3 Topics متكررين و Content gaps
        * Meta Ad Library: رابط مكتبة إعلانات المنافس الأول المباشر: [{comp1_ad_library_url}]({comp1_ad_library_url})
        * أقوى Angle إعلاني وأنواع الكرياتيف والعروض المتكررة
        * Google rating وعدد الريفيوز وملخص الإيجابيات والسلبيات وأسلوب وسرعة الرد

        [المنافس الثاني: {comp2_name}]
        * اسم المنافس: {comp2_name}
        * لينك الموقع/اللاندنج: [{comp2_website}]({comp2_website})
        * لينك Instagram: [{comp2_ig}]({comp2_ig})
        * لينك Facebook: [{comp2_fb}]({comp2_fb})
        * لينك TikTok: {comp2_tiktok}
        * Google Business Profile / Maps link: [{comp2_gmaps}]({comp2_gmaps})
        * التغطية الجغرافية والجمهور المستهدف وأقرب 3 خدمات شبهنا
        * Positioning & Offer, USP, Proofs, الباقات، وهل الأسعار معلنة أم لا
        * أقوى CTA وطريقة الوصول للـ Offer وهل بيطلب بيانات؟
        * Nurture وميزة الفانل عنده
        * تنوع المحتوى شهرياً ونبرة الصوت Tone of Voice
        * أفضل ٥ Reels من حيث المشاهدات (استخرج أمثلة وروابط)
        * أفضل ٥ بوستات من حيث التفاعل (استخرج أمثلة وروابط)
        * أكثر 3 Topics متكررين و Content gaps
        * Meta Ad Library: رابط مكتبة إعلانات المنافس الثاني المباشر: [{comp2_ad_library_url}]({comp2_ad_library_url})
        * أقوى Angle إعلاني وأنواع الكرياتيف والعروض المتكررة
        * Google rating وعدد الريفيوز وملخص الإيجابيات والسلبيات وأسلوب وسرعة الرد

        — ملخص المقارنة بين البراند والمنافسين الاثنين (يطلع منه قرارات) —
        * نقط تفوقنا عليهما (1–3 نقاط)
        * نقط تفوق المنافس الأول والفرص الناتجة
        * نقط تفوق المنافس الثاني والفرص الناتجة
        * فرصة Quick win إستراتيجية

         - SWOT Analysis 
        * Strengths, Weaknesses, Opportunities, Threats

        2- Customer journey 
        * درجة الوعي (Awareness Levels: Unaware, Problem Aware, Solution Aware, Brand Aware)
        * رحلة العميل تفصيلياً (أول نقطة احتكاك -> ماذا يفعل قبل الشراء -> اعتراضات الجمهور -> القرار النهائي)

        3- Objectives + key results (KPI) 
        * الهدف الرئيسي والمنتج والسوق والمدة (90 يوم)
        * 3 أهداف استراتيجية SMART + الـ KPI الأساسي لكل هدف

        4- Customer (Segment & Buyer Persona) 
        * حدد 4 Segments تفصيلية مع: (Interest or need + location + Age and gender + Pain Point + Decision Trigger).

        أعد التقرير شاملاً ومفصلاً مع طباعة كل رابط صراحة وبوضوح.
        """

        try:
            ai_response = model.generate_content(strict_prompt_with_links)
            st.success("✅ STRATEGY REPORT DONE!")
            st.markdown(ai_response.text)
            
            try:
                db_payload = {
                    "brand_name": brand_name,
                    "inputs": {
                        "geo": geo_coverage,
                        "objective": main_objective,
                        "ad_spend": ad_spend,
                        "timeframe": "90_days",
                        "competitors": [comp1_name, comp2_name]
                    },
                    "scraped_data": json.loads(json.dumps(brand_parsed_links, default=str)),
                    "strategy_output": str(ai_response.text)
                }
                supabase.table("strategy_projects").insert(db_payload).execute()
                st.info("💾 SAVED IM DATABASE.")
            except Exception as db_err:
                pass
        except Exception as ai_err:
            st.error(f"❌ ERROR: {str(ai_err)}")

elif project_mode == "View History":
    st.header("📂 Saved Projects")
    try:
        response = supabase.table("strategy_projects").select("*").order("created_at", descending=True).execute()
        projects = response.data
        if projects:
            project_names = [f"{p['brand_name']} - {str(p['created_at'])[:10]}" for p in projects]
            selected_proj = st.selectbox("اختر مشروعاً لعرضه:", project_names)
            idx = project_names.index(selected_proj)
            st.subheader(f"📊 التقرير الاستراتيجي لـ {projects[idx]['brand_name']}")
            st.markdown(projects[idx]['strategy_output'])
        else:
            st.write("لا توجد مشاريع محفوظة حالياً.")
    except Exception as e:
        st.error(f"خطأ في جلب المشاريع: {str(e)}")
