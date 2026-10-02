import streamlit as st
import google.generativeai as genai
from supabase import create_client
from apify_client import ApifyClient
import json
import datetime

# ---------------------------------------------------------
# 1. Page Configuration & Custom Styling
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

    .main-header {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        padding: 24px;
        border-radius: 12px;
        color: #FFFFFF;
        margin-bottom: 20px;
    }
    
    .main-header h1 {
        color: #FFFFFF !important;
        font-weight: 800 !important;
        font-size: 1.6rem !important;
        margin: 0 0 6px 0 !important;
    }

    div[data-testid="stForm"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 12px !important;
        padding: 20px !important;
    }

    div.stButton > button, div[data-testid="stForm"] button {
        width: 100% !important;
        background-color: #2563EB !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
        border-radius: 8px !important;
        padding: 10px 20px !important;
        border: none !important;
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
    model = genai.GenerativeModel('gemini-3.8-flash')
    apify = ApifyClient(apify_key)
    return supabase, model, apify

try:
    supabase, model, apify = init_services()
except Exception as e:
    st.error("⚠️ خطأ في الاتصال بالخدمات السحابية. يرجى التأكد من ضبط الـ Secrets.")

# ---------------------------------------------------------
# 3. Flexible Scraping Logic
# ---------------------------------------------------------
def scrape_social_account(url, account_type="brand"):
    """Safely scrapes data if URL is Instagram, or structures metadata if Facebook/Web."""
    if not url:
        return {"source": "manual", "account_type": account_type, "url": "", "posts": []}
    
    if "instagram.com" in url.lower():
        cleaned_handle = url.replace("https://instagram.com/", "").replace("https://www.instagram.com/", "").replace("/", "").strip()
        try:
            run_input = {
                "directUrls": [f"https://www.instagram.com/{cleaned_handle}/"],
                "resultsType": "posts",
                "searchLimit": 15
            }
            run = apify.actor("apify/instagram-post-scraper").call(run_input=run_input)
            items = apify.dataset(run["defaultDatasetId"]).list_items().items
            
            cleaned_posts = []
            for item in items:
                cleaned_posts.append({
                    "url": item.get("url") or item.get("postUrl"),
                    "type": item.get("type"),
                    "likes": item.get("likesCount"),
                    "comments": item.get("commentsCount"),
                    "views": item.get("videoViewCount") or item.get("playCount"),
                    "caption": (item.get("caption") or "")[:150]
                })
            return {"source": "apify_instagram", "account_type": account_type, "url": url, "posts": cleaned_posts}
        except Exception:
            return {"source": "instagram_link", "account_type": account_type, "url": url, "posts": []}
    else:
        return {"source": "facebook_or_web_link", "account_type": account_type, "url": url, "posts": []}

# ---------------------------------------------------------
# 4. Streamlit UI
# ---------------------------------------------------------
st.markdown("""
<div class="main-header">
    <h1>🎯 أداة الـ Audit والاستراتيجية المرنة</h1>
    <p>تحديد يدوي كامل للتواريخ والمنصات وأهداف الحملات دون أي فرض تلقائي</p>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("### 📂 إدارة المشاريع")
project_mode = st.sidebar.radio("اختر النمط المطلوب:", ["مشروع جديد", "استعراض المشاريع السابقة"])

if project_mode == "مشروع جديد":
    with st.form("custom_dates_audit_form"):
        tab1, tab2 = st.tabs(["1️⃣ حسابات البراند والمنافسين وفترة التحليل", "2️⃣ بيانات الإعلانات والأداء الداخلي (اختياري)"])
        
        with tab1:
            col1, col2 = st.columns(2)
            with col1:
                brand_name = st.text_input("اسم البراند الرئيسي *", placeholder="مثال: Brand X")
                brand_url = st.text_input("رابط البراند الرئيسي (Instagram / Facebook / Web) *")
                
                # تحديد التاريخ يدوياً برغبة المستخدم
                st.markdown("**📅 تحديد نطاق تاريخ التحليل يدوياً:**")
                date_col1, date_col2 = st.columns(2)
                with date_col1:
                    start_date = st.date_input("تاريخ البداية", value=datetime.date.today() - datetime.timedelta(days=90))
                with date_col2:
                    end_date = st.date_input("تاريخ النهاية", value=datetime.date.today())

            with col2:
                comp1_name = st.text_input("اسم المنافس الأول *")
                comp1_url = st.text_input("رابط المنافس الأول (أي منصة: IG / FB / Web) *")
                comp2_name = st.text_input("اسم المنافس الثاني (اختياري)")
                comp2_url = st.text_input("رابط المنافس الثاني (اختياري)")
        
        with tab2:
            st.caption("أدخل البيانات المتاحة لديك فقط، واترك باقي الحقول فارغة:")
            c1, c2 = st.columns(2)
            with c1:
                ad_spend = st.number_input("الإنفاق الإعلاني ($)", min_value=0.0, value=0.0)
                ad_objective = st.selectbox("هدف الحملة الإعلانية الرئيسي:", [
                    "لم يتم إجراء إعلانات", 
                    "رسائل (Messages)", 
                    "عملاء محتملين (Leads)", 
                    "زيارات موقع / واتساب (Traffic)", 
                    "تفاعل (Engagement)", 
                    "مبيعات / شراء (Sales/Purchases)", 
                    "مكالمات (Calls)"
                ])
                ad_results_count = st.number_input("عدد النتائج المتحققة", min_value=0, value=0)
                cost_per_result = st.number_input("تكلفة النتيجة الواحدة ($ Cost Per Result)", min_value=0.0, value=0.0)
            
            with c2:
                in_reach = st.number_input("الوصول الإجمالي (Reach) - إن وجد", min_value=0, value=0)
                in_clicks = st.number_input("نقرات الموقع / الواتساب - إن وجد", min_value=0, value=0)
                watch_time_input = st.text_input("ساعات المشاهدة (Watch Time) - اختياري")

        submitted = st.form_submit_button("🚀 بدء تحليل الحسابات وتوليد الـ Audit")

    if submitted and brand_name and brand_url:
        st.info("🔄 1/2 جاري فحص وسحب منشورات الحسابات المتاحة...")
        
        brand_data = scrape_social_account(brand_url, "brand")
        comp1_data = scrape_social_account(comp1_url, "competitor_1") if comp1_url else {"posts": []}
        comp2_data = scrape_social_account(comp2_url, "competitor_2") if comp2_url else {"posts": []}

        internal_metrics = {}
        if ad_spend > 0 or ad_objective != "لم يتم إجراء إعلانات":
            internal_metrics["ads_performance"] = {
                "spend": ad_spend,
                "objective": ad_objective,
                "results_count": ad_results_count,
                "cost_per_result": cost_per_result
            }
        if in_reach > 0:
            internal_metrics["reach"] = in_reach
        if in_clicks > 0:
            internal_metrics["clicks"] = in_clicks
        if watch_time_input:
            internal_metrics["watch_time"] = watch_time_input

        brand_data_json = json.dumps(brand_data, ensure_ascii=False, default=str)
        comp1_data_json = json.dumps(comp1_data, ensure_ascii=False, default=str)
        comp2_data_json = json.dumps(comp2_data, ensure_ascii=False, default=str)
        internal_metrics_json = json.dumps(internal_metrics, ensure_ascii=False, default=str)

        st.info("🧠 2/2 جاري إعداد التقرير المخصص بناءً على تواريخك ومعطياتك الفعلية...")

        analysis_prompt = f"""أنت استشاري خبير في Social Media Audit وBrand Strategy.

قم بإجراء تحليل حقيقي ودقيق بناءً على المعطيات التالية:

اسم البراند الرئيسي: {brand_name} (الرابط: {brand_url})
فترة التحليل المحددة يدوياً من المستخدم: من {start_date} إلى {end_date}

بيانات البراند:
{brand_data_json}

بيانات المنافس الأول ({comp1_name}):
{comp1_data_json}

بيانات المنافس الثاني ({comp2_name if comp2_name else 'لا يوجد منافس ثاني'}):
{comp2_data_json}

البيانات الإعلانية والداخلية المدخلة صراحةً من المستخدم:
{internal_metrics_json}

قواعد صارمة للتحليل:
1. فترة التحليل محددة صراحةً من المستخدم كالتالي: من {start_date} إلى {end_date}. التزم بهذه التواريخ تماماً في التقرير ولا تغيرها.
2. اعتمد أهداف الحملات ونوع المنصات المدخلة كما هي بدون فرض منصة أو هدف معين.
3. إذا كانت الخانات الاختيارية غير مدخلة، اكتب "غير مدخلة ضمن البيانات" ولا تخترع أرقاماً لها.

أخرج التقرير باللغة العربية وبأسلوب منظم وشامل يغطي كافة الأقسام الرئيسية للـ Audit والاستراتيجية.
"""

        try:
            ai_response = model.generate_content(analysis_prompt)
            st.success("✅ تم استخراج التقرير بنجاح وفق التواريخ التي حددتها!")
            st.markdown(ai_response.text)

            try:
                db_payload = {
                    "brand_name": brand_name,
                    "inputs": {"brand_url": brand_url, "comp1": comp1_url, "comp2": comp2_url, "start_date": str(start_date), "end_date": str(end_date)},
                    "scraped_data": brand_data,
                    "strategy_output": str(ai_response.text)
                }
                supabase.table("strategy_projects").insert(db_payload).execute()
                st.info("💾 تم حفظ التقرير في قاعدة البيانات.")
            except Exception:
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
