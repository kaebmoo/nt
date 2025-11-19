# ETL Integration Quick Start
## เริ่มต้นใช้งาน ETL Admin Tab

---

## 🚀 Quick Deployment (3 Steps)

### 1. ตรวจสอบ Integration

```bash
cd /Users/seal/Documents/GitHub/nt/revenue-report-web
python etl_integration.py
```

✅ **ต้องเห็น:** `Valid: True`

---

### 2. รัน Application

```bash
streamlit run app.py
```

---

### 3. Login & Access

1. **Login** ด้วย admin account
2. คลิกที่ tab **"🔧 ETL Admin"**
3. คลิก **"📂 Load ETL Configuration"**
4. เริ่มใช้งาน!

---

## 📋 Files Overview

| File | Purpose |
|------|---------|
| `etl_integration.py` | จัดการ ETL imports และ paths |
| `etl_admin_tab.py` | ETL admin interface (refactored) |
| `app.py` | Main app (modified - added ETL tab) |

---

## 🔧 Common Tasks

### Load ETL Configuration

**Sidebar → "📂 Load ETL Configuration"**

### Run FI Module

**Sidebar → "1️⃣ Run FI Module"**

หรือ

**Tab: FI Module → "▶️ Run FI Processing"**

### Run ETL Module

**Sidebar → "2️⃣ Run ETL Module"**

หรือ

**Tab: ETL Module → "▶️ Run ETL Pipeline"**

### Run All (FI + ETL)

**Sidebar → "▶️ Run All"**

### Check Reconciliation

**Tab: Reconciliation**
- ดูผล Monthly/YTD reconciliation
- ตรวจสอบ tolerance
- ดู differences

### View Logs

**Tab: Logs**
- เลือกไฟล์ log
- Filter by level (ERROR, WARNING, INFO)
- Search in logs

---

## ⚡ Keyboard Shortcuts (Streamlit)

- `R` - Rerun app
- `C` - Clear cache
- `Esc` - Close sidebar

---

## 🔒 Access Control

| Feature | User | Admin |
|---------|------|-------|
| Browse Reports | ✅ | ✅ |
| Send Email | ✅ | ✅ |
| ETL Admin | ❌ | ✅ |

---

## 🐛 Quick Troubleshooting

### ❌ "ETL System Integration Error"

**Fix:**
```bash
# Check path
ls -la /Users/seal/Documents/GitHub/nt/revenue-report/config.json

# Test integration
python etl_integration.py
```

---

### ❌ "Access Denied"

**Fix:** Login ด้วย **admin** account

---

### ❌ "Configuration not loaded"

**Fix:** คลิก **"📂 Load ETL Configuration"** ใน sidebar

---

## 📊 Session State Reference

### Web App States
- `logged_in`
- `user_data`
- `user_email`

### ETL Admin States (isolated)
- `etl_config_manager`
- `etl_system`
- `etl_fi_completed`
- `etl_etl_completed`

**Note:** ใช้ `etl_` prefix เพื่อหลีกเลี่ยง collision

---

## 📞 Need Help?

**Full Documentation:**
- `ETL_INTEGRATION_GUIDE.md` (detailed guide)
- `/revenue-report/README.md` (ETL system docs)

**Test Integration:**
```bash
python etl_integration.py
```

**Expected Output:**
```
Valid: True
ETL Base Exists: True
Config File Exists: True
Modules Available: True
```

---

**Happy Processing! 🎉**
