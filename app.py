import streamlit as st
import google.generativeai as genai
from supabase import create_client
from apify_client import ApifyClient
import json

st.set_page_config(page_title="Strategy Mentoring - Full Audit & Strategy", layout="wide")

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

st.title("📊 Strategy Mentoring - Automated Complete Audit Tool")

# Sidebar
st.sidebar.header("📁 إدارة المشاريع")
project_mode = st.sidebar.radio("اختر النمط:", ["مشروع جديد", "استعراض المشاريع السابقة"])

if project_mode == "مشروع جديد":
    st.header("📝 إدخال البيانات الأساسية (والـ AI يحلل ويستكمل كافة المخرجات)")
    
    with st.form("exact_structured_form"):
        tab1, tab2, tab3 = st.tabs(["1️⃣ البراند والمنصات", "2️⃣ المنافس والسوق", "3️⃣ الأرقام الداخلية (اختياري)"])
        
        with tab1:
            col1, col2 = st.columns(2)
            with col1:
                brand_name = st.text_input("اسم البراند الرئيسي *", placeholder="مثال: Brand X")
                product_service = st.text_input("المنتج / الخدمة *", placeholder="مثال: كورسات / كافيه / ملابس")
                geo_coverage = st.text_input("الدولة / المدينة / التغطية الجغرافية *", placeholder="مثال: مصر - القاهرة")
                main_objective = st.text_input("الهدف الرئيسي اللى فى البريف (30/60/90 يوم) *")
                expected_audience = st.text_input("عدد الجمهور المتوقع للبراند")
            with col2:
                ig_handle = st.text_input("Instagram Username / Link")
                fb_url = st.text_input("Facebook Page Link")
                tiktok_handle = st.text_input("TikTok Username / Link")
                linkedin_url = st.text_input("LinkedIn Link")
                yt_url = st.text_input("YouTube Channel Link")

        with tab2:
            col_a, col_b = st.columns(2)
            with col_a:
                comp_name = st.text_input("اسم المنافس")
                comp_website = st.text_input("لينك الموقع/اللاندنج للمنافس")
                comp_ig = st.text_input("لينك Instagram للمنافس")
                comp_fb = st.text_input("Facebook/TikTok/Google Maps للمنافس")
            with col_b:
                market_insights = st.text_area("عينة تعليقات/اعتراضات/شكاوى الجمهور من الجروبات أو التقييمات")

        with tab3:
            c1, c2, c3 = st.columns(3)
            with c1:
                followers_count = st.text_input("عدد المتابعين الحالي والنمو")
                reach_period = st.text_input("Reach والتفاعلات خلال الفترة")
            with c2:
                profile_visits = st.text_input("Profile Visits / Clicks")
                content_mix_input = st.text_input("تنوع المحتوى شهرياً (كام ريل/كاروسيل/صورة/تكست)")
            with c3:
                ad_spend = st.number_input("اتصرف كام على Meta Ads ($)", min_value=0.0, value=0.0)
                ad_results = st.text_input("هدف الإعلانات والنتائج و Cost Per Result")

        submitted = st.form_submit_button("🚀 بدء الـ Audit واستخراج المخرجات الكاملة")

    if submitted and brand_name:
        st.info("🔄 جاري سحب البيانات عبر Apify...")
        scraped_data = {}
        if ig_handle:
            try:
                run_input = {"directUrls": [f"https://www.instagram.com/{ig_handle}/"], "resultsType": "details"}
                run = apify.actor("apify/instagram-profile-scraper").call(run_input=run_input, timeout_secs=25)
                scraped_data['brand_ig'] = apify.dataset(run["defaultDatasetId"]).list_items().items
            except Exception as e:
                scraped_data['ig_error'] = str(e)

        st.info("🧠 جاري إعداد التقرير المكتمل بنسبة 100% وتعبئة كافة الجداول والبندود المطلوبة...")

        full_output_prompt = f"""
        أنت Senior Marketing Strategist. قم بإنشاء Audit واستراتيجية تسويقية متكاملة ومشروحة بدقة للبراند '{brand_name}'.
        يجب عليك الالتزام بالحقول والبنية التالية حرفياً، وتعبئة كافة البيانات المطلوبة إما من المدخلات أو استنتاجه وتحليله بناءً على معايير السوق وتحديثات DataReportal والداتا المسحوبة.

        عرض التقرير يكون بتنسيق Markdown احترافي، ويشمل كل البنود بدون اختصار:

        # Strategy Mentoring - {brand_name}

        ## 1- Situation Analysis

        ### platforms analysis
        | البند | البيان / التحليل |
        | :--- | :--- |
        | **لينك/يوزر الحساب** | FB: {fb_url} \| IG: {ig_handle} \| TikTok: {tiktok_handle} \| LinkedIn: {linkedin_url} \| YT: {yt_url} |
        | **عدد المتابعين الحالي** | {followers_count if followers_count else 'استخراج بناءً على المنصات'} |
        | **نمو المتابعين خلال الفترة** | زيادة / نقص وتقييم معدل النمو |
        | **Reach خلال الفترة** | {reach_period if reach_period else 'تقدير بناءً على النشاط والميزانية'} |
        | **Engagements خلال الفترة** | لايك / كومنت / شير / سيف |
        | **Profile visits / Clicks** | {profile_visits if profile_visits else 'تقدير زوار البروفايل ونقرات الواتساب/الموقع'} |
        | **تنوع المحتوى شهرياً** | {content_mix_input if content_mix_input else 'توزيع موصى به: كام ريل - كام كاروسيل - كام صورة - كام تكست'} |
        | **أفضل ٥ Reels من حيث المشاهدات** | تحليل واستخراج أداء أفضل 5 ريلز |
        | **أفضل ٥ بوستات من حيث التفاعل** | تحليل واستخراج أداء أفضل 5 بوستات تفاعلاً |
        | **إحصائيات متقدمة بالفيديو** | Watch Time \| Average Play Time \| 3-second Views |
        | **الجمهور الأساسي** | المدن / السن / النوع |
        | **عدد الجمهور المتوقع للبراند** | {expected_audience if expected_audience else 'تقدير حجم السوق المستهدف'} |
        | **صرف Meta Ads خلال الفترة** | {ad_spend} $ |
        | **Objective للحملات** | (Messages/Leads/Calls/Traffic) |
        | **عدد النتائج و Cost per result** | {ad_results if ad_results else 'تقدير النتائج وتكلفة النتيجة بناء على المجال'} |

        ### Audience Analysis
        * **كم ساعة يقضي المستخدم على السوشيال ميديا؟**: (من DataReportal لدولة {geo_coverage})
        * **ترتيب المنصات في البلد؟**: (من DataReportal لدولة {geo_coverage})
        * **نوع المحتوى المفضل؟**: (من DataReportal)
        * **نسبة ذكور / إناث**: (من platform insights / DataReportal)
        * **الفئة العمرية وأهم المدن**:
        * **المستوى الإقتصادي**:
        * **المشاكل**: (من AnswerThePublic / الجروبات / الكومنتات: {market_insights})
        * **الاهتمامات ودوافع الشراء**: (من Meta Insights والكومنتات)
        * **المؤثرين المناسبين**:
        * **سلوك المستخدم على Facebook**:
        * **نوع المحتوى المفضل على Instagram (Explore)**:
        * **نوع الفيديوهات والتريند على TikTok (Creative Center)**:
        * **طريقة الشراء وسرعة القرار**: (أونلاين/أوفلاين - سريع/بياخد وقت)
        * **الاعتراضات وعوامل الثقة (إيه اللي يطمنه)**:

        ### competitor analysis (المنافس: {comp_name})
        | البند | تفاصيل المنافس ({comp_name}) |
        | :--- | :--- |
        | **روابط المنافس** | الموقع: {comp_website} \| IG: {comp_ig} \| FB/Maps: {comp_fb} |
        | **التغطية والجمهور المستهدف** | الدولة/المدينة - السن والنوع والمكان |
        | **أقرب 3 خدمات/منتجات شبهنا** | 1. ... \| 2. ... \| 3. ... |
        | **Positioning & Offer و USP** | تموضعه في السوق، العرض الرئيسي، والسبب المباشر لاختياره |
        | **Proof و الباقات والأسعار** | أدلة إثبات الكلام، العروض/الباقات (Bundles)، وهل الأسعار معلنة؟ |
        | **أقوى CTA وطريقة الوصول للـ Offer** | (واتساب / فورم / مكالمة / حجز أونلاين) وهل يطلب بيانات؟ |
        | **Nurture وميزة الفانل** | (Auto-reply / رسائل / Newsletter) والميزة الواضحة |
        | **تنوع المحتوى شهرياً و Tone of Voice** | تعليمي-أوفر-بروف-ترند + نبرة الصوت واستخدام UGC |
        | **أفضل 5 Reels وأفضل 5 بوستات** | روابط/عناوين وViews وEngagements تقريبية |
        | **أكثر 3 Topics و Content Gaps** | المواضيع المتكررة والفجوات التي أهملها المنافس |
        | **Meta Ad Library Analysis** | أمثلة الإعلانات، أقوى Angle، نوع الكرياتيف، والعروض المتكررة |
        | **Google Ratings والريفيوز** | التقييم، عدد الريفيوز، أهم 3 إيجابيات، أهم 3 سلبيات، وأسلوب وسرعة الرد |
        | **ملخص المقارنة والقرارات** | **نقط تفوقنا عليه**: (1-3 نقاط) <br> **نقط تفوقه علينا**: (1-3 نقاط) <br> **فرصة Quick Win**: ... |

        ### SWOT Analysis
        * **Strengths (نقاط القوة)**:
        * **Weaknesses (نقاط الضعف)**:
        * **Opportunities (الفرص)**:
        * **Threats (التهديدات)**:

        ---

        ## 2- Customer journey

        * **درجة الوعي (Awareness Level)**:
          - هل هو غير واعي بالمشكلة؟
          - هل هو واعي بالمشكلة فقط؟
          - هل هو واعي بالحل؟
          - هل هو واعي بالبراند نفسه؟
        * **رحلة العميل (Customer Journey)**:
          - أول نقطة احتكاك:
          - ماذا يفعل قبل الشراء؟ (تسلسل الأسئلة والترددات)
          - ما الذي يمنعه من القرار؟ (اعتراضات الجمهور)
          - ما الذي يدفعه للقرار النهائي؟ (آخر خطوة قبل الشراء)

        ---

        ## 3- Objectives + key results (KPI)

        * **بيانات الهدف**: الهدف الرئيسي: {main_objective} \| المنتج: {product_service} \| السوق: {geo_coverage} \| المدة: (30/60/90 يوم)
        * **الأهداف الاستراتيجية (3 أهداف SMART + الـ KPI لكل هدف)**:
          1. **الهدف الأول**: ... (KPI الرئيسي: ...)
          2. **الهدف الثاني**: ... (KPI الرئيسي: ...)
          3. **الهدف الثالث**: ... (KPI الرئيسي: ...)

        ---

        ## 4- Customer (Segment & Buyer Persona)

        قم بتحديد 4 Segments تفصيلية تشمل: (Interest or need + location + Age and gender + Pain Point + Decision Trigger):
        1. **Segment 1**:
        2. **Segment 2**:
        3. **Segment 3**:
        4. **Segment 4**:
        """

        try:
            ai_response = model.generate_content(full_output_prompt)
            st.success("✅ تم استخراج التقرير بالكامل وحفظ الجداول!")
            st.markdown(ai_response.text)
            
            try:
                db_payload = {
                    "brand_name": brand_name,
                    "inputs": {"geo": geo_coverage, "objective": main_objective, "ad_spend": ad_spend},
                    "scraped_data": json.loads(json.dumps(scraped_data, default=str)),
                    "strategy_output": str(ai_response.text)
                }
                supabase.table("strategy_projects").insert(db_payload).execute()
                st.info("💾 تم حفظ التقرير في قاعدة البيانات بنجاح.")
            except Exception as db_err:
                pass
        except Exception as ai_err:
            st.error(f"❌ حدث خطأ أثناء التوليد: {str(ai_err)}")

elif project_mode == "استعراض المشاريع السابقة":
    st.header("📂 المشاريع المحفوظة")
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
