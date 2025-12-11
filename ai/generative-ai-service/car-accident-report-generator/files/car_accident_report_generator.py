import io
import json
import base64
import os

import streamlit as st
from PIL import Image
from pdf2image import convert_from_bytes
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import arabic_reshaper
from bidi.algorithm import get_display


from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI
from langchain_core.messages import HumanMessage, SystemMessage

from config import COMPARTMENT_ID  # you provide this

from matplotlib.patches import Rectangle
import matplotlib.pyplot as plt



# For the font
ARABIC_FONT_PATH = "fonts/NotoNaskhArabic-Regular.ttf" 
# Register a font name for Arabic text
pdfmetrics.registerFont(TTFont("ArabicMain", ARABIC_FONT_PATH))

# For the background of the damage map thing
CAR_TOP_VIEW_PATH = os.path.join("assets", "car_top_view.png")

# ---------- Helpers ----------
def ar(text):
    """Shape + bidi Arabic text for correct RTL display in ReportLab."""
    if not text:
        return ""
    # Ensure we work with str
    text = str(text)
    reshaped = arabic_reshaper.reshape(text)
    # Bidi to get correct visual ordering
    return get_display(reshaped)

def file_to_jpeg_bytes_list(uploaded_file):
    """
    Takes a Streamlit UploadedFile and returns a list of BytesIO objects
    with JPEG-encoded images (one per page for PDFs).
    """
    if uploaded_file is None:
        return []

    image_bytes_list = []

    if uploaded_file.type == "application/pdf":
        pages = convert_from_bytes(uploaded_file.read(), fmt="jpeg")
        for page in pages:
            buf = io.BytesIO()
            page.save(buf, format="JPEG")
            buf.seek(0)
            image_bytes_list.append(buf)
    else:
        img = Image.open(uploaded_file).convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        buf.seek(0)
        image_bytes_list.append(buf)

    return image_bytes_list

def limit_images(image_bytes_list, max_images=8):
    """
    Ensure we don't send too many images per Maverick call.
    """
    if len(image_bytes_list) > max_images:
        return image_bytes_list[:max_images]
    return image_bytes_list

def parse_llm_json(raw):
    """
    Make LLM output safe for json.loads:
    - handle None / empty
    - strip code fences ```...```
    - extract substring between first '{' and last '}'
    """
    if raw is None:
        raise ValueError("LLM response is None")

    # Some LangChain objects may not be plain strings
    if not isinstance(raw, str):
        raw = str(raw)

    raw = raw.strip()

    if not raw:
        raise ValueError("LLM response is empty")

    # Strip markdown fences like ```json ... ```
    if raw.startswith("```"):
        parts = raw.split("```")
        # try to find the part that actually contains JSON
        for p in parts:
            p = p.strip()
            if p.startswith("{") and "}" in p:
                raw = p
                break

    # If it still doesn't start with '{', extract the JSON substring
    if not raw.lstrip().startswith("{"):
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1 and start < end:
            raw = raw[start:end + 1]

    return json.loads(raw)

def inject_arabic_css():
    with open(ARABIC_FONT_PATH, "rb") as f:
        font_data = f.read()
    encoded = base64.b64encode(font_data).decode("utf-8")

    st.markdown(
        f"""
        <style>
        @font-face {{
            font-family: 'ArabicMainWeb';
            src: url(data:font/ttf;base64,{encoded}) format('truetype');
        }}
        .arabic-text {{
            font-family: 'ArabicMainWeb', 'Noto Naskh Arabic', 'Amiri', sans-serif;
            direction: rtl;
            text-align: right;
            font-size: 0.9rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
# ---------- Maverick extractor ----------

def maverick_extract_party(party_label, all_images_bytes):
    """
    Call Llama 4 Maverick for each party.
    Returns JSON of shape:
    {
      "party_1": { driver, vehicle, insurance },
      "damage": {
        "party_1": { damage_summary, primary_areas, driveable }
      }
    }
    or the same with party_2.
    """
    llm = ChatOCIGenAI(
        model_id="meta.llama-4-maverick-17b-128e-instruct-fp8",
        compartment_id=COMPARTMENT_ID,
        model_kwargs={"max_tokens": 2500, "temperature": 0}
    )

    # we use Arabic but also tell model which logical party this is
    party_num = "الأول" if party_label == "party_1" else "الثاني"

    # system_msg = SystemMessage(
    #     content=f"""
    #     أنت مساعد ذكاء اصطناعي متخصص في تقارير حوادث السيارات لشركة نجم.

    #     جميع الصور في هذا الطلب تخص طرفاً واحداً فقط في الحادث، وهو:
    #     - الطرف {party_num} (يجب أن تسجله في الحقل "{party_label}").

    #     الصور تتضمن (قد يكون بعضها مفقوداً):
    #     - رخصة القيادة لهذا الطرف
    #     - رخصة السير / استمارة المركبة لهذا الطرف
    #     - وثيقة أو أكثر من وثائق التأمين لهذا الطرف
    #     - صور أضرار سيارة هذا الطرف

    #     مهمتك:
    #     1. استخراج المعلومات الأساسية لهذا الطرف فقط (سائق، مركبة، تأمين).
    #     2. تحليل صور الأضرار وتحديد الجهات المتضررة من السيارة (أمام، خلف، يمين، يسار، أمام يمين، أمام يسار، خلف يمين، خلف يسار).
    #     3. تلخيص حالة الأضرار لهذه السيارة.

    #     إرشادات مهمة:
    #     - أعد جميع القيم النصية باللغة العربية فقط.
    #     - إذا كانت المعلومة غير موجودة أو غير واضحة، أعد القيمة null.
    #     - لا تضف أي نص خارج عن صيغة JSON.
    #     - التزم تماماً بالهيكل التالي، مع استبدال PARTY_LABEL باسم الطرف ({party_label}):
    #     ملاحظة مهمة جداً:
    #     اسم السائق الموجود في رخصة القيادة قد يكون مختلفاً تماماً عن اسم مالك المركبة الموجود في استمارة السيارة. 
    #     لا تفترض أبداً أن السائق هو مالك المركبة. 
    #     يجب استخراج:
    #     - اسم السائق فقط من رخصة القيادة.
    #     - اسم مالك المركبة فقط من استمارة السيارة أو وثائق التأمين.

    #     إذا كان هناك اختلاف بين الاسمين فهذا طبيعي ويجب الاحتفاظ به كما هو.

    #     شرط إضافي مهم جداً:
    #     - يجب أن يأتي اسم السائق فقط من رخصة القيادة، وليس من أي مستند آخر.
    #     - يجب أن يأتي اسم مالك المركبة فقط من رخصة السير (الاستمارة) أو وثيقة التأمين، وليس من رخصة القيادة.

    #     لا يجوز للذكاء الاصطناعي أن يستنتج أو يفترض أسماء السائق أو المالك من أي مصدر آخر غير المستند الصحيح.
    #     إذا لم يظهر الاسم في المستند الصحيح، يجب إعادة القيمة null.

    #     تذكر: "مهيم مياه" هو اسم يظهر في المستندات.
    #     تذكر: رقم الهيكل ليس هو نفسه رقم اللوحة

    #     قاعدة إلزامية لتمثيل اللغة:
    #     - يجب أن تكون جميع القيم النصية بالأحرف العربية فقط، ولا يسمح باستخدام أي حروف لاتينية (A–Z).
    #     - الاستثناء الوحيد هو الحقول التي تحتوي على أرقام أو أكواد مثل:
    #     id_number, plate_no, policy_no, رقم الوثيقة، أرقام هويات، أرقام لوحات، أرقام وثائق التأمين.
    #     - إذا كان النص في المستند مكتوباً بالإنجليزية فقط (مثل اسم دولة أو اسم شخص)، قم بترجمته أو كتابته بحروف عربية (تعريب/نقل صوتي).
    #     - لا تكتب أبداً أسماء أو جنسيات أو أنواع رخصة أو شركات تأمين بحروف لاتينية.

    #     أمثلة:
    #     - "BANGLADESH" → "بنجلاديش"
    #     - "Toyota" → "تويوتا"
    #     - "Abdullah" → "عبد الله"

    #     {{
    #     "{party_label}": {{
    #         "driver": {{
    #         "name": "<string or null>",
    #         "nationality": "<string or null>",
    #         "age": "<string or null>",
    #         "mobile": "<string or null>",
    #         "id_number": "<string or null>",
    #         "license_type": "<string or null>",
    #         "license_expiry": "<string or null>",
    #         "license_issue_date": "<string or null>"
    #         }},
    #         "vehicle": {{
    #         "owner_name": "<string or null>",
    #         "make_model": "<string or null>",
    #         "year_color": "<string or null>",
    #         "plate_no": "<string or null>"
    #         }},
    #         "insurance": {{
    #         "company_name": "<string or null>",
    #         "policy_no": "<string or null>",
    #         "expiry_date": "<string or null>",
    #         "start_date": "<string or null>",
    #         "insurance_type": "<string or null>"
    #         }}
    #     }},
    #     "damage": {{
    #         "{party_label}": {{
    #         "damage_summary": "<ملخص الأضرار بالعربية أو null>",
    #         "primary_areas": [
    #             "<واحد أو أكثر من: front, rear, left, right, front-left, front-right, rear-left, rear-right>"
    #         ],
    #         "driveable": true
    #         }}
    #     }}
    #     }}

    #     أعد استجابة بصيغة JSON فقط، بدون ``` أو أي نص إضافي.
    #     """
    # )
    
    system_msg = SystemMessage(
    content=f"""
        You are an AI assistant specialized in generating car-accident reports for Najm.

        All images in this request belong to **one party only**, which is:
        - Party {party_num} (you must record it under the field "{party_label}").

        The images may include (some may be missing):
        - Driver’s license for this party
        - Vehicle registration (Istimara) for this party
        - One or more insurance documents for this party
        - Photos of this party’s vehicle damages

        Your tasks:
        1. Extract only the essential information for this party (driver, vehicle, insurance).
        2. Analyze the damage photos and identify the damaged areas of the vehicle (front, rear, left, right, front-left, front-right, rear-left, rear-right).
        3. Produce a summary of the vehicle damage.

        Important rules:
        - **All returned text values must be in Arabic only.**
        - If any information is missing or unclear, return **null**.
        - Do NOT add any text outside the JSON format.
        - Follow the exact JSON structure below, using PARTY_LABEL as ({party_label}).

        Critical note:
        The driver’s name in the driver’s license may be completely different from the vehicle owner’s name in the registration or insurance documents.  
        Never assume the driver is the owner.

        You must extract:
        - Driver’s name **only** from the driver’s license.
        - Owner’s name **only** from the vehicle registration (Istimara) or insurance document.

        If the correct document does not contain the name, return **null**.  
        The model must never infer or guess the driver or owner name from another source.

        Remember:
        - "مهيم مياه" is an actual name that may appear in documents.
        - The chassis number is **not** the same as the plate number.

        Mandatory language rule:
        - All text values must be in **Arabic letters only**, never English (A–Z).
        - Exception: fields containing numbers or codes (e.g., id_number, plate_no, policy_no, document numbers).
        - If a value appears **only in English** in the document (e.g., person name, country name, brand), **transliterate or translate it into Arabic**.
        - Never output English letters in names, nationalities, license types, or insurance company names.

        Examples:
        - "BANGLADESH" → "بنجلاديش"
        - "Toyota" → "تويوتا"
        - "Abdullah" → "عبد الله"

        Expected JSON structure:
        {{
            "{party_label}": {{
                "driver": {{
                    "name": "<string or null>",
                    "nationality": "<string or null>",
                    "age": "<string or null>",
                    "mobile": "<string or null>",
                    "id_number": "<string or null>",
                    "license_type": "<string or null>",
                    "license_expiry": "<string or null>",
                    "license_issue_date": "<string or null>"
                }},
                "vehicle": {{
                    "owner_name": "<string or null>",
                    "make_model": "<string or null>",
                    "year_color": "<string or null>",
                    "plate_no": "<string or null>"
                }},
                "insurance": {{
                    "company_name": "<string or null>",
                    "policy_no": "<string or null>",
                    "expiry_date": "<string or null>",
                    "start_date": "<string or null>",
                    "insurance_type": "<string or null>"
                }}
            }},
            "damage": {{
                "{party_label}": {{
                    "damage_summary": "<Arabic damage summary or null>",
                    "primary_areas": [
                        "<one or more of: front, rear, left, right, front-left, front-right, rear-left, rear-right>"
                    ],
                    "driveable": true
                }}
            }}
        }}

        Return the response **as JSON only**, with no ``` or any additional text.
        """
        )

    content = [
        {
            "type": "text",
            "text": f"صور مستندات وأضرار حادث مروري للطرف {party_num} فقط."
        }
    ]
    for img_bytes in all_images_bytes:
        encoded = base64.b64encode(img_bytes.getvalue()).decode("utf-8")
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{encoded}"}
            }
        )

    human_msg = HumanMessage(content=content)

    with st.spinner(f"استخراج بيانات {party_num} باستخدام Maverick..."):
        resp = llm.invoke([system_msg, human_msg])

    try:
        try:
            raw = resp.content
            parsed = parse_llm_json(raw)
            return parsed
        except Exception as e:
            st.error(f"Failed to parse LLM response for {party_label}: {e}")
            # Debug output so you can see exactly what the model returned
            st.subheader(f"Raw LLM response for {party_label}")
            st.code(str(resp.content), language="json")
            raise
    except Exception as e:
        st.error(f"Failed to parse LLM response for {party_label}: {e}")
        st.text(resp.content)
        raise


