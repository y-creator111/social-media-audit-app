import streamlit as st
import google.generativeai as genai
from supabase import create_client
from apify_client import ApifyClient
import json

st.set_page_config(page_title="Strategy Mentoring - Auto IG Scraper & Audit", layout="wide")

# Initialize Services
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

st.title("📊 Strategy Mentoring - Automated Social Media Audit")

# Helper function to parse and extract top metrics automatically via Python
def parse_ig_apify_data(items):
    if not items:
        return {"error": "لم يتم العثور على منشورات أو الحساب خاص"}
    
    reels = []
    posts = []
    reels_count = 0
    carousel_count = 0
    image_count = 0
    
    for item in items:
        p_type = item.get('type', '')
        is_video = item.get('isVideo', False) or p_type in ['Video', 'Reel']
        
        # Count types
        if is_video:
            reels_count += 1
            views = item.get('playCount') or item.get('videoViewCount') or item.get('likesCount', 0)
            reels.append({
                'url': item.get('url', ''),
                'views': views,
                'caption': item.get('caption', '')[:100]
            })
        elif p_type in ['Sidecar', 'Carousel']:
            carousel_count += 1
        else:
            image_count += 1
            
        engagements = (item.get('likesCount', 0) or 0) + (item.get('commentsCount', 0) or 0)
        posts.append({
            'url': item.get('url', ''),
            'engagements': engagements,
            'likes': item.get('likesCount', 0),
            'comments': item.get('commentsCount', 0),
            'caption': item.get('caption', '')[:100]
        })
        
    # Sort automatically in Python
    top_5_reels = sorted(reels, key=lambda x: x['views'], reverse=True)[:5]
    top_5_posts = sorted(posts, key=lambda x: x['engagements'], reverse=True)[:5]
    
    return {
        "followers": items[0].get('followersCount', 'غير محدد') if items else 'N/A',
        "content_mix": f"Reels: {reels_count} | Carousels: {carousel_count} | Images: {image_count}",
        "top_5_reels": top_5_reels,
        "top_5_posts": top_5_posts
    }

# Navigation Sidebar
st.sidebar.header("📁 إدارة المشاريع")
project_mode = st.sidebar.radio("اختر النمط:", ["مشروع جديد", "استعراض المشاريع السابقة"])

