import streamlit as st
import google.generativeai as genai
from supabase import create_client
from apify_client import ApifyClient
import json

st.set_page_config(page_title="Strategy Mentoring - 90 Days Multi-Competitor Audit", layout="wide")

# 1. Initialize Services
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

st.title("📊 Strategy Mentoring - 90 Days Multi-Competitor Audit & Strategy")

# Navigation Sidebar
st.sidebar.header("📁 إدارة المشاريع")
project_mode = st.sidebar.radio("اختر النمط:", ["مشروع جديد", "استعراض المشاريع السابقة"])

if project_mode == "مشروع جديد":
    st.header("🎯 مدخلات التحليل والـ Audit (خلال آخر ٩٠ يومًا)")
    
    with st.form("exact_90days_2comp_audit_form"):
        # --- 1. BRAND INPUTS ---
        st.subheader("1️⃣ بيانات البراند الرئيسي (منصات أساسية واختيارية)")
        col1, col2 = st.columns(2)
        with col1:
            brand_name = st.text_input("اسم البراند الرئيسي *")
            product_service = st.text_input("المنتج / الخدمة *")
            geo_coverage = st.text_input("الدولة / المدينة / التغطية الجغرافية *")
            main_objective = st.text_input("الهدف الرئيسي اللى فى البريف (لـ 90 يوم) *")
            expected_audience = st.text_input("عدد الجمهور المتوقع للبراند")
        with col2:
            st.markdown("**المنصات الأساسية:**")
            brand_ig = st.text_input("Instagram Username/Link (أساسي للبراند) *")
            brand_fb = st.text_input("Facebook Page URL (أساسي للبراند) *")
            st.markdown("**المنصات الاختيارية:**")
            brand_tiktok = st.text_input("TikTok Username/Link (اختياري للبراند)")
            brand_linkedin = st.text_input("LinkedIn Link (اختياري للبراند)")
            brand_yt = st.text_input("YouTube Link (اختياري للبراند)")

        # --- 2. COMPETITOR 1 INPUTS ---
        st.subheader("2️⃣ بيانات المنافس الأول (Competitor 1)")
        col_c1_a, col_c1_b = st.columns(2)
        with col_c1_a:
            comp1_name = st.text_input("اسم المنافس الأول *")
            comp1_website = st.text_input("لينك الموقع/اللاندنج للمنافس الأول")
            comp1_ig = st.text_input("Instagram Link للمنافس الأول (أساسي) *")
        with col_c1_b:
            comp1_fb = st.text_input("Facebook Link للمنافس الأول (أساسي) *")
            comp1_tiktok = st.text_input("TikTok Link للمنافس الأول (اختياري)")
            comp1_gmaps = st.text_input("Google Maps Link للمنافس الأول")

        # --- 3. COMPETITOR 2 INPUTS ---
        st.subheader("3️⃣ بيانات المنافس الثاني (Competitor 2)")
        col_c2_a, col_c2_b = st.columns(2)
        with col_c2_a:
            comp2_name = st.text_input("اسم المنافس الثاني *")
            comp2_website = st.text_input("لينك الموقع/اللاندنج للمنافس الثاني")
            comp2_ig = st.text_input("Instagram Link للمنافس الثاني (أساسي) *")
        with col_c2_b:
            comp2_fb = st.text_input("Facebook Link للمنافس الثاني (أساسي) *")
            comp2_tiktok = st.text_input("TikTok Link للمنافس الثاني (اختياري)")
            comp2_gmaps = st.text_input("Google Maps Link للمنافس الثاني")

        # --- 4. ADS & QUALITATIVE DATA ---
        st.subheader("4️⃣ البيانات المالية وأبحاث الجمهور (خلال آخر 90 يوم)")
        c1, c2 = st.columns(2)
        with c1:
            ad_spend = st.number_input("اتصرف كام على Meta Ads خلال آخر 90 يوم ($) - اختياري", min_value=0.0, value=0.0)
            ad_objective_results = st.text_input("Objective للحملات والنتائج و Cost Per Result خلال 90 يوم")
        with c2:
            market_notes = st.text_area("أبحاث الجمهور، الكومنتات، الشكاوى، والاعتراضات من الجروبات/الريفيوز")

        submitted = st.form_submit_button("🚀 بدء الـ Audit الشامل وتوليد الاستراتيجية (90 يوم - 2 منافسين)")

    if submitted and brand_name and brand_ig and comp1_name and comp2_name:
        st.info("🔄 جاري سحب البيانات أوتوماتيكياً عبر Apify للحسابات المتاحة...")
        scraped_data = {}
        
        # Try scraping Brand Instagram
        try:
            run_input = {"directUrls": [f"https://www.instagram.com/{brand_ig}/"], "resultsType": "details"}
            run = apify.actor("apify/instagram-profile-scraper").call(run_input=run_input, timeout_secs=25)
            scraped_data['brand_ig'] = apify.dataset(run["defaultDatasetId"]).list_items().items
        except Exception as e:
            scraped_data['ig_error'] = str(e)

        st.info("🧠 جاري تحليل الأداء والتفاعل لآخر ٩٠ يومًا وتوليد التقرير المكتمل كلياً مع المنافسين الاثنين...")

        strict_2comp_prompt = f"""
        أنت Senior Brand Strategist & Growth Director. قم بإجراء Audit كامل واستخراج استراتيجية متكاملة للبراند '{brand_name}' عن فترة **آخر 90 يومًا فقط**.

        المنصات الأساسية للتحليل: Instagram و Facebook.
        المنصات الاختيارية: TikTok, LinkedIn, YouTube (قم بفرز وتحليل مخرجاتها إن وُجدت روابطها).

        بيانات الإدخال:
        - البراند الرئيسي: {brand_name} | المنتج: {product_service} | التغطية: {geo_coverage} | الهدف الرئيسي: {main_objective} | الجمهور المتوقع: {expected_audience}
        - روابط البراند: IG: {brand_ig} | FB: {brand_fb} | TikTok: {brand_tiktok} | LinkedIn: {brand_linkedin} | YT: {brand_yt}
        - المنافس الأول: {comp1_name} | الموقع: {comp1_website} | IG: {comp1_ig} | FB: {comp1_fb} | TikTok: {comp1_tiktok} | Maps: {comp1_gmaps}
        - المنافس الثاني: {comp2_name} | الموقع: {comp2_website} | IG: {comp2_ig} | FB: {comp2_fb} | TikTok: {comp2_tiktok} | Maps: {comp2_gmaps}
        - أداء الإعلانات (آخر 90 يوم): صرف Meta Ads: {ad_spend} $ | النتائج والأهداف: {ad_objective_results}
        - ملاحظات أبحاث السوق والكومنتات: {market_notes}
        - بيانات Scraping: {json.dumps(scraped_data, ensure_ascii=False)}

        المطلوب: التزم حرفياً بالهيكل التالي وقوائمه ومجالاته الـ 50+ باللغة العربية، ودون حذف أو اختصار أي عنصر نهائياً:

        Strategy Mentoring - {brand_name}

        1- Situation Analysis 

         - platforms analysis 
        * لينك/يوزر الحساب: (FB: {brand_fb}, IG: {brand_ig}, TikTok: {brand_tiktok}, LinkedIn: {brand_linkedin}, YT: {brand_yt})
        * عدد المتابعين الحالي
        * نمو المتابعين خلال الفترة (زيادة/نقص خلال آخر 90 يوم)
        * Reach خلال الفترة (خلال آخر 90 يوم)
        * Engagements خلال الفترة (لايك/كومنت/شير/سيف)
        * Profile visits خلال الفترة Website clicks أو WhatsApp clicks (لو متاح)
        * تنوع المحتوى: كام ريل في الشهر - كام كاروسيل في الشهر-كام بوست صورة- كام بوست تكست
        * أفضل ٥ Reels من حيث المشاهدات (خلال آخر 90 يوم)
        * أفضل ٥ بوستات من حيث التفاعل (خلال آخر 90 يوم)
        * إحصائيات متقدمة بالفيديو: Watch Time و Average Play Time و 3-second Views.
        * الجمهور الأساسي (مدن/سن/نوع)
        * عدد الجمهور المتوقع للبراند: {expected_audience}
        * اتصرف كام على Meta Ads خلال الفترة؟ ({ad_spend} $)
        * Objective للحملات كان إيه؟ (Messages/Leads/Calls/Traffic)
        * عدد النتائج (رسائل/ليدز/مكالمات) خلال الفترة
        * Cost per result خلال الفترة

         - Audience Analysis 
        * كم ساعة يقضي المستخدم على السوشيال ميديا؟ من DataReportal (لدولة {geo_coverage})
        * ترتيب المنصات في البلد؟ من DataReportal (لدولة {geo_coverage})
        * نوع المحتوى المفضل؟ من DataReportal
        * نسبة ذكور / إناث من platform insights / data reportal
        * الفئة العمرية من platform insights / data reportal
        * أهم المدن من platform insights / data reportal
        * المستوى الإقتصادي من platform insights / data reportal
        * المشاكل من AnswerThePublic / Groups
        * الاهتمامات من Meta Insights
        * دوافع الشراء من Comments / Survey
        * المؤثرين المناسبين
        * سلوك المستخدم على Facebook من Groups / Comments
        * نوع المحتوى المفضل على Instagram من Explore
        * نوع الفيديوهات والتريند على TikTok من Creative Center (إن وجد)
        * طريقة الشراء أونلاين ولا أوفلاين من Observation
        * سرعة القرار سريع ولا بياخد وقت من Experience
        * الاعتراضات من Comments
        * الثقة (إيه اللي يطمنه) من Reviews

         - competitor analysis
        ملاحظة: قم بتقديم التحليل الكامل أدناه بشكل منفصل ومفصل لكلٍ من: **المنافس الأول ({comp1_name})** و **المنافس الثاني ({comp2_name})**:

        [المنافس الأول: {comp1_name}]
        * اسم المنافس: {comp1_name}
        * لينك الموقع/اللاندنج: {comp1_website}
        * لينك Instagram: {comp1_ig}
        * لينك Facebook: {comp1_fb}
        * لينك TikTok: {comp1_tiktok}
        * Google Business Profile / Maps link: {comp1_gmaps}
        * الدولة/المدينة/التغطية الجغرافية؟
        * مين الجمهور اللي باين إنه مستهدفه؟ (سن - نوع - مكان )
        * أقرب 3 خدمات/منتجات بيبيعها شبهنا
        * Positioning & Offer
        * USP / السبب اللي بيقولك تختاره
        * Proof بيستخدمه لإثبات كلامه؟ 
        * العروض/الباقات (Bundles) اللي عنده؟
        * الأسعار معلنة ولا لأ؟
        * أقوى CTA عنده إيه؟
        * طريقة الوصول للـ Offer: واتساب؟ فورم؟ مكالمة؟ حجز أونلاين؟
        * هل بيطلب بيانات؟ (اسم/موبايل/إيميل) — فين؟
        * هل فيه Nurture/متابعة؟ (Auto-reply/رسائل/Newsletter)
        * ميزة واضحة في الفانل عنده؟
        * كام ريل في الشهر - كام كاروسيل في الشهر-كام بوست صورة- كام بوست تكست (خلال آخر 90 يوم)
        * تنوع المحتوى شهرياً: تعليمي-أوفر-بروف-ترند/لايف
        * أفضل ٥ Reels من حيث المشاهدات (لينك + Views لكل واحد خلال 90 يوم)
        * أفضل ٥ بوستات من حيث التفاعل (لينك + Engagements لكل واحد خلال 90 يوم)
        * أكثر 3 Topics/Angles متكررين عنده
        * Tone of Voice
        * هل بيستخدم UGC/شهادات/قبل-بعد؟ أمثلة (لينكات)
        * إيه الـ Content gaps؟ (حاجة هو مش مغطّيها)
        * Meta Ad Library: أمثلة لآخر إعلاناته (لينكات/سكرينات)
        * أقوى Angle اعلاني واضح؟
        * هل بيستخدم Lead Form ولا Website ولا WhatsApp؟
        * أنواع الكرياتيف: UGC/قبل-بعد/موشن/ستاتيك/كاروسيل ....
        * أي Offers/Promos متكررة في الإعلانات؟
        * Google rating + عدد الريفيوز (لو موجود)
        * أكثر 3 نقاط مدح في الريفيوز (ملخص)
        * أكثر 3 شكاوى/سلبيات (ملخص)
        * هل بيرد على الريفيوز؟ (نعم/لا) + أسلوب الرد
        * سرعة تجاوبه في الرسائل؟
        * ساعات العمل/طرق التواصل الظاهرة؟

        [المنافس الثاني: {comp2_name}]
        * اسم المنافس: {comp2_name}
        * لينك الموقع/اللاندنج: {comp2_website}
        * لينك Instagram: {comp2_ig}
        * لينك Facebook: {comp2_fb}
        * لينك TikTok: {comp2_tiktok}
        * Google Business Profile / Maps link: {comp2_gmaps}
        * الدولة/المدينة/التغطية الجغرافية؟
        * مين الجمهور اللي باين إنه مستهدفه؟ (سن - نوع - مكان )
        * أقرب 3 خدمات/منتجات بيبيعها شبهنا
        * Positioning & Offer
        * USP / السبب اللي بيقولك تختاره
        * Proof بيستخدمه لإثبات كلامه؟ 
        * العروض/الباقات (Bundles) اللي عنده؟
        * الأسعار معلنة ولا لأ؟
        * أقوى CTA عنده إيه؟
        * طريقة الوصول للـ Offer: واتساب؟ فورم؟ مكالمة؟ حجز أونلاين؟
        * هل بيطلب بيانات؟ (اسم/موبايل/إيميل) — فين؟
        * هل فيه Nurture/متابعة؟ (Auto-reply/رسائل/Newsletter)
        * ميزة واضحة في الفانل عنده؟
        * كام ريل في الشهر - كام كاروسيل في الشهر-كام بوست صورة- كام بوست تكست (خلال آخر 90 يوم)
        * تنوع المحتوى شهرياً: تعليمي-أوفر-بروف-ترند/لايف
        * أفضل ٥ Reels من حيث المشاهدات (لينك + Views لكل واحد خلال 90 يوم)
        * أفضل ٥ بوستات من حيث التفاعل (لينك + Engagements لكل واحد خلال 90 يوم)
        * أكثر 3 Topics/Angles متكررين عنده
        * Tone of Voice
        * هل بيستخدم UGC/شهادات/قبل-بعد؟ أمثلة (لينكات)
        * إيه الـ Content gaps؟ (حاجة هو مش مغطّيها)
        * Meta Ad Library: أمثلة لآخر إعلاناته (لينكات/سكرينات)
        * أقوى Angle اعلاني واضح؟
        * هل بيستخدم Lead Form ولا Website ولا WhatsApp؟
        * أنواع الكرياتيف: UGC/قبل-بعد/موشن/ستاتيك/كاروسيل ....
        * أي Offers/Promos متكررة في الإعلانات؟
        * Google rating + عدد الريفيوز (لو موجود)
        * أكثر 3 نقاط مدح في الريفيوز (ملخص)
        * أكثر 3 شكاوى/سلبيات (ملخص)
        * هل بيرد على الريفيوز؟ (نعم/لا) + أسلوب الرد
        * سرعة تجاوبه في الرسائل؟
        * ساعات العمل/طرق التواصل الظاهرة؟

        — ملخص المقارنة بين البراند والمنافسين الاثنين (يطلع منه قرارات) —
        * نقط تفوقنا عليهما (1–3 نقاط)
        * نقط تفوق المنافس الأول والفرص الناتجة عنه
        * نقط تفوق المنافس الثاني والفرص الناتجة عنه
        * فرصة Quick win إستراتيجية

         - SWOT Analysis 
        * Strengths
        * Weaknesses
        * Opportunities
        * Threats

        2- Customer journey 
        * درجة الوعي (Awareness Level)
          - هل هو غير واعي بالمشكلة؟ من كومنتات البوستات / من جروبات الفيسبوك
          - هل هو واعي بالمشكلة فقط؟ من كومنتات البوستات / من جروبات الفيسبوك
          - هل هو واعي بالحل؟ من كومنتات البوستات / من جروبات الفيسبوك
          - هل هو واعي بالبراند نفسه ؟ من خلال داتا 3 شهور سابقة
        * رحلة العميل (Customer Journey)
          - أول نقطة احتكاك تحليل المنصات ومحتوى المنافسين
          - ماذا يفعل قبل الشراء؟ تسلسل الأسئلة والترددات
          - ما الذي يمنعه من القرار؟ اعتراضات الجمهور
          - ما الذي يدفعه للقرار النهائي؟ آخر خطوة قبل الشراء

        3- Objectives + key results (KPI) 
        * الهدف الرئيسي اللى فى البريف: {main_objective}
        * المنتج/الخدمة: {product_service}
        * السوق/المنطقة: {geo_coverage}
        * الفترة الزمنية: 90 يوم
        * الأهداف الاستراتيجية ( 3 أهداف SMART ) + KPI أساسي لكل هدف

        4- Customer (Segment & Buyer Persona) 
        * حدد 4 Segments تفصيلية مع: (Interest or need + location + Age and gender + Pain Point + Decision Trigger).

        قدم التقرير بصيغة واضحة، عميقة وشاملة للغاية دون اختصار.
        """

        try:
            ai_response = model.generate_content(strict_2comp_prompt)
            st.success("✅ تم استخراج التقرير الاستراتيجي الشامل لـ 90 يومًا وللمنافسين الاثنين بنجاح!")
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
                    "scraped_data": json.loads(json.dumps(scraped_data, default=str)),
                    "strategy_output": str(ai_response.text)
                }
                supabase.table("strategy_projects").insert(db_payload).execute()
                st.info("💾 تم حفظ التقرير والمشروع بنجاح في قاعدة البيانات.")
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