# ---------- PDF generation ----------

def build_pdf(extracted_json) -> bytes:
    """
    Build a report PDF.
    Headers are English; values are Arabic taken from extracted_json.
    """
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    def draw_label_value(x_mm, y_mm, label_en, value_ar, right_column=False):
        if right_column:
            x_start = x_mm * mm
            x_value = (x_mm + 70) * mm
        else:
            x_start = x_mm * mm
            x_value = (x_mm + 80) * mm

        # English header (left-aligned, Latin font)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(x_start, y_mm * mm, label_en)

        # Arabic value (right-aligned, Arabic font)
        if value_ar:
            shaped = ar(value_ar)
            c.setFont("ArabicMain", 11)
            c.drawRightString(x_value, (y_mm - 1.5) * mm, shaped)


    p1 = extracted_json.get("party_1", {}) or {}
    p2 = extracted_json.get("party_2", {}) or {}

    d1 = p1.get("driver", {}) or {}
    v1 = p1.get("vehicle", {}) or {}
    ins1 = p1.get("insurance", {}) or {}

    d2 = p2.get("driver", {}) or {}
    v2 = p2.get("vehicle", {}) or {}
    ins2 = p2.get("insurance", {}) or {}

    # Title
    y = 285
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2, y * mm, "Liability Determination Report")
    y -= 8
    c.setFont("Helvetica", 10)
    c.drawCentredString(width / 2, y * mm, "Final Report")

    # Party 1 driver info (left)
    y -= 12
    c.setFont("Helvetica-Bold", 11)
    c.drawString(20 * mm, y * mm, "Party (1) Driver Info")
    y -= 6
    draw_label_value(20, y, "Name", d1.get("name"))
    y -= 6
    draw_label_value(20, y, "Nationality", d1.get("nationality"))
    y -= 6
    draw_label_value(20, y, "Age", d1.get("age"))
    y -= 6
    draw_label_value(20, y, "Mobile No.", d1.get("mobile"))
    y -= 6
    draw_label_value(20, y, "ID Number", d1.get("id_number"))
    y -= 6
    draw_label_value(20, y, "License Type", d1.get("license_type"))
    y -= 6
    draw_label_value(20, y, "Expiry Date", d1.get("license_expiry"))
    y -= 10

    # Party 2 driver info (right)
    y_driver2 = 265
    c.setFont("Helvetica-Bold", 11)
    c.drawString(120 * mm, y_driver2 * mm, "Party (2) Driver Info")
    y_driver2 -= 6
    draw_label_value(120, y_driver2, "Name", d2.get("name"), right_column=True)
    y_driver2 -= 6
    draw_label_value(120, y_driver2, "Nationality", d2.get("nationality"), right_column=True)
    y_driver2 -= 6
    draw_label_value(120, y_driver2, "Age", d2.get("age"), right_column=True)
    y_driver2 -= 6
    draw_label_value(120, y_driver2, "Mobile No.", d2.get("mobile"), right_column=True)
    y_driver2 -= 6
    draw_label_value(120, y_driver2, "ID Number", d2.get("id_number"), right_column=True)
    y_driver2 -= 6
    draw_label_value(120, y_driver2, "License Type", d2.get("license_type"), right_column=True)
    y_driver2 -= 6
    draw_label_value(120, y_driver2, "Expiry Date", d2.get("license_expiry"), right_column=True)

    # Party 1 vehicle
    y -= 8
    c.setFont("Helvetica-Bold", 11)
    c.drawString(20 * mm, y * mm, "Party (1) Vehicle Info")
    y -= 6
    draw_label_value(20, y, "Owner Name", v1.get("owner_name"))
    y -= 6
    draw_label_value(20, y, "Make/Model", v1.get("make_model"))
    y -= 6
    draw_label_value(20, y, "Year & Color", v1.get("year_color"))
    y -= 6
    draw_label_value(20, y, "Plate No", v1.get("plate_no"))
    y -= 10

    # Party 2 vehicle
    y_vehicle2 = 210
    c.setFont("Helvetica-Bold", 11)
    c.drawString(120 * mm, y_vehicle2 * mm, "Party (2) Vehicle Info")
    y_vehicle2 -= 6
    draw_label_value(120, y_vehicle2, "Owner Name", v2.get("owner_name"), right_column=True)
    y_vehicle2 -= 6
    draw_label_value(120, y_vehicle2, "Make/Model", v2.get("make_model"), right_column=True)
    y_vehicle2 -= 6
    draw_label_value(120, y_vehicle2, "Year & Color", v2.get("year_color"), right_column=True)
    y_vehicle2 -= 6
    draw_label_value(120, y_vehicle2, "Plate No", v2.get("plate_no"), right_column=True)

    # Party 1 insurance
    y -= 8
    c.setFont("Helvetica-Bold", 11)
    c.drawString(20 * mm, y * mm, "Party (1) Insurance Info")
    y -= 6
    draw_label_value(20, y, "Company Name", ins1.get("company_name"))
    y -= 6
    draw_label_value(20, y, "Policy No", ins1.get("policy_no"))
    y -= 6
    draw_label_value(20, y, "Start Date", ins1.get("start_date"))
    y -= 6
    draw_label_value(20, y, "Expiry Date", ins1.get("expiry_date"))
    y -= 6
    draw_label_value(20, y, "Insurance Type", ins1.get("insurance_type"))
    y -= 10

    # Party 2 insurance
    y_ins2 = 160
    c.setFont("Helvetica-Bold", 11)
    c.drawString(120 * mm, y_ins2 * mm, "Party (2) Insurance Info")
    y_ins2 -= 6
    draw_label_value(120, y_ins2, "Company Name", ins2.get("company_name"), right_column=True)
    y_ins2 -= 6
    draw_label_value(120, y_ins2, "Policy No", ins2.get("policy_no"), right_column=True)
    y_ins2 -= 6
    draw_label_value(120, y_ins2, "Start Date", ins2.get("start_date"), right_column=True)
    y_ins2 -= 6
    draw_label_value(120, y_ins2, "Expiry Date", ins2.get("expiry_date"), right_column=True)
    y_ins2 -= 6
    draw_label_value(120, y_ins2, "Insurance Type", ins2.get("insurance_type"), right_column=True)

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.getvalue()


