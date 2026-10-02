import streamlit as st
import google.generativeai as genai
from supabase import create_client
from apify_client import ApifyClient
import json
import datetime

# ---------------------------------------------------------
# 1. Page Configuration & Professional RTL Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="Social Media Audit & Strategy Engine",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def inject_custom_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');

    /* Global Direction & Typography */
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

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        direction: rtl !important;
        text-align: right !important;
        background-color: #FFFFFF !important;
        border-left: 1px solid #E2E8F0 !important;
    }

    /* Header Styling */
    .main-header {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        padding: 28px;
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
        font-size: 0.95rem !important;
    }

    /* Forms & Containers */
    div[data-testid="stForm"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 12px !important;
        padding: 24px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.03) !important;
    }

    /* Button Styling */
    div.stButton > button, div[data-testid="stForm"] button {
        width: 100% !important;
        background-color: #2563EB !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
        border-radius: 8px !important;
        padding: 12px 24px !important;
        border: none !important;
        box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2) !important;
    }

    /* Tabs Styling */
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
    </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# ---------------------------------------------------------
# 2. Services Initialization
# ---------------------------------------------------------
@st.cache_resource
def init_services():
    supabase_url = st.secrets["SUPABASE_URL"]
    supabase_key = st.secrets["SUPABASE_KEY"]
    gemini_key = st.secrets["GEMINI_API_KEY"]
    apify_key = st.secrets["APIFY_KEY"]
    
    supabase = create_client(supabase_url, supabase_key)
    genai.configure(api_key=gemini_key)
    # تعديل اسم النموذج إلى gemini-3.8-flash المعتمد في الحساب
    model = genai.GenerativeModel('gemini-3.8-flash')
    apify = ApifyClient(apify_key)
    return supabase, model, apify

try:
    supabase, model, apify = init_services()
except Exception as e:
    st.error("⚠️ خطأ في الاتصال بالخدمات السحابية. يرجى التأكد من ضبط الـ Secrets في Streamlit.")

# ---------------------------------------------------------
# 3. Data Collection Functions (Apify & Meta Ad Library)
# ---------------------------------------------------------
def scrape_instagram_account(profile_url, account_type="brand"):
    """Scrapes raw Instagram profile and post data via Apify with safety timeouts."""
    if not profile_url:
        return {"source": "apify", "account_type": account_type, "profile_url": "", "posts": [], "status": "no_url_provided"}
    
    cleaned_handle = profile_url.replace("https://instagram.com/", "").replace("https://www.instagram.com/", "").replace("/", "").strip()
    
    try:
        run_input = {
            "directUrls": [f"https://www.instagram.com/{cleaned_handle}/"],
            "resultsType": "posts",
            "searchLimit": 30
        }
        run = apify.actor("apify/instagram-post-scraper").call(run_input=run_input, timeout_secs=30)
        items = apify.dataset(run["defaultDatasetId"]).list_items().items
        
        cleaned_posts = []
        for item in items:
            cleaned_posts.append({
                "post_id": item.get("id"),
                "url": item.get("url") or item.get("postUrl"),
                "timestamp": item.get("timestamp"),
                "type": item.get("type"),
                "likes_count": item.get("likesCount"),
                "comments_count": item.get("commentsCount"),
                "video_view_count": item.get("videoViewCount") or item.get("playCount"),
                "caption": (item.get("caption") or "")[:200]
            })
            
        return {
            "source": "apify",
            "account_type": account_type,
            "profile_url": f"https://www.instagram.com/{cleaned_handle}/",
            "posts": cleaned_posts,
            "status": "success"
        }
    except Exception as e:
        return {
            "source": "apify",
            "account_type": account_type,
            "profile_url": profile_url,
            "posts": [],
            "status": f"error: {str(e)}"
        }

def collect_meta_ad_library(brand_name, comp1_name, comp2_name):
    """Structures verified Meta Ad Library query pointers."""
    ad_data = []
    entities = [("brand", brand_name), ("competitor_1", comp1_name), ("competitor_2", comp2_name)]
    
    for entity_type, name in entities:
        if name:
            ad_url = f"https://www.facebook.com/ads/library/?active_status=all&ad_type=all&q={name.replace(' ', '%20')}"
            ad_data.append({
                "entity_type": entity_type,
                "advertiser_name": name,
                "ad_library_search_url": ad_url,
                "ads_found": []
            })
            
    return {
        "source": "meta_ad_library",
        "ads": ad_data
    }

