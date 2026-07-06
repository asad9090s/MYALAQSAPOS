# POS Mobile - Python to Android APK

Aap ke Tkinter `Shop ok.py` ka Android version - **Kivy + Buildozer** se bana. Same UI flow (Search → Cart → Customer → Checkout), SQLite database (text files ki jagah), aur build ho ke APK ban jayega jo Android phone par install hogi.

---

## 📦 Project Structure

```
POS_Mobile/
├── main.py              # Kivy UI app (POS screen)
├── db.py                # SQLite database layer (same schema as Tkinter)
├── buildozer.spec       # Android build config
├── requirements.txt     # Python deps
├── README.md            # Ye file
└── assets/              # Icon + presplash (add karo)
```

---

## 🚀 Do tareeqe se APK banao

### Tareeqa A: Local Build (Linux/WSL only) - FREE

Buildozer sirf **Linux** par chalta hai (Ubuntu 22+). Windows par WSL2 use karo.

#### 1. WSL install karo (Windows par)
```powershell
# PowerShell as Admin
wsl --install -d Ubuntu-22.04
```
Restart, Ubuntu setup karo (username/password).

#### 2. WSL mein dependencies install
```bash
sudo apt update
sudo apt install -y python3 python3-pip git zip unzip openjdk-17-jdk autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev
pip3 install --user buildozer==1.5.0 cython==0.29.36 virtualenv
echo 'export PATH=$PATH:~/.local/bin' >> ~/.bashrc
source ~/.bashrc
```

#### 3. Project ko WSL mein copy karo
```bash
# Windows se WSL mein access
mkdir ~/pos_mobile
cp /mnt/c/path/to/POS_Mobile/* ~/pos_mobile/
cd ~/pos_mobile
```

#### 4. APK build karo
```bash
buildozer -v android debug
```
Pehli baar **45-60 minute** lagenge (downloads + build). Output:
```
~/pos_mobile/bin/pos_mobile-1.0.0-debug.apk
```

#### 5. Phone par install
- `pos_mobile-1.0.0-debug.apk` ko phone mein copy karo
- File manager se install karo (Unknown sources allow karo)

---

### Tareeqa B: GitHub Actions (Cloud build) - EASIEST ✅

Agar Linux nahi hai ya 1 ghanta wait nahi karna, to GitHub Actions use karo - **free + 20 min**.

#### 1. GitHub repo banao
- https://github.com/new → "pos-mobile" naam do → Public → Create

#### 2. Project upload karo
- "Add file" → "Upload files" → saari files drag-drop → Commit

#### 3. GitHub Action workflow add karo
- "Add file" → "Create new file" → naam: `.github/workflows/build.yml`
- Ye content paste karo:

```yaml
name: Build Android APK

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install Buildozer
        run: |
          pip install buildozer==1.5.0 cython==0.29.36

      - name: Install system deps
        run: |
          sudo apt update
          sudo apt install -y zip unzip openjdk-17-jdk autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev

      - name: Build APK
        run: buildozer -v android debug

      - name: Upload APK artifact
        uses: actions/upload-artifact@v4
        with:
          name: pos-mobile-apk
          path: bin/*.apk
```
- Commit

#### 4. Build trigger ho jayega
- "Actions" tab mein jao
- Build chal raha hoga - **20-25 minute** lagenge
- Complete hone par, build par click → "Artifacts" → `pos-mobile-apk` download

#### 5. APK install karo
- Zip extract → `pos_mobile-1.0.0-debug.apk` phone mein bhejo
- Install

---

## 🎯 App Features

✅ **Same flow as Tkinter** - Search (Barcode/Name) → Cart → Customer → Checkout
✅ **SQLite database** - Local phone storage, no server needed
✅ **Sample data pre-loaded** - 10 products + 4 customers (testing ke liye)
✅ **Barcode scan** - TextInput se (hardware scanner bhi chal jayega)
✅ **Name search** - LIKE query, dropdown
✅ **Cart edit/remove** - per item
✅ **Customer create + select** - new customer popup
✅ **Discount modes** - Per Item / Overall / Percentage
✅ **Bill Disc + Cash Disc**
✅ **Grand Total + Paid + Balance** (auto-calc)
✅ **Cash / Online payment**
✅ **Comments field**
✅ **Sale history** (db.get_sale_history)
✅ **Dashboard stats** (db.get_dashboard_stats)
✅ **Walk-in Customer** auto-default

