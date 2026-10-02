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
    <h1>🎯 أداة الـ Audit والاستراتيجية المنفصلة حسب المنصات</h1>
    <p>تحليل تفصيلي لكل منصة على حدة مع تخصيص كامل للتواريخ وأهداف الحملات الدقيقة</p>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("### 📂 إدارة المشاريع")
project_mode = st.sidebar.radio("اختر النمط المطلوب:", ["مشروع جديد", "استعراض المشاريع السابقة"])

if project_mode == "مشروع جديد":
    with st.form("per_platform_audit_form"):
        tab1, tab2 = st.tabs(["1️⃣ حسابات البراند والمنافسين وفترة التحليل", "2️⃣ الأداء الإعلاني والداخلي منفصل لكل منصة"])
        
        with tab1:
            col1, col2 = st.columns(2)
            with col1:
                brand_name = st.text_input("اسم البراند الرئيسي *", placeholder="مثال: Brand X")
                brand_url = st.text_input("رابط البراند الرئيسي (Instagram / Facebook / Web) *")
                
                st.markdown("**📅 نطاق تاريخ التحليل:**")
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
            st.markdown("### 📢 تفاصيل الحملة الإعلانية (Ads Manager)")
            c1, c2, c3 = st.columns(3)
            with c1:
                ad_spend = st.number_input("الإنفاق الإعلاني الإجمالي ($)", min_value=0.0, value=0.0)
                ad_objective = st.selectbox("هدف الحملة الإعلانية الصريح:", [
                    "لم يتم إجراء إعلانات", 
                    "زيادة إعجابات الصفحة (Get more Page Likes)", 
                    "زيادة المتابعين (Followers)", 
                    "رسائل (Messages)", 
                    "زيارات موقع / واتساب (Traffic)", 
                    "تفاعل مع المنشورات (Post Engagement)", 
                    "مشاهدات الفيديو (Video Views)", 
                    "عملاء محتملين (Leads)", 
                    "مبيعات / شراء (Sales)", 
                    "هدف آخر"
                ])
            with c2:
                ad_results_count = st.number_input("عدد النتائج المتحققة (مثلاً: عدد إعجابات الصفحة/الرسائل)", min_value=0, value=0)
                cost_per_result = st.number_input("تكلفة النتيجة الواحدة ($ Cost Per Result)", min_value=0.0, value=0.0)
            with c3:
                custom_objective = st.text_input("اكتب هدف الحملة بالتفصيل (إذا اخترت هدف آخر)")

            st.markdown("---")
            st.markdown("### 📊 الأداء الداخلي والوصول (منفصل لكل منصة على حدة)")
            
            st.markdown("**1️⃣ منصة الفيسبوك (Facebook Insights):**")
            fb_col1, fb_col2 = st.columns(2)
            with fb_col1:
                fb_reach = st.number_input("وصول الفيسبوك (Facebook Reach)", min_value=0, value=0)
            with fb_col2:
                fb_clicks = st.number_input("نقرات الفيسبوك / Clicks", min_value=0, value=0)

            st.markdown("**2️⃣ منصة الإنستجرام (Instagram Insights):**")
            ig_col1, ig_col2 = st.columns(2)
            with ig_col1:
                ig_reach = st.number_input("وصول الإنستجرام (Instagram Reach)", min_value=0, value=0)
            with ig_col2:
                ig_clicks = st.number_input("زيارات البروفايل / النقرات على الإنستجرام", min_value=0, value=0)

            st.markdown("**3️⃣ منصات أخرى (TikTok / LinkedIn / YouTube):**")
            other_col1, other_col2 = st.columns(2)
            with other_col1:
                other_reach = st.number_input("وصول المنصات الأخرى (Reach)", min_value=0, value=0)
            with other_col2:
                other_watch_time = st.text_input("ساعات المشاهدة (Watch Time - إن وجدت)")

        submitted = st.form_submit_button("🚀 بدء تحليل المنصات وتوليد الـ Audit")

    if submitted and brand_name and brand_url:
        st.info("🔄 1/2 جاري فحص وسحب بيانات الحسابات...")
        
        brand_data = scrape_social_account(brand_url, "brand")
        comp1_data = scrape_social_account(comp1_url, "competitor_1") if comp1_url else {"posts": []}
        comp2_data = scrape_social_account(comp2_url, "competitor_2") if comp2_url else {"posts": []}

        final_objective = custom_objective if (ad_objective == "هدف آخر" and custom_objective) else ad_objective

        internal_metrics = {}
        if ad_spend > 0 or final_objective != "لم يتم إجراء إعلانات":
            internal_metrics["ads_performance"] = {
                "spend": ad_spend,
                "objective": final_objective,
                "results_count": ad_results_count,
                "cost_per_result": cost_per_result
            }
        
        internal_metrics["facebook_insights"] = {"reach": fb_reach, "clicks": fb_clicks} if (fb_reach or fb_clicks) else "غير مدخلة"
        internal_metrics["instagram_insights"] = {"reach": ig_reach, "clicks": ig_clicks} if (ig_reach or ig_clicks) else "غير مدخلة"
        internal_metrics["other_platforms_insights"] = {"reach": other_reach, "watch_time": other_watch_time} if (other_reach or other_watch_time) else "غير مدخلة"

        brand_data_json = json.dumps(brand_data, ensure_ascii=False, default=str)
        comp1_data_json = json.dumps(comp1_data, ensure_ascii=False, default=str)
        comp2_data_json = json.dumps(comp2_data, ensure_ascii=False, default=str)
        internal_metrics_json = json.dumps(internal_metrics, ensure_ascii=False, default=str)

        st.info("🧠 2/2 جاري تحليل البيانات منفصلة لكل منصة...")

        analysis_prompt = f"""أنت استشاري خبير ومحترف في Social Media Audit وBrand Strategy.

قم بإجراء تحليل حقيقي ومستقل لكل منصة على حدة بناءً على المعطيات التالية:

اسم البراند الرئيسي: {brand_name} (الرابط: {brand_url})
فترة التحليل المحددة يدوياً من المستخدم: من {start_date} إلى {end_date}

بيانات البراند المسحوبة:
{brand_data_json}

بيانات المنافس الأول ({comp1_name}):
{comp1_data_json}

بيانات المنافس الثاني ({comp2_name if comp2_name else 'لا يوجد منافس ثاني'}):
{comp2_data_json}

البيانات الإعلانية والداخلية المفصلة لكل منصة:
{internal_metrics_json}

قواعد صارمة لا يمكن مخالفتها:
1. حلل كل منصة بشكل مستقل تماماً (Facebook منفصل، Instagram منفصل، إلخ) وممنوع نهائياً دمج أو تجميع الوصول (Reach) للمنصات في رقم واحد.
2. التزم بهدف الحملة الإعلانية المختار صراحةً: ({final_objective}). حلل أداء الإعلان وتكلفة النتيجة بناءً على هذا الهدف فقط (مثلاً إذا كان الهدف Get More Page Likes، يكون التقييم لمعدل تكلفة الإعجاب الواحد ولا تربطه بالمبيعات أو الليدز).
3. التزم بالفترة الزمنية المحددة صراحةً: من {start_date} إلى {end_date}.
4. إذا كانت أي منصة أو أي خانة غير مدخلة، اكتب "غير مدخلة" ولا تخترع أو تفترض أرقاماً لها.

أخرج التقرير باللغة العربية بأسلوب احترافي ودقيق.
"""

        try:
            ai_response = model.generate_content(analysis_prompt)
            st.success("✅ تم استخراج التقرير بنجاح وبتحليل منفصل لكل منصة!")
            st.markdown(ai_response.text)

            try:
                db_payload = {
                    "brand_name": brand_name,
                    "inputs": {"brand_url": brand_url, "comp1": comp1_url, "comp2": comp2_url, "start_date": str(start_date), "end_date": str(end_date), "objective": final_objective},
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
