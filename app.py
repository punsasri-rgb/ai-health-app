import streamlit as st
from google import genai
from google.genai import types
import pydantic
from typing import List, Optional

# ตั้งค่าหน้าจอ Streamlit
st.set_page_config(page_title="AI Health & Nutrition Assistant", page_icon="🥗", layout="wide")

st.title("🥗 AI Health & Nutrition Assistant")
st.subheader("ระบบวิเคราะห์โภชนาการและคำนวณแผนสุขภาพ")

# ช่องกรอก API Key
api_key = st.text_input("ใส่ Google Gemini API Key ของคุณที่นี่ (หาได้จาก Google AI Studio):", type="password")

if not api_key:
    st.info("กรุณากรอก API Key เพื่อเริ่มใช้งาน")
    st.stop()

# สร้าง Client เชื่อมต่อ Gemini API
client = genai.Client(api_key=api_key)

# กำหนดโครงสร้างข้อมูลผลลัพธ์ (Schema) ด้วย Pydantic ให้รองรับครบทั้ง 6 ข้อ
class NutritionAnalysis(pydantic.BaseModel):
    item_1_bmr_tdee: str
    item_2_caloric_target: str
    item_3_macronutrients: str
    item_4_menu_analysis: str
    item_5_health_recommendations: str
    item_6_workout_plan: str

# ฟอร์มรับข้อมูลผู้ใช้
with st.form("user_info_form"):
    st.markdown("### 📋 กรอกข้อมูลส่วนตัวและเมนูอาหาร")
    col1, col2, col3 = st.columns(3)
    with col1:
        age = st.number_input("อายุ (ปี)", min_value=10, max_value=120, value=25)
        gender = st.selectbox("เพศ", ["ชาย", "หญิง"])
    with col2:
        weight = st.number_input("น้ำหนัก (กก.)", min_value=30.0, max_value=200.0, value=60.0)
        height = st.number_input("ส่วนสูง (ซม.)", min_value=100.0, max_value=250.0, value=170.0)
    with col3:
        activity_level = st.selectbox(
            "ระดับการออกกำลังกาย",
            [
                "ไม่ออกกำลังกาย / นั่งทำงานเป็นหลัก",
                "ออกกำลังกายเบาๆ (1-3 วัน/สัปดาห์)",
                "ออกกำลังกายปานกลาง (3-5 วัน/สัปดาห์)",
                "ออกกำลังกายหนัก (6-7 วัน/สัปดาห์)",
                "ออกกำลังกายหนักมาก / นักกีฬา"
            ]
        )
        goal = st.selectbox("เป้าหมายสุขภาพ", ["ลดน้ำหนัก", "รักษาน้ำหนัก", "เพิ่มกล้ามเนื้อ"])

    user_menu = st.text_area("ระบุเมนูอาหารไทยที่รับประทานในวันนี้ (เช่น ข้าวมันไก่, ส้มตำไทย, ต้มยำกุ้ง):")
    submit_button = st.form_submit_button("🚀 วิเคราะห์ข้อมูลสุขภาพและเมนูอาหาร")

if submit_button:
    if not user_menu:
        st.warning("กรุณาระบุเมนูอาหารไทยก่อนกดวิเคราะห์")
    else:
        with st.spinner("กำลังประมวลผลข้อมูลโภชนาการด้วย AI..."):
            prompt = f"""
            คุณเป็นผู้เชี่ยวชาญด้านโภชนาการและวิทยาศาสตร์การกีฬา
            ข้อมูลผู้ใช้:
            - เพศ: {gender}, อายุ: {age} ปี, น้ำหนัก: {weight} กก., ส่วนสูง: {height} ซม.
            - ระดับกิจกรรม: {activity_level}
            - เป้าหมาย: {goal}
            - เมนูอาหารที่รับประทานวันนี้: {user_menu}

            กรุณาวิเคราะห์และจัดทำรายงานโภชนาการให้ครบทั้ง 6 ข้อดังต่อไปนี้:
            ข้อ 1. คำนวณค่า BMR และ TDEE
            ข้อ 2. คำนวณเป้าหมายแคลอรีต่อวันตามเป้าหมาย ({goal})
            ข้อ 3. สัดส่วนสารอาหารหลัก (Macronutrients: โปรตีน, คาร์โบไฮเดรต, ไขมัน)
            ข้อ 4. วิเคราะห์เมนูอาหารที่ระบุ ({user_menu}) ประมาณการแคลอรีและสารอาหาร
            ข้อ 5. คำแนะนำด้านสุขภาพและการปรับโภชนาการเพิ่มเติม
            ข้อ 6. แนะนำแผนการออกกำลังกายที่เหมาะสม
            """

            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=NutritionAnalysis,
                    ),
                )

                # ดึงข้อมูล JSON ที่ได้แปลงเป็น Pydantic Object
                result = NutritionAnalysis.model_validate_json(response.text)

                st.success("✅ วิเคราะห์ข้อมูลเรียบร้อยแล้ว!")
                st.markdown("---")

                # แสดงผลลัพธ์ครบทั้ง 6 ข้อ
                st.markdown(f"### 1. ค่า BMR และ TDEE\n{result.item_1_bmr_tdee}")
                st.markdown(f"### 2. เป้าหมายแคลอรีประจำวัน\n{result.item_2_caloric_target}")
                st.markdown(f"### 3. สัดส่วนสารอาหารหลัก (Macronutrients)\n{result.item_3_macronutrients}")
                st.markdown(f"### 4. ผลการวิเคราะห์เมนูอาหาร\n{result.item_4_menu_analysis}")
                st.markdown(f"### 5. คำแนะนำด้านสุขภาพและการปรับโภชนาการ\n{result.item_5_health_recommendations}")
                st.markdown(f"### 6. แนะนำแผนการออกกำลังกาย\n{result.item_6_workout_plan}")

            except Exception as e:
                st.error(f"เกิดข้อผิดพลาดในการประมวลผล: {e}")