if project_mode == "مشروع جديد":
    st.header("🎯 الإدخالات (Apify والـ AI يتكفلان بالباقي أوتوماتيكياً)")
    
    with st.form("auto_audit_form"):
        col1, col2 = st.columns(2)
        with col1:
            brand_name = st.text_input("اسم البراند الرئيسي *")
            ig_handle = st.text_input("Instagram Username للبراند (بدون @) *", placeholder="مثال: nike")
            geo_coverage = st.text_input("الدولة / السوق المستهدف *", placeholder="مصر / السعودية")
            main_objective = st.text_input("الهدف الرئيسي (30/60/90 يوم) *")
            product_service = st.text_input("المنتج / الخدمة *")
        
        with col2:
            comp_name = st.text_input("اسم المنافس الرئيسي *")
            comp_ig = st.text_input("Instagram Username للمنافس (بدون @) *", placeholder="مثال: adidas")
            ad_spend = st.number_input("صرف الإعلانات المباشر على Meta ($) - اختياري", min_value=0.0, value=0.0)
            private_notes = st.text_area("أي بيانات خاصة أو ملاحظات إضافية (اختياري)")

        submitted = st.form_submit_button("🚀 بدء السحب الأوتوماتيكي والـ Audit الكامل")

    if submitted and brand_name and ig_handle:
        st.info("🔄 جاري سحب بيانات البراند والمنافس أوتوماتيكياً عبر Apify...")
        
        brand_parsed = {}
        comp_parsed = {}
        
        # Scrape Brand
        try:
            run_input_brand = {"directUrls": [f"https://www.instagram.com/{ig_handle}/"], "resultsType": "posts"}
            run_b = apify.actor("apify/instagram-post-scraper").call(run_input=run_input_brand, timeout_secs=35)
            brand_items = apify.dataset(run_b["defaultDatasetId"]).list_items().items
            brand_parsed = parse_ig_apify_data(brand_items)
        except Exception as e:
            st.warning(f"⚠️ تعذر سحب كامل منشورات البراند أوتوماتيكياً: {str(e)}")

        # Scrape Competitor
        if comp_ig:
            try:
                run_input_comp = {"directUrls": [f"https://www.instagram.com/{comp_ig}/"], "resultsType": "posts"}
                run_c = apify.actor("apify/instagram-post-scraper").call(run_input=run_input_comp, timeout_secs=35)
                comp_items = apify.dataset(run_c["defaultDatasetId"]).list_items().items
                comp_parsed = parse_ig_apify_data(comp_items)
            except Exception as e:
                st.warning(f"⚠️ تعذر سحب بيانات المنافس أوتوماتيكياً: {str(e)}")

        st.info("🧠 جاري تحليل الداتا المسحوبة وإعداد التقرير الاستراتيجي الشامل...")

        prompt = f"""
        أنت Senior Growth Director & Brand Strategist.
        قم بإجراء Audit كامل واستخراج استراتيجية متكاملة للبراند '{brand_name}' بناءً على البيانات التي تم سحبها أوتوماتيكياً بواسطة Apify والمعطيات التالية:

        معلومات الإدخال:
        - البراند: {brand_name} (IG: instagram.com/{ig_handle})
        - المنافس: {comp_name} (IG: instagram.com/{comp_ig})
        - الدولة/السوق: {geo_coverage}
        - الهدف: {main_objective}
        - المنتج/الخدمة: {product_service}
        - صرف الإعلانات المباشر: {ad_spend} $
        - ملاحظات إضافية: {private_notes}

        البيانات المستخرجة أوتوماتيكياً بواسطة Python و Apify للبراند:
        {json.dumps(brand_parsed, ensure_ascii=False, indent=2)}

        البيانات المستخرجة أوتوماتيكياً بواسطة Python و Apify للمنافس ({comp_name}):
        {json.dumps(comp_parsed, ensure_ascii=False, indent=2)}

        المطلوب: توليد التقرير كاملاً باللغة العربية مع الالتزام بالهيكل التالي حرفياً وبكل تفاصيله وبدون حذف أو اختصار أي بند:

        # Strategy Mentoring - {brand_name}

        ## 1- Situation Analysis

        ### platforms analysis
        - يوزر الحساب: instagram.com/{ig_handle}
        - عدد المتابعين الحالي (من الداتا المسحوبة)
        - نمو المتابعين تقديراً خلال الفترة
        - Reach والـ Engagements المباشرة من التفاعلات
        - Profile visits و Website/WhatsApp clicks تقديراً
        - تنوع المحتوى شهرياً (العدد الفعلي المسحوب للريلز والكاروسيل والصور)
        - أفضل ٥ Reels من حيث المشاهدات (عرض اللينكات وأعداد المشاهدات المسحوبة أوتوماتيكياً)
        - أفضل ٥ بوستات من حيث التفاعل (عرض اللينكات والتفاعلات المسحوبة أوتوماتيكياً)
        - إحصائيات متقدمة بالفيديو (Watch Time, Average Play Time, 3-sec Views)
        - الجمهور الأساسي وحجم الجمهور المتوقع للبراند في {geo_coverage}
        - تحليل Meta Ads (الميزانية {ad_spend}$، الهدف الموصى به، النتائج المتوقعة، و Cost per result)

        ### Audience Analysis
        - كم ساعة يقضي المستخدم على السوشيال ميديا في {geo_coverage} (من DataReportal)
        - ترتيب المنصات ونوع المحتوى المفضل في {geo_coverage} (من DataReportal)
        - نسبة ذكور / إناث، الفئات العمرية، أهم المدن، والمستوى الاقتصادي
        - المشاكل والاعتراضات الشائعة في هذا المجال
        - الاهتمامات ودوافع الشراء وسلوك المستخدم على FB و IG Explore و TikTok Creative Center
        - طريقة الشراء وسرعة القرار وعوامل بناء الثقة

        ### competitor analysis (المنافس: {comp_name})
        - يوزر المنافس: instagram.com/{comp_ig}
        - التغطية والجمهور المستهدف وأقرب 3 خدمات شبهنا
        - Positioning & Offer, USP, Proofs, الباقات، والأسعار هل معلنة أم لا
        - أقوى CTA وطريقة الوصول للـ Offer والفانل والـ Nurture
        - تنوع المحتوى شهرياً ونبرة الصوت Tone of Voice
        - أفضل 5 Reels من حيث المشاهدات وأفضل 5 بوستات للمنافس (من الداتا المسحوبة أوتوماتيكياً)
        - أكثر 3 Topics متكررة و Content Gaps
        - Meta Ad Library Analysis (الأنجلات الإعلانية والكرياتيف)
        - تقييمات جوجل والريفيوز وأسلوب الرد
        - ملخص المقارنة: (3 نقاط تفوقنا - 3 نقاط تفوقه - فرصة Quick win)

        ### SWOT Analysis
        - Strengths, Weaknesses, Opportunities, Threats

        ---

        ## 2- Customer journey
        - درجة الوعي (Awareness Levels: Unaware, Problem Aware, Solution Aware, Brand Aware)
        - رحلة العميل (أول نقطة احتكاك -> ما قبل الشراء -> الاعتراضات -> القرار النهائي)

        ---

        ## 3- Objectives + key results (KPI)
        - الهدف الرئيسي والمنتج والسوق والمدة (30/60/90 يوم)
        - 3 أهداف استراتيجية SMART + الـ KPI الأساسي لكل هدف

        ---

        ## 4- Customer (Segment & Buyer Persona)
        - تحديد 4 Segments تفصيلية تشمل: (Interest/Need + Location + Age & Gender + Pain Point + Decision Trigger)
        """

        try:
            ai_response = model.generate_content(prompt)
            st.success("✅ تم جلب البيانات أوتوماتيكياً وتوليد التقرير بنجاح!")
            st.markdown(ai_response.text)
            
            try:
                db_payload = {
                    "brand_name": brand_name,
                    "inputs": {"geo": geo_coverage, "objective": main_objective, "ad_spend": ad_spend},
                    "scraped_data": json.loads(json.dumps(brand_parsed, default=str)),
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
