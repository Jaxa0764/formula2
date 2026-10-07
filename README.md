# 🚀 SmartFuel UZ — Fuel & EV Smart Navigator Platform for Uzbekistan

**SmartFuel UZ** — O'zbekistondagi avtoyoqilg'i (AI-80, AI-91, AI-92, AI-95, AI-98, Dizel), yuqori bosimli metan (CNG), propan (LPG) va elektromobillarni tezkor quvvatlash (EV Fast DC / Ultra-Fast) shoxobchalarini real-vaqtda kuzatish, eng arzon narxlarni taqqoslash va marshrut tuzish uchun mo'ljallangan zamonaviy platforma.

---

## 🌟 Asosiy Imkoniyatlar

1. **Interaktiv Katta Xarita (Leaflet.js + CartoDB Dark Matter)**:
   - Shaharlar: Toshkent, Samarqand, Buxoro, Farg'ona, Andijon, Namangan
   - Rangli maxsus SVG pinlar: 🟢 Metan (CNG), 🟠 Propan (LPG), ⛽ Benzin/Dizel, ⚡ EV Zaryadlash, 🔴 Yopiq/Ta'mirda
   - Foydalanuvchining real-vaqtdagi radar joylashuvi
2. **"Tavsiya etilgan eng maqbul variant" (Best Option AI algoritmi)**:
   - Masofa, narx, gaz bosimi, navbat uzunligi va reytingni hisobga olgan holda eng optimal zapravkani aniqlaydi va asoslab beradi.
3. **Aqlli AI Yordamchi (Floating AI Assistant)**:
   - Real ma'lumotlar bazasiga ulangan.
   - Savollar: *"Eng arzon AI-92 qayerda?"*, *"Eng yaqin metan zapravkani top"*, *"Bo'sh EV zaryadkalar qayerda?"*, *"Yaqin 3 ta zapravkani taqqosla"*.
   - Javoblar ichida `[Xaritada ko'rsatish]`, `[Marshrut tuzish]`, `[Batafsil]` interaktiv tugmalari mavjud.
4. **Real-Vaqt Yangilanishlar (WebSockets)**:
   - Administrator narx yoki metan bosimini o'zgartirganda sahifani yangilamasdan (reload qilmasdan) darhol aks etadi.
5. **Kuchli Administrator Boshqaruv Markazi (`/admin.html`)**:
   - 16 ta bo'lim: Umumiy ko'rsatkichlar (KPIs), Zapravkalar boshqaruvi (CRUD), CNG metan bosimi slayderi, Narxlarni ommaviy yangilash, EV zaryadlash nazorati, Shikoyatlar, Ogohlantirishlar, Audit jurnali (Logs), Foydalanuvchilar va rollar (RBAC).

---

## ⚡ Qanday Ishga Tushiriladi? (Start Berish Qo'llanmasi)

Platformani ishga tushirish uchun 2 ta server (Backend va Frontend) yurgaziladi:

### 1-Usul: Tezkor start (Hozirgi holatda ishlayapti!)

Hozirda ikkala server ham fonda avtomatik tarzda ishlab turibdi:
* **Foydalanuvchi interfeysi (Asosiy xarita va AI)**: [http://localhost:5173/](http://localhost:5173/)
* **Administrator boshqaruv paneli**: [http://localhost:5173/admin.html](http://localhost:5173/admin.html)
* **Backend API Swagger Hujjatlari**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

### 2-Usul: Qo'lda start berish (Terminal orqali)

#### A) Backend serverini ishga tushirish (FastAPI):
Terminalda loyiha papkasiga kiring va quyidagi buyruqni bering:
```bash
cd /home/azaroot/Desktop/formula
PYTHONPATH=backend .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
*Backend `http://localhost:8000` manzilida ishlaydi.*

#### B) Frontend serverini ishga tushirish (Vite):
Boshqa terminal oynasida frontend papkasiga kiring va bering:
```bash
cd /home/azaroot/Desktop/formula/frontend
npm run dev
```
*Frontend `http://localhost:5173` manzilida ishlaydi.*

---

## 🔑 Demo Kirish Ma'lumotlari

* **Super Admin**:
  - Email: `admin@smartfuel.uz`
  - Parol: `admin123`
* **Oddiy foydalanuvchi**:
  - Email: `user@smartfuel.uz`
  - Parol: `user123`

---

## 🗄️ Ma'lumotlar Bazasini Qayta To'ldirish (Seed Data)

Agar ma'lumotlarni qaytadan tozalab, boshlang'ich 16 ta haqiqiy o'zbek shoxobchasi bilan to'ldirmoqchi bo'lsangiz:
```bash
cd /home/azaroot/Desktop/formula
.venv/bin/python backend/seed/seed_uzbekistan.py
```

---

## 🐳 Docker orqali ishga tushirish (PostgreSQL bilan)

```bash
docker-compose up -d --build
```
