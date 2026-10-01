import streamlit as st
import google.generativeai as genai
from supabase import create_client
from apify_client import ApifyClient
import json

st.set_page_config(page_title="Strategy Mentoring AI - Audit & Strategy", layout="wide")

# Initialize Connections
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

# Sidebar Navigation
st.sidebar.header("📁 إدارة المشاريع")
project_mode = st.sidebar.radio("اختر النمط:", ["مشروع جديد", "استعراض المشاريع السابقة"])

if project_mode == "مشروع جديد":
    st.header("📝 مدخلات المشروع والبيانات المباشرة")
    
    with st.form("exact_strategy_form"):
        # Section 1: Brand & Internal Performance Inputs
        st.subheader("1️⃣ بيانات البراند الرئيسي والأداء الداخلي")
        col1, col2 = st.columns(2)
        with col1:
            brand_name = st.text_input("اسم البراند الرئيسي *")
            brand_url = st.text_input("رابط الموقع / اللاندنج / الواتساب")
            geo_coverage = st.text_input("الدولة / المدينة / التغطية الجغرافية *")
            main_objective = st.text_input("الهدف الرئيسي اللى فى البريف (30/60/90 يوم) *")
            product_service = st.text_input("المنتج / الخدمة *")
            expected_audience = st.text_input("عدد الجمهور المتوقع للبراند")
        with col2:
            ig_handle = st.text_input("Instagram Username / Link")
            fb_url = st.text_input("Facebook Page Link")
            tiktok_handle = st.text_input("TikTok Username / Link")
            linkedin_url = st.text_input("LinkedIn Link")
            yt_url = st.text_input("YouTube Channel Link")

        st.subheader("📊 أداء المنصات والحملات الإعلانية (Platform & Meta Ads Performance)")
        c1, c2, c3 = st.columns(3)
        with c1:
            followers_count = st.text_input("عدد المتابعين الحالي")
            followers_growth = st.text_input("نمو المتابعين خلال الفترة (زيادة/نقص)")
            reach_period = st.text_input("Reach خلال الفترة")
            engagements_period = st.text_input("Engagements خلال الفترة (لايك/كومنت/شير/سيف)")
        with c2:
            profile_visits = st.text_input("Profile visits خلال الفترة")
            website_whatsapp_clicks = st.text_input("Website clicks أو WhatsApp clicks")
            content_mix_input = st.text_input("تنوع المحتوى: (كام ريل - كام كاروسيل - كام بوست صورة - كام بوست تكست في الشهر)")
        with c3:
            ad_spend = st.number_input("اتصرف كام على Meta Ads خلال الفترة ($) - اختياري", min_value=0.0, value=0.0)
            ad_objective = st.text_input("Objective للحملات كان إيه؟ (Messages/Leads/Calls/Traffic)")
            ad_results = st.text_input("عدد النتائج (رسائل/ليدز/مكالمات) خلال الفترة")
            cost_per_result = st.text_input("Cost per result خلال الفترة")

        # Section 2: Audience Analysis Inputs
        st.subheader("2️⃣ أبحاث الجمهور وسلوك المستهلك (Audience Inputs)")
        col_a, col_b = st.columns(2)
        with col_a:
            demographics_input = st.text_area("نسبة ذكور/إناث، الفئة العمرية، أهم المدن، المستوى الاقتصادي (platform insights / DataReportal)")
            problems_input = st.text_area("المشاكل والاعتراضات (من AnswerThePublic / Groups / Comments)")
            buying_drivers_input = st.text_area("دوافع الشراء وعوامل الثقة (من Comments / Survey / Reviews)")
        with col_b:
            behavior_input = st.text_area("سلوك المستخدم على FB، نوع المحتوى المفضل على IG Explore، والتريندات على TikTok Creative Center")
            buying_habit_input = st.text_input("طريقة الشراء (أونلاين/أوفلاين) وسرعة اتخاذ القرار (سريع/بياخد وقت)")

        # Section 3: Competitor Inputs
        st.subheader("3️⃣ بيانات المنافس للتحليل والمقارنة (Competitor Inputs)")
        comp_name = st.text_input("اسم المنافس")
        comp_website = st.text_input("لينك الموقع/اللاندنج للمنافس")
        comp_ig = st.text_input("لينك Instagram للمنافس")
        comp_fb = st.text_input("لينك Facebook للمنافس")
        comp_tiktok = st.text_input("لينك TikTok للمنافس")
        comp_gmaps = st.text_input("Google Business Profile / Maps link للمنافس")
        comp_details = st.text_area("تفاصيل المنافس: الجمهور المستهدف، أقرب 3 خدمات، Positioning & Offer، USP، Proof، الباقات، هل الأسعار معلنة، الـ CTA، طريقة الوصول للـ Offer، شروط البيانات، النشر، تنوع المحتوى، نبرة الصوت، الكرياتيف، وتقييمات جوجل")

        submitted = st.form_submit_button("🚀 بدء الـ Audit الشامل وتوليد الاستراتيجية")

    if submitted and brand_name:
        st.info("🔄 جاري جلب البيانات المتاحة عبر Apify...")
        scraped_data = {}
        if ig_handle:
            try:
                run_input = {"directUrls": [f"https://www.instagram.com/{ig_handle}/"], "resultsType": "details"}
                run = apify.actor("apify/instagram-profile-scraper").call(run_input=run_input, timeout_secs=30)
                scraped_data['brand_ig'] = apify.dataset(run["defaultDatasetId"]).list_items().items
            except Exception as e:
                st.warning("⚠️ استغرق سحب البيانات وقتاً طويلاً، سيتم الاعتماد على المدخلات المباشرة لتوليد التقرير المكتمل.")
                scraped_data['ig_error'] = str(e)

        st.info("🧠 جاري توليد التقرير الاستراتيجي الشامل بنفس الهيكل المطلوب حرفياً...")

        strict_prompt = f"""
        أنت Senior Marketing Strategist & Growth Director. قم بإجراء Audit كامل واستخراج استراتيجية متكاملة للبراند '{brand_name}' بناءً على البيانات التالية، ملتزماً بالهيكل المطلوب حرفياً ودون اختصار أي بند:

        عنوان المشروع: Strategy Mentoring - {brand_name}

        1- Situation Analysis

         - platforms analysis
        لينك/يوزر الحساب: (FB: {fb_url}, IG: {ig_handle}, TikTok: {tiktok_handle}, LinkedIn: {linkedin_url}, YT: {yt_url})
        عدد المتابعين الحالي: {followers_count}
        نمو المتابعين خلال الفترة (زيادة/نقص): {followers_growth}
        Reach خلال الفترة: {reach_period}
        Engagements خلال الفترة (لايك/كومنت/شير/سيف): {engagements_period}
        Profile visits خلال الفترة Website clicks أو WhatsApp clicks: {profile_visits} / {website_whatsapp_clicks}
        تنوع المحتوى: (كام ريل في الشهر - كام كاروسيل في الشهر-كام بوست صورة- كام بوست تكست): {content_mix_input}
        أفضل ٥ Reels من حيث المشاهدات (استخرج/حلل بناءً على البيانات والنشاط)
        أفضل ٥ بوستات من حيث التفاعل (استخرج/حلل بناءً على البيانات والنشاط)
        الجمهور الأساسي (مدن/سن/نوع)
        عدد الجمهور المتوقع للبراند: {expected_audience}
        اتصرف كام على Meta Ads خلال الفترة؟ ({ad_spend} $)
        Objective للحملات كان إيه؟ (Messages/Leads/Calls/Traffic): {ad_objective}
        عدد النتائج (رسائل/ليدز/مكالمات) خلال الفترة: {ad_results}
        Cost per result خلال الفترة: {cost_per_result}

         - Audience Analysis
        كم ساعة يقضي المستخدم على السوشيال ميديا؟ من DataReportal (لدولة {geo_coverage})
        ترتيب المنصات في البلد؟ من DataReportal (لدولة {geo_coverage})
        نوع المحتوى المفضل؟ من DataReportal
        نسبة ذكور / إناث من platform insights / data reportal: {demographics_input}
        الفئة العمرية من platform insights / data reportal
        أهم المدن من platform insights / data reportal
        المستوى الإقتصادي من platform insights / data reportal
        المشاكل من AnswerThePublic / Groups: {problems_input}
        الاهتمامات من Meta Insights
        دوافع الشراء من Comments / Survey: {buying_drivers_input}
        المؤثرين
        سلوك المستخدم على Facebook من Groups / Comments: {behavior_input}
        نوع المحتوى المفضل على Instagram من Explore
        نوع الفيديوهات والتريند على TikTok من Creative Center
        طريقة الشراء أونلاين ولا أوفلاين من Observation: {buying_habit_input}
        سرعة القرار سريع ولا بياخد وقت من Experience
        الاعتراضات من Comments
        الثقة (إيه اللي يطمنه) من Reviews

        - competitor analysis
        اسم المنافس: {comp_name}
        لينك الموقع/اللاندنج: {comp_website}
        لينك Instagram: {comp_ig}
        لينك Facebook: {comp_fb}
        لينك TikTok: {comp_tiktok}
        Google Business Profile / Maps link: {comp_gmaps}
        الدولة/المدينة/التغطية الجغرافية؟
        مين الجمهور اللي باين إنه مستهدفه؟ (سن - نوع - مكان )
        أقرب 3 خدمات/منتجات بيبيعها شبهنا
        Positioning & Offer
        USP / السبب اللي بيقولك تختاره
        Proof بيستخدمه لإثبات كلامه؟
        العروض/الباقات (Bundles) اللي عنده؟
        الأسعار معلنة ولا لأ؟
        أقوى CTA عنده إيه؟
        طريقة الوصول للـ Offer: واتساب؟ فورم؟ مكالمة؟ حجز أونلاين؟
        هل بيطلب بيانات؟ (اسم/موبايل/إيميل) — فين؟
        هل فيه Nurture/متابعة؟ (Auto-reply/رسائل/Newsletter)
        ميزة واضحة في الفانل عنده؟
        كام ريل في الشهر - كام كاروسيل في الشهر-كام بوست صورة- كام بوست تكست
        تنوع المحتوى شهرياً: تعليمي-أوفر-بروف-ترند/لايف
        أفضل ٥ Reels من حيث المشاهدات (لينك + Views لكل واحد)
        أفضل ٥ بوستات من حيث التفاعل (لينك + Engagements لكل واحد)
        أكثر 3 Topics/Angles متكررين عنده
        Tone of Voice
        هل بيستخدم UGC/شهادات/قبل-بعد؟ أمثلة (لينكات)
        إيه الـ Content gaps؟ (حاجة هو مش مغطّيها)
        Meta Ad Library: أمثلة لآخر إعلاناته (لينكات/سكرينات)
        أقوى Angle اعلاني واضح؟
        هل بيستخدم Lead Form ولا Website ولا WhatsApp؟
        أنواع الكرياتيف: UGC/قبل-بعد/موشن/ستاتيك/كاروسيل ....
        أي Offers/Promos متكررة في الإعلانات؟
        Google rating + عدد الريفيوز (لو موجود)
        أكثر 3 نقاط مدح في الريفيوز (ملخص)
        أكثر 3 شكاوى/سلبيات (ملخص)
        هل بيرد على الريفيوز؟ (نعم/لا) + أسلوب الرد
        سرعة تجاوبه في الرسائل؟
        ساعات العمل/طرق التواصل الظاهرة؟
        تفاصيل ومدخلات إضافية للمنافس: {comp_details}
        — ملخص المقارنة (يطلع منه قرارات) —
        نقط تفوقنا عليه (1–3 نقاط)
        نقط تفوقه علينا (1–3 نقاط)
        فرصة Quick win

        - SWOT Analysis
        Strengths
        Weaknesses
        Opportunities
        Threats

        2- Customer journey
        درجة الوعي (Awareness Level)
        هل هو غير واعي بالمشكلة؟ من كومنتات البوستات / من جروبات الفيسبوك
        هل هو واعي بالمشكلة فقط؟ من كومنتات البوستات / من جروبات الفيسبوك
        هل هو واعي بالحل؟ من كومنتات البوستات / من جروبات الفيسبوك
        هل هو واعي بالبراند نفسه ؟ من خلال داتا 3 شهور سابقة
        رحلة العميل (Customer Journey)
        أول نقطة احتكاك تحليل المنصات ومحتوى المنافسين
        ماذا يفعل قبل الشراء؟ تسلسل الأسئلة والترددات
        ما الذي يمنعه من القرار؟ اعتراضات الجمهور
        ما الذي يدفعه للقرار النهائي؟ آخر خطوة قبل الشراء

        3- Objectives + key results (KPI)
        الهدف الرئيسي اللى فى البريف: {main_objective}
        المنتج/الخدمة: {product_service}
        السوق/المنطقة: {geo_coverage}
        الفترة الزمنية (30/60/90 يوم)
        الأهداف الاستراتيجية ( 3 أهداف SMART ) + KPI أساسي لكل هدف

        4- Customer (Segment & Buyer Persona)
        حدد 4 Segments
        مع Interest or need + location + Age and gender

        بيانات Scraping المتاحة من Apify: {json.dumps(scraped_data, ensure_ascii=False)}

        قم بصياغة التقرير بلغة عربية احترافية، مع الالتزام التام بملء كافة البنود والتحليلات المطلوبة أعلاه بدقة وبدون حذف أي عنصر.
        """

        try:
            ai_response = model.generate_content(strict_prompt)
            st.success("✅ تم استخراج الاستراتيجية والـ Audit المكتمل تماماً بنجاح!")
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
                st.warning(f"⚠️ التقرير معروض بالكامل أعلاه، مع وجود ملاحظة حفظ في قاعدة البيانات: {str(db_err)}")
        except Exception as ai_err:
            st.error(f"❌ حدث خطأ أثناء التوليد بواسطة الذكاء الاصطناعي: {str(ai_err)}")

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