# ---------------------------------------------------------
# 4. Streamlit User Interface
# ---------------------------------------------------------
st.markdown("""
<div class="main-header">
    <h1>🎯 محرك الـ Audit والاستراتيجية المحمي ضد التخمين</h1>
    <p>جمع واستخراج آلي للبيانات عبر Apify و Meta Ad Library مع تحليل دقيق ممتثل للشرط الصارم</p>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("### 📂 إدارة المشاريع")
project_mode = st.sidebar.radio("اختر النمط المطلوب:", ["مشروع جديد", "استعراض المشاريع السابقة"])

if project_mode == "مشروع جديد":
    with st.form("audit_engine_form"):
        tab1, tab2 = st.tabs(["1️⃣ روابط المنصات وحسابات التحليل", "2️⃣ البيانات الداخلية (اختياري)"])
        
        with tab1:
            col1, col2 = st.columns(2)
            with col1:
                brand_name = st.text_input("اسم البراند الرئيسي *", placeholder="مثال: Brand X")
                brand_ig_url = st.text_input("رابط إنستجرام البراند الرئيسي *", placeholder="https://www.instagram.com/brand")
            with col2:
                comp1_ig_url = st.text_input("رابط إنستجرام المنافس الأول *", placeholder="https://www.instagram.com/comp1")
                comp2_ig_url = st.text_input("رابط إنستجرام المنافس الثاني *", placeholder="https://www.instagram.com/comp2")
                comp1_name = st.text_input("اسم المنافس الأول", placeholder="Competitor 1")
                comp2_name = st.text_input("اسم المنافس الثاني", placeholder="Competitor 2")
        
        with tab2:
            st.caption("أدخل الأرقام المتاحة فقط من لوحة التحليلات الداخلية، واترك باقي الحقول فارغة:")
            c1, c2, c3 = st.columns(3)
            with c1:
                in_reach = st.number_input("الوصول (Reach)", min_value=0, value=0)
                in_spend = st.number_input("الإنفاق الإعلاني ($)", min_value=0.0, value=0.0)
            with c2:
                in_clicks = st.number_input("نقرات الموقع / الواتساب", min_value=0, value=0)
                in_leads = st.number_input("عدد العملاء المحتملين (Leads)", min_value=0, value=0)
            with c3:
                in_sales = st.number_input("إجمالي المبيعات / الشراء", min_value=0, value=0)
                in_watch_time = st.text_input("ساعات المشاهدة (Watch Time)")

        submitted = st.form_submit_button("🚀 بدء جمع البيانات التلقائي وتشغيل الـ Audit")

    if submitted and brand_name and brand_ig_url:
        # Time and metadata
        now = datetime.datetime.now()
        collected_at = now.strftime("%Y-%m-%d %H:%M:%S")
        analysis_end = now.strftime("%Y-%m-%d")
        analysis_start = (now - datetime.timedelta(days=90)).strftime("%Y-%m-%d")

        # 1. Scrape Apify
        st.info("🔄 1/3 جاري سحب المنشورات والحسابات تلقائياً عبر Apify...")
        brand_data = scrape_instagram_account(brand_ig_url, "brand")
        competitor_1_data = scrape_instagram_account(comp1_ig_url, "competitor") if comp1_ig_url else {"source": "apify", "posts": []}
        competitor_2_data = scrape_instagram_account(comp2_ig_url, "competitor") if comp2_ig_url else {"source": "apify", "posts": []}

        # 2. Collect Ad Library Data
        st.info("🔍 2/3 جاري ربط وتجميع روابط وسجلات Meta Ad Library...")
        ad_library_data = collect_meta_ad_library(brand_name, comp1_name, comp2_name)

        # 3. Format Internal Metrics JSON
        internal_metrics = {
            "instagram_insights": {"reach": in_reach, "clicks": in_clicks, "watch_time": in_watch_time} if (in_reach or in_clicks or in_watch_time) else [],
            "meta_ads_manager": {"spend": in_spend, "leads": in_leads, "purchases": in_sales} if (in_spend or in_leads or in_sales) else [],
            "tiktok_analytics": [],
            "google_analytics": [],
            "crm": [],
            "sales": []
        }

        # JSON Serialization
        brand_data_json = json.dumps(brand_data, ensure_ascii=False, default=str)
        competitor_1_data_json = json.dumps(competitor_1_data, ensure_ascii=False, default=str)
        competitor_2_data_json = json.dumps(competitor_2_data, ensure_ascii=False, default=str)
        ad_library_data_json = json.dumps(ad_library_data, ensure_ascii=False, default=str)
        internal_metrics_json = json.dumps(internal_metrics, ensure_ascii=False, default=str)

        # 4. Construct Strict System Prompt
        st.info("🧠 3/3 جاري تحليل الداتا وتعبئة التقرير الشامل عبر الذكاء الاصطناعي...")

        analysis_prompt = f"""أنت محلل محترف في Social Media Audit وBrand Strategy.

ستقوم بتحليل بيانات حقيقية تم جمعها تلقائيًا من:
1. Apify للمنشورات والحسابات العامة.
2. Meta Ad Library للإعلانات العامة.
3. أي بيانات داخلية متاحة داخل النظام.

اسم البراند: {brand_name}
فترة التحليل: من {analysis_start} إلى {analysis_end}
تاريخ جمع البيانات: {collected_at}

بيانات البراند:
{brand_data_json}

بيانات المنافس الأول:
{competitor_1_data_json}

بيانات المنافس الثاني:
{competitor_2_data_json}

إعلانات Meta Ad Library:
{ad_library_data_json}

البيانات الداخلية المتاحة:
{internal_metrics_json}

قواعد أساسية لا يمكن مخالفتها:
1. استخدم البيانات الموجودة في المدخلات فقط.
2. ممنوع اختلاق أي:
- أرقام - روابط - مشاهدات - وصول - إنفاق - عملاء - مبيعات - نتائج حملات - أعمار جمهور - مدن - أسماء حملات - تقييمات - معلومات عن المنافسين
3. إذا لم توجد المعلومة، اكتب: "غير متاح في البيانات المجمعة".
4. لا تستخدم عدد الإعجابات كبديل لعدد المشاهدات.
5. لا تستخدم عدد التعليقات كبديل لعدد المشاركات أو الحفظ.
6. إذا كانت المشاهدات غير متاحة، لا تحسب متوسط مشاهدات.
7. لا تقل إن إعلانًا ناجح لمجرد ظهوره في Meta Ad Library.
8. لا تقل إن المنافس أنفق مبلغًا معينًا إلا إذا كان الرقم موجودًا صراحةً في البيانات المرسلة.
9. لا تعتبر Meta Ad Library مصدرًا لنتائج الحملات أو عدد العملاء أو المبيعات.
10. Meta Ad Library تستخدم فقط لتحليل المعلومات الظاهرة عن الإعلان، مثل:
- نص الإعلان - العنوان - الوصف - الدعوة لاتخاذ إجراء - نوع التصميم - تاريخ بدء الإعلان - تاريخ انتهاء الإعلان إن وجد - المنصات - الرابط العام للإعلان - الرابط المقصود إن وجد
11. لا تعرض أي رابط إلا إذا كان موجودًا فعلًا في البيانات.
12. إذا كان الرابط غير موجود، اكتب: "لا يوجد رابط متاح".
13. لا تقل إن التحليل يغطي آخر 90 يومًا إلا إذا كان كل منشور يحمل تاريخًا وتمت فلترته فعليًا داخل الفترة.
14. لا تستخدم أي معلومة من معرفتك العامة عن البراند أو المنافسين باعتبارها حقيقة.
15. افصل بين:
- بيانات مؤكدة - أرقام محسوبة - استنتاجات - فرضيات - توصيات
16. كل استنتاج يجب أن يوضح الدليل الذي بُني عليه.
17. كل توصية يجب أن تكون عملية وقابلة للتنفيذ.
18. كل توصية يجب أن تحتوي على:
- الإجراء المطلوب - السبب - الدليل - مدة التنفيذ - مؤشر قياس النجاح
19. إذا كانت البيانات قليلة أو ناقصة، اخفض مستوى الثقة واكتب السبب.
20. لا تعرض تقريرًا عامًا أو إنشائيًا لا يرتبط بالبيانات.
21. لا تكرر المعلومات نفسها في أكثر من قسم.
22. لا تستخدم لغة مؤكدة عند وجود نقص في البيانات.

استخدم:
- تشير البيانات المتاحة إلى...
- يبدو من المنشورات المتاحة...
- يمكن اختبار فرضية...
- لا يمكن التأكد من ذلك من البيانات الحالية...

احسب فقط المؤشرات التي يمكن حسابها من البيانات الموجودة. مثلًا:
- عدد المنشورات - عدد المنشورات حسب النوع - متوسط الإعجابات إذا كانت الإعجابات موجودة - متوسط التعليقات إذا كانت التعليقات موجودة - متوسط المشاهدات إذا كانت المشاهدات موجودة - معدل التفاعل فقط إذا كانت عناصر المعادلة متاحة - أعلى المنشورات حسب المقياس المتاح فعلًا.

إذا كان هناك أكثر من مصدر لنفس المعلومة، اختر المصدر الأكثر مباشرة، واذكر التعارض إذا اختلفت القيم.

أخرج التقرير باللغة العربية وبأسلوب واضح ومناسب لصاحب عمل غير متخصص، مستخدماً تنسيق Markdown منظم جداً ويحتوي على كافة الأقسام التالية بالترتيب:

أولًا: الملخص التنفيذي
ثانيًا: نطاق التحليل وجودة البيانات
ثالثًا: تحليل البراند
رابعًا: تحليل المنافس الأول
خامسًا: تحليل المنافس الثاني
سادسًا: مقارنة البراند بالمنافسين
سابعًا: تحليل إعلانات Meta Ad Library (مع إضافة الملاحظة الإلزامية)
ثامنًا: تحليل الأداء الداخلي
تاسعًا: تحليل المحتوى
عاشرًا: SWOT
الحادي عشر: استراتيجية 30 و60 و90 يومًا
الثاني عشر: خطة المحتوى
الثالث عشر: خطة الاختبارات
الرابع عشر: البيانات المطلوبة مستقبلًا
الخامس عشر: الخلاصة
"""

        try:
            ai_response = model.generate_content(analysis_prompt)
            st.success("✅ تم إكمال الـ Audit بنجاح وتطبيق شروط الخصوصية وجودة البيانات!")
            st.markdown(ai_response.text)

            # Save Audit Run to Supabase DB
            try:
                db_payload = {
                    "brand_name": brand_name,
                    "inputs": {"brand_url": brand_ig_url, "comp1": comp1_ig_url, "comp2": comp2_ig_url},
                    "scraped_data": brand_data,
                    "strategy_output": str(ai_response.text)
                }
                supabase.table("strategy_projects").insert(db_payload).execute()
                st.info("💾 تم حفظ التقرير بجدول `strategy_projects` في قاعدة البيانات.")
            except Exception as db_err:
                pass
        except Exception as ai_err:
            st.error(f"❌ حدث خطأ أثناء التوليد: {str(ai_err)}")

elif project_mode == "استعراض المشاريع السابقة":
    st.header("📂 تقارير الـ Audit المحفوظة")
    try:
        response = supabase.table("strategy_projects").select("*").order("created_at", descending=True).execute()
        projects = response.data
        if projects:
            project_names = [f"{p['brand_name']} - {str(p['created_at'])[:10]}" for p in projects]
            selected_proj = st.selectbox("اختر تقريراً لعرضه:", project_names)
            idx = project_names.index(selected_proj)
            st.subheader(f"📊 تقرير الـ Audit الخاص بـ {projects[idx]['brand_name']}")
            st.markdown(projects[idx]['strategy_output'])
        else:
            st.write("لا توجد مشاريع محفوظة حالياً.")
    except Exception as e:
        st.error(f"خطأ في جلب المشاريع من قاعدة البيانات: {str(e)}")