---

## 🗄️ Database Schema

Same as aap ke Tkinter app:
- `frmClass` - customer groups
- `frmProducts` - products (id, name, barcode, price, stock, PurchasePrice, Minimumq, discount)
- `frmStudentInfo` - customers (name, fatherName=shop, Phone, idclass)
- `saleMaster` - sale headers (InvoiceNumber, idstudent, total, paid, paymentType, ...)
- `frmsaledetail` - sale items (idproduct, quantity, idsaleMaster, price, discount)
- `onlinePayments` - online payment records
- `frmVendor`, `frmCategories`, `expenses`, `users`

DB path Android par: `/data/data/com.pos.pos_mobile/files/pos.db`
DB path Desktop par: `~/.pos_mobile/pos.db`

---

## 🧪 Local Test (Desktop pe)

APK banane se pehle desktop par test karo:

```bash
cd POS_Mobile
pip install kivy==2.3.0
python main.py
```

Window khulega (400x720), mobile jaisa look. Test:
- Search "Coca" → product list
- Click → cart mein add
- "SAVE & PROCESS SALE" → success popup
- `~/.pos_mobile/pos.db` SQLite file check karo

---

## 🔧 Customization

### Shop naam change karna
`main.py` mein `HeaderBar("My Shop")` ko edit karo:
```python
self.header = HeaderBar("Aap Ki Dukaan")
```

### Sample data hataana
`main.py` mein `_init_db` method mein ye line comment karo:
```python
# added = self.pos_screen.db.seed_sample_data()
```

### Real data import (Tkinter se)
Tkinter app ke textdb se data migrate karne ke liye ye script use karo:

```python
# migrate.py (separately run karo desktop pe)
import os, sqlite3
from db import MobileDB

# 1. TextFileDB se read karo (aap ke Shop ok.py ka format)
TEXTDB = "C:/path/to/textdb"

# 2. SQLite mein write
db = MobileDB("./pos.db")
# ... loop through products/customers/sales and insert
```

Main ye script bhi bana sakta hoon agar chahiye.

---

## 🎨 Icons & Splash

`assets/` folder mein ye 2 files add karo:
- `icon.png` - 512x512 PNG (app icon)
- `presplash.png` - 512x512 PNG (splash screen)

Ya free icons: https://icons8.com se download karo.

---

## 🚨 Common Issues

| Problem | Solution |
|---------|----------|
| `buildozer: command not found` | `pip install buildozer` aur `~/.local/bin` PATH mein add |
| Java error during build | `sudo apt install openjdk-17-jdk` |
| Build stuck at "Download SDK" | Internet slow - 60 min wait |
| APK crash on phone | `adb logcat \| grep python` se logs dekho |
| `sqlite3` import error | Buildozer `requirements` mein `sqlite3` add hai (built-in hai) |
| Phone storage permission | App settings → Permissions → Storage → Allow |
| App not visible after install | App drawer mein "POS Mobile" naam se dikhna chahiye |

---

## 📊 Next Steps

### 1. Print support (Bluetooth thermal printer)
- `escpos` library use karo
- `requirements = escpos` buildozer.spec mein add karo
- Bluetooth printer ke saath pair karke print karo

### 2. Login screen
- `users` table already hai
- Login screen banao jo `db.verify_user(username, password)` call kare

### 3. Reports screens
- `db.get_sale_history()` use karke sales list dikhao
- `db.get_dashboard_stats()` se today's total

### 4. Cloud sync
- Firebase ya REST API se data ko server par sync karo
- Multi-device support

### 5. Real barcode scanner (camera)
- `zbarlight` ya `pyzbar` use karo
- Camera permission add karo

---

## 📞 Support

Agar build mein issue aaye to:
1. Pura error log bhejo
2. `buildozer.spec` ka content bhejo
3. `requirements.txt` ka content bhejo

Main exact fix dunga.

**Apna phone ka Android version bhi batao** (Settings → About → Android version) - min API 24 (Android 7+) chahiye.
