import streamlit as st
from google import genai
from google.genai import types
import pydantic
import os

st.set_page_config(page_title="AI Health Assistant", layout="wide")
st.title("🥗 AI Health & Nutrition Assistant (Thai Food Edition)")

# ช่องใส่ API Key บนหน้าเว็บ
api_key = st.text_input("ใส่ Google Gemini API Key ของคุณที่นี่ (หาได้จาก Google AI Studio):", type="password")

st.sidebar.header("1. ข้อมูลส่วนตัวและโรคประจำตัว")
with st.sidebar:
    age = st.number_input("อายุ (ปี)", min_value=10, max_value=100, value=30)
    gender = st.selectbox("เพศ", ["ชาย", "หญิง"])
    weight = st.number_input("น้ำหนัก (กก.)", min_value=30.0, max_value=200.0, value=65.0)
    height = st.number_input("ส่วนสูง (ซม.)", min_value=100.0, max_value=220.0, value=170.0)
    activity_level = st.selectbox("ระดับกิจวัตรประจำวัน", [
        "นั่งทำงานอยู่กับที่ (1.2)",
        "ออกกำลังกายเล็กน้อย 1-3 วัน/สัปดาห์ (1.375)",
        "ออกกำลังกายปานกลาง 3-5 วัน/สัปดาห์ (1.55)",
    ])
    st.subheader("โรคประจำตัว / ข้อจำกัด")
    has_diabetes = st.checkbox("เบาหวาน")
    has_hypertension = st.checkbox("ความดันโลหิตสูง")
    has_fatty_liver = st.checkbox("ไขมันพอกตับ")
    has_knee_pain = st.checkbox("ข้อเข่าเสื่อม")
    has_pcos = st.checkbox("PCOS")

if gender == "ชาย":
    bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
else:
    bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161
multiplier = float(activity_level.split("(")[-1].replace(")", ""))
tdee = bmr * multiplier

col1, col2, col3 = st.columns(3)
col1.metric("BMR (พลังงานพื้นฐาน)", f"{int(bmr)} kcal")
col2.metric("TDEE (พลังงานที่ใช้ต่อวัน)", f"{int(tdee)} kcal")
col3.metric("เป้าหมายลดน้ำหนัก", f"{int(tdee - 500)} kcal")

health_risks = []
if has_diabetes: health_risks.append("- เบาหวาน: จำกัดน้ำตาล เน้น Low-GI")
if has_hypertension: health_risks.append("- ความดัน: ควบคุมโซเดียมไม่ให้เกิน 2,000 มก.")
if has_fatty_liver: health_risks.append("- ไขมันพอกตับ: หลีกเลี่ยงน้ำตาลฟรุกโตส")
if has_knee_pain: health_risks.append("- ข้อเข่าเสื่อม: หลีกเลี่ยงแรงกระแทก")
if has_pcos: health_risks.append("- PCOS: ควบคุมอินซูลิน เน้นโปรตีน/ไฟเบอร์")

st.header("2. AI วิเคราะห์อาหารไทย & ปรับสูตร")
food_input = st.text_input("พิมพ์ชื่อเมนูอาหารไทย หรือรายละเอียด:", placeholder="เช่น ข้าวมันไก่ตอน ไม่เอาหนัง")

class NutritionAnalysis(pydantic.BaseModel):
    menu_name: str
    estimated_calories: int
    protein_g: float
    carbs_g: float
    fat_g: float
    sodium_mg: float
    health_warnings: list[str]
    healthier_customization_tips: list[str]

if st.button("วิเคราะห์เมนู"):
    if not api_key:
        st.error("กรุณาใส่ Gemini API Key ด้านบนก่อนครับ")
    elif not food_input:
        st.error("กรุณากรอกชื่อเมนูก่อนครับ")
    else:
        with st.spinner("Gemini กำลังวิเคราะห์..."):
            try:
                client = genai.Client(api_key=api_key)
                risk_context = ", ".join(health_risks) if health_risks else "ไม่มีโรคพิเศษ"
                prompt = f"""คุณคือนักกำหนดอาหาร ผู้ใช้มีโรคประจำตัว: {risk_context} 
                จงวิเคราะห์เมนู: "{food_input}" ประเมินแคลอรี สารอาหาร คำเตือน และคำแนะนำปรับสูตร"""

                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=NutritionAnalysis,
                        temperature=0.2
                    )
                )
                import json
                res = json.loads(response.text)
                st.success("สำเร็จ!")
                st.write(f"**เมนู:** {res['menu_name']} | **พลังงาน:** {res['estimated_calories']} kcal")
                st.write(f"โปรตีน: {res['protein_g']}g | คาร์บ: {res['carbs_g']}g | ไขมัน: {res['fat_g']}g | โซเดียม: {res['sodium_mg']}mg")

                if res['health_warnings']:
                    for w in res['health_warnings']: st.warning(w)
                for t in res['healthier_customization_tips']:
                    st.info(f"💡 {t}")
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {e}")