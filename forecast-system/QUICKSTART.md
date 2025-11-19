# 🚀 Quick Start Guide - ระบบพยากรณ์

## ติดตั้ง (Installation)

### วิธีที่ 1: ใช้ Install Script (แนะนำ)
```bash
cd /home/user/nt/forecast-system
chmod +x install.sh
./install.sh
```

### วิธีที่ 2: ติดตั้งแบบ Manual
```bash
# แก้ปัญหา Prophet/CmdStanPy ก่อน
pip uninstall -y polars cmdstanpy prophet
pip install "polars<0.20.0"
pip install "cmdstanpy>=1.2.0"
pip install "prophet>=1.1.5"

# ติดตั้ง requirements อื่นๆ
pip install -r requirements.txt
```

---

## วิธีใช้งาน

### 1️⃣ รันตัวอย่าง (Command Line)

```bash
cd /home/user/nt/forecast-system

# ตัวอย่าง Joint Forecasting (4 วิธี)
python examples/joint_forecast_example.py
```

**ผลลัพธ์ที่ได้**:
- เปรียบเทียบ 4 วิธีพยากรณ์ (Sequential, VAR, XGBoost, Method Comparison)
- แสดงกราฟเปรียบเทียบความแม่น
- แสดง Profit/Margin Analysis

---

### 2️⃣ รัน Web Interface (Streamlit)

```bash
cd /home/user/nt/forecast-system
streamlit run src/web/app.py
```

**เปิดเว็บ**: http://localhost:8501

**ฟีเจอร์ใน Web**:
- อัปโหลดข้อมูล CSV/Excel
- เลือก Model (Prophet, SARIMAX, XGBoost, Ensemble)
- ปรับพารามิเตอร์
- ดาวน์โหลดผลลัพธ์

---

## 📁 โครงสร้างข้อมูลที่รองรับ

### สำหรับ Joint Forecasting (รายได้+ค่าใช้จ่ายพร้อมกัน)

```csv
date,revenue,expense,sales_unit,product
2024-01-01,100000,60000,BKK,Product_A
2024-02-01,120000,70000,BKK,Product_A
2024-03-01,110000,65000,BKK,Product_A
...
```

**คอลัมน์ที่จำเป็น**:
- `date`: วันที่ (รูปแบบ YYYY-MM-DD)
- `revenue`: รายได้
- `expense`: ค่าใช้จ่าย

**คอลัมน์เสริม (Optional)**:
- `sales_unit`: หน่วยขาย
- `product`: ผลิตภัณฑ์
- `gl_code`: รหัสบัญชี
- `department`: แผนก

---

## 🔧 แก้ปัญหาที่พบบ่อย

### ❌ Error: `schema_overrides` not found
**สาเหตุ**: polars version ใหม่เกินไป

**วิธีแก้**:
```bash
pip uninstall -y polars
pip install "polars<0.20.0"
```

---

### ❌ Error: Prophet model failed
**วิธีแก้**: ใช้ model อื่นแทน

แก้ไขใน `src/web/app.py`:
```python
# เปลี่ยนจาก
model_type = st.selectbox("Select Model", ["prophet", "sarimax", "xgboost"])

# เป็น (ใช้ SARIMAX เป็นค่าเริ่มต้น)
model_type = st.selectbox("Select Model", ["sarimax", "xgboost", "prophet"])
```

---

### ❌ Error: No module named 'cmdstanpy'
**วิธีแก้**:
```bash
pip install cmdstanpy>=1.2.0
```

---

## 📊 ตัวอย่างโค้ดเรียกใช้

### Python Code (แบบง่าย)
```python
import pandas as pd
from src.engines.joint_engine import JointForecastEngine

# โหลดข้อมูล
df = pd.read_csv("your_data.csv")

# สร้าง Engine
engine = JointForecastEngine()

# พยากรณ์แบบ Sequential (รายได้ → ค่าใช้จ่าย)
result = engine.forecast_sequential(
    df_revenue=df,
    df_expense=df,
    date_column='date',
    revenue_column='revenue',
    expense_column='expense',
    periods=12
)

# ดูผลลัพธ์
print(result.revenue_forecast)
print(result.expense_forecast)
print(result.profit_forecast)
```

---

## 📚 เอกสารเพิ่มเติม

- **Joint Forecasting Guide**: `JOINT_FORECASTING_GUIDE.md`
- **API Documentation**: `docs/API.md`
- **Examples**: `examples/`

---

## 💡 Tips

1. **Model Selection**:
   - Prophet: ดีสำหรับข้อมูลที่มี Seasonality ชัดเจน
   - SARIMAX: ดีสำหรับข้อมูลที่มีแนวโน้มเชิงเส้น
   - XGBoost: ดีสำหรับข้อมูลที่มี Non-linear patterns
   - Ensemble: รวมทุก Model (แม่นที่สุดแต่ช้าที่สุด)

2. **Data Quality**:
   - ควรมีข้อมูลอย่างน้อย 24 เดือน
   - ไม่ควรมีค่าว่าง (missing values) มากกว่า 10%
   - ควรทำความสะอาดข้อมูล Outliers ก่อน

3. **Performance**:
   - Peer Group Analysis ใช้เวลานาน → ปิดได้ถ้าไม่ใช้
   - ใช้ `hierarchicalforecast` เฉพาะกรณีต้องการ reconciliation

---

## 🆘 ติดปัญหา?

1. ตรวจสอบ Python version: ต้อง >= 3.8
2. ตรวจสอบ pip version: `pip --version`
3. ลองติดตั้งใหม่ด้วย `./install.sh`

---

**สร้างโดย**: Claude Code Agent
**วันที่**: 2025-11-18
**เวอร์ชัน**: 1.0.0