def preview_pdf_first_page(pdf_bytes):
    """
    Convert first page of PDF to image and show in Streamlit.
    """
    images = convert_from_bytes(pdf_bytes, first_page=1, last_page=1)
    if images:
        st.image(images[0], caption="Report preview", use_container_width=True)


# ---------- Damage map visualisation ----------

def draw_car_damage_map(areas, title, bg_path=CAR_TOP_VIEW_PATH):
    img = Image.open(bg_path)

    # Create figure/axes and show image as background
    fig, ax = plt.subplots(figsize=(4, 2))
    ax.imshow(img, extent=(0, 1, 0, 1), origin="upper")  # coords in [0,1]x[0,1]
    ax.set_axis_off()
    fig.suptitle(title, fontsize=10)

    def highlight(x, y, w, h):
        """
        x, y, w, h are in normalized coordinates (0–1).
        origin="upper" means (0,0) is top-left, y increases downward.
        """
        ax.add_patch(Rectangle((x, y), w, h, alpha=0.3))

    # You can tweak these boxes to match your specific car image proportions
    for area in areas or []:
        if area == "front":
            highlight(0.15, 0.05, 0.7, 0.25)
        elif area == "rear":
            highlight(0.15, 0.70, 0.7, 0.25)
        elif area == "left":
            highlight(0.05, 0.20, 0.20, 0.60)
        elif area == "right":
            highlight(0.75, 0.20, 0.20, 0.60)
        elif area == "front-left":
            highlight(0.05, 0.05, 0.30, 0.30)
        elif area == "front-right":
            highlight(0.65, 0.05, 0.30, 0.30)
        elif area == "rear-left":
            highlight(0.05, 0.65, 0.30, 0.30)
        elif area == "rear-right":
            highlight(0.65, 0.65, 0.30, 0.30)

    st.pyplot(fig)


def show_damage_maps(damage_json):
    st.subheader("Damage overview per car")

    cols = st.columns(2)

    with cols[0]:
        p1 = damage_json.get("party_1", {}) or {}
        draw_car_damage_map(p1.get("primary_areas", []), "Party 1 Damage")
        st.markdown(
            '<div class="arabic-text">ملخص الأضرار للطرف الأول:</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="arabic-text">{p1.get("damage_summary") or "غير متوفر"}</div>',
            unsafe_allow_html=True,
        )

    with cols[1]:
        p2 = damage_json.get("party_2", {}) or {}
        draw_car_damage_map(p2.get("primary_areas", []), "Party 2 Damage")
        st.markdown(
            '<div class="arabic-text">ملخص الأضرار للطرف الثاني:</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="arabic-text">{p2.get("damage_summary") or "غير متوفر"}</div>',
            unsafe_allow_html=True,
        )

# ---------- Main Streamlit app ----------

def insurance():
    st.set_page_config(layout="wide")
    inject_arabic_css()
    st.title("Liability Determination Report")

    with st.sidebar:
        st.header("Party 1 – Documents")
        p1_license = st.file_uploader(
            "Party 1 Driving License",
            type=["pdf", "jpg", "jpeg", "png"],
            key="p1_license",
        )
        p1_reg = st.file_uploader(
            "Party 1 Vehicle Registration",
            type=["pdf", "jpg", "jpeg", "png"],
            key="p1_reg",
        )
        p1_ins = st.file_uploader(
            "Party 1 Insurance",
            type=["pdf", "jpg", "jpeg", "png"],
            key="p1_ins",
        )
        p1_damage = st.file_uploader(
            "Party 1 Damage Photos (one or more)",
            type=["pdf", "jpg", "jpeg", "png"],
            accept_multiple_files=True,
            key="p1_damage",
        )

        st.header("Party 2 – Documents")
        p2_license = st.file_uploader(
            "Party 2 Driving License",
            type=["pdf", "jpg", "jpeg", "png"],
            key="p2_license",
        )
        p2_reg = st.file_uploader(
            "Party 2 Vehicle Registration",
            type=["pdf", "jpg", "jpeg", "png"],
            key="p2_reg",
        )
        p2_ins = st.file_uploader(
            "Party 2 Insurance",
            type=["pdf", "jpg", "jpeg", "png"],
            key="p2_ins",
        )
        p2_damage = st.file_uploader(
            "Party 2 Damage Photos (one or more)",
            type=["pdf", "jpg", "jpeg", "png"],
            accept_multiple_files=True,
            key="p2_damage",
        )

    st.markdown("---")

    if st.button("Generate report"):
        mandatory = [p1_license, p1_reg, p1_ins, p2_license, p2_reg, p2_ins]
        if not all(mandatory):
            st.error("Please upload license, registration, and insurance for both parties.")
            return

        # ----- Party 1 images -----
        p1_images = []
        for f in [p1_license, p1_reg, p1_ins]:
            p1_images.extend(file_to_jpeg_bytes_list(f))
        for f in (p1_damage or []):
            p1_images.extend(file_to_jpeg_bytes_list(f))
        p1_images = limit_images(p1_images, max_images=8)

        # ----- Party 2 images -----
        p2_images = []
        for f in [p2_license, p2_reg, p2_ins]:
            p2_images.extend(file_to_jpeg_bytes_list(f))
        for f in (p2_damage or []):
            p2_images.extend(file_to_jpeg_bytes_list(f))
        p2_images = limit_images(p2_images, max_images=8)

        if not p1_images or not p2_images:
            st.error("No images found after conversion.")
            return

        # Maverick calls per party
        p1_json = maverick_extract_party("party_1", p1_images)
        p2_json = maverick_extract_party("party_2", p2_images)

        # Merge into combined structure used by PDF & damage maps
        combined = {
            "party_1": p1_json.get("party_1", {}),
            "party_2": p2_json.get("party_2", {}),
            "damage": {
                "party_1": (p1_json.get("damage") or {}).get("party_1", {}),
                "party_2": (p2_json.get("damage") or {}).get("party_2", {}),
            },
        }

        st.subheader("Extracted JSON (debug)")
        st.json(combined)

        pdf_bytes = build_pdf(combined)

        st.subheader("Generated Report")
        st.download_button(
            label="Download PDF report",
            data=pdf_bytes,
            file_name="report.pdf",
            mime="application/pdf",
        )

        preview_pdf_first_page(pdf_bytes)

        show_damage_maps(combined.get("damage", {}) or {})


if __name__ == "__main__":
    insurance()
