# Ansh Air Cool - AC Service Billing System — पूरा सॉफ्टवेयर डॉक्यूमेंटेशन

---

## 1. SOFTWARE KA PARICHAY (Overview)

| Field | Value |
|---|---|
| **Software Name** | Ansh Air Cool - Billing System |
| **App Name (internal)** | `AC_Service_Billing` |
| **Version** | `1.0.0` |
| **Company** | Ansh Air Cool |
| **Purpose** | AC service & AMC billing, customer management, technician tracking, inventory, online requests, daily logs |
| **Platform** | Windows Desktop (PySide6 / Qt6) |
| **Database** | SQLite (`data/desktop_software.db`) |
| **UI Language** | English + Hindi (via `utils/language.py`) |
| **Project Root** | `D:\Desktop_software-main\` |

---

## 2. SOFTWARE KAAM KAISE KARTA HAI (How Software Works)

### 2.1 STARTUP PROCESS (main.py)

```
Jab software start hota hai → yeh hota hai:

1. main() function call hota hai
2. Application() class create hoti hai
3. QApplication(sys.argv) — Qt application initialize hota hai
4. Font set hota hai: 'Segoe UI', 10pt (pura app mein same font)
5. _setup_database() call hota hai:
   - DatabaseConnection() — SQLite se connection banane ki koshish
   - Agar DB connect nahi hota → ERROR dialog dikhta hai "Cannot connect to database"
   - Agar error aaya → sys.exit(1) se program band ho jata hai
6. _show_splash() call hota hai:
   - assets/logo.png image load hoti hai
   - Agar logo nahi mila → assets/Logo.png try hoti hai
   - Agar dono nahi mile → blank white image (400x300) create hoti hai
   - Splash screen show hoti hai with "App Name" + "Version" + "Starting..."
   - Splash 2 second (2000ms) ke liye dikhti hai (WindowStaysOnTopHint)
7. QTimer.singleShot(2000, _show_login) — 2 second baad:
   - LOGIN_ENABLED = True → LoginWindow dikhti hai
   - LOGIN_ENABLED = False → direct MainWindow open hota hai (admin user DB se fetch karke)
```

### 2.2 LOGIN SYSTEM (login_view.py + auth_controller.py)

```
LOGIN WINDOW UI:
- Full screen QMainWindow
- Background: assets/login_page.png (poori screen cover karti hai)
- Dark overlay: rgba(15, 23, 42, 0.85) — background ke upar semi-transparent layer
- Center mein ek glass card (max-width 400px):
  * Logo image (top)
  * "Ansh Air Cool - Billing System" title (large)
  * Username input field
  * Password input field (with eye button → password dikhata/chhupata hai)
  * "Remember Me" checkbox
  * "Login" button (cyan color)
  * "Forgot Password?" link (bottom)
  * Error label (red, initially hidden)

LOGIN KAISE KAAM KARTA HAI:
1. User username/password enter karta hai
2. "Login" button click karta hai
3. _on_login() function call hota hai:
   a. Fields validate hote hain: dono empty nahi hone chahiye
   b. auth_controller.login(username, password, remember_me) call hota hai
   c. Controller kya karta hai:
      - check_lockout() — kya user lockout hai? Agar 5 failed attempts hain aur 15 min nahi huye → error "Account locked"
      - Database se user fetch karta hai (username se)
      - bcrypt.checkpw() — user ke password hash se match karta hai
      - Agar match → login successful
      - Agar match nahi → record_failed_attempt(username) — failed count badhata hai
      - Agar failed attempts >= 5 → is_lockout = True, 15 min ka timer set
      - Agar successful → reset_failed_attempts(username) — failed count 0 karta hai
      - Agar "Remember Me" checked → username save hota hai (local settings mein)
   d. Success → on_login_success(user_data) signal emit hota hai
   e. LoginWindow close hoti hai
   f. MainWindow(user_data, on_logout) open hota hai

PASSWORD STRENGTH INDICATOR:
- Jab user password type karta hai, har character ke baad validate_password_strength() call hota hai
- Check karta hai: min 8 chars, uppercase, lowercase, digit, special character
- Ek bar dikhta hai: red (weak) → yellow (medium) → green (strong)
```

### 2.3 MAIN WINDOW (main_window.py)

```
MAIN WINDOW UI:
- QMainWindow (maximized on launch)
- Layout:
  ┌──────────────────────────────────────────────────────┐
  │  HEADER: [App Name]        [🔔 User: Admin] [🚪Logout]│
  ├──────────┬───────────────────────────────────────────┤
  │ SIDEBAR  │                                           │
  │ 📊 Dash  │         QStackedWidget                    │
  │ ➕ Inv.  │         (Content Area)                    │
  │ 📋 Inv.  │                                           │
  │ 👥 Cust  │     Active view dikhta hai                │
  │ 🔧 Tech  │     (Dashboard/Invoices/etc)              │
  │ 📅 AMC   │                                           │
  │ 📝 Logs  │                                           │
  │ 🌐 Req.  │                                           │
  │ 📈 Rep.  │                                           │
  │ 📦 Inv.  │                                           │
  │ ⚙️ Set.  │                                           │
  │ 🚪 Exit  │                                           │
  ├──────────┴───────────────────────────────────────────┤
  │ STATUS BAR: [User: Admin] [Shop: Ansh Air Cool]      │
  │            [Date: 20-05-2026] [DB: ✅ Connected]      │
  └──────────────────────────────────────────────────────┘

MAIN WINDOW KAISE KAAM KARTA HAI:
1. __init__() mein:
   a. user_data (login se aaya) store hota hai
   b. on_logout callback store hota hai
   c. SessionManager mein user login hota hai (get_session().login(user_data))
   d. _setup_ui() — sidebar + stacked widget + header + status bar banate hain
   e. _load_user_data() — user ka naam, role header mein dikhata hai
   f. _connect_navigation() — sidebar buttons ko stacked widget ke index se connect karta hai
   g. Sabse pehle Dashboard view (index 0) show hota hai

2. Sidebar Navigation:
   - Har button QPushButton hai, jiska icon + label hota hai
   - Button click → _navigate_to(index) call hota hai
   - _navigate_to():
     a. QStackedWidget.setCurrentIndex(index) — view switch hota hai
     b. Pichle active button ka style reset hota hai
     c. Naye button par active style apply hota hai (cyan left border)
   
3. Logout:
   - Logout button click → _on_logout() call hota hai
   - SessionManager.logout() — session end hota hai
   - MainWindow close hoti hai
   - on_logout() callback → main.py mein _show_login() call hota hai
   - LoginWindow phir se open hoti hai

4. Notification Bell:
   - 🔔 icon → click → ReminderDialog open hota hai (AMC expiry + pending payments)
   - Badge number dikhta hai (kitne reminders pending hain)
```

---

## 3. HAR SECTION KA UI AUR KAAM KAISE KARTA HAI

### 3.1 DASHBOARD (enhanced_dashboard_view.py)

```
UI STRUCTURE:
┌──────────────────────────────────────────────────────┐
│ 📊 Dashboard                        📅 20-05-2026   │
├──────────────────────────────────────────────────────┤
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐│
│ │ 👥 1,234  │ │ 📄 5,678 │ │ 💰 ₹45L  │ │ ⏳ ₹2.3L ││
│ │ Customers │ │ Invoices │ │ Revenue  │ │ Pending  ││
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘│
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐│
│ │ 🛠️ 12   │ │ 💵 ₹8K   │ │ 🆕 3     │ │ 📊 45    ││
│ │ Services │ │ Collected│ │ New Cust │ │ ActiveAMC││
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘│
├──────────────────────────────────────────────────────┤
│ ┌──────────────┐ ┌──────────────┐                    │
│ │  Revenue     │ │ Top Services │                    │
│ │  Trend Chart │ │ Pie Chart    │                    │
│ │  [BARS]      │ │ [DONUT]     │                    │
│ └──────────────┘ └──────────────┘                    │
│ ┌──────────────┐ ┌──────────────┐                    │
│ │ Payment      │ │ Stock Status │                    │
│ │ Status Chart │ │ Chart        │                    │
│ │ [H-BARS]     │ │ [BARS]       │                    │
│ └──────────────┘ └──────────────┘                    │
├──────────────────────────────────────────────────────┤
│ Search: [_______________]  Date: [__] to [__]        │
│ ┌──────┬────────┬────────┬────────┬──────────┐       │
│ │ Inv# │ Cust   │ Amount │ Status │  Date    │       │
│ ├──────┼────────┼────────┼────────┼──────────┤       │
│ │ INV  │ Ram    │ ₹2,500 │ ✅Paid │ 20-05-26│       │
│ │ 1001 │ Sharma │        │        │          │       │
│ └──────┴────────┴────────┴────────┴──────────┘       │
└──────────────────────────────────────────────────────┘

DASHBOARD KAISE KAAM KARTA HAI:
1. Jab Dashboard view load hota hai, _load_data() call hota hai
2. _load_data() → dashboard_controller.get_dashboard_stats() call hota hai
3. get_dashboard_stats() ek hi SQL query mein 7 stats laata hai:
   - SELECT (SELECT COUNT(*) FROM customers WHERE is_active=TRUE) as total_customers
   - (SELECT COUNT(*) FROM invoices WHERE is_active=TRUE) as total_invoices
   - ... ek sath 7 subqueries
   - Aur 12 months ka revenue data: MONTH(invoice_date) ke GROUP BY se
4. Data aane ke baad:
   a. 8 MetricCards update hote hain (value + label)
   b. 4 Charts update hote hain (set_data() call)
   c. Summary table refresh hoti hai
5. MetricCard clickable hai — click karne par relevant view/section open hota hai
   (e.g., "Total Customers" click → Customer view open)
6. Charts custom QPainter se draw hote hain (koi library nahi)
7. Dashboard har baar view switch par refresh hota hai (current data dikhata hai)
```

### 3.2 INVOICE CREATION (invoice_view.py - Tab 1: New Invoice)

```
UI STRUCTURE:
┌──────────────────────────────────────────────────────┐
│ 📄 New Invoice                    [Save] [Reset]     │
├──────────────────────────────────────────────────────┤
│ ┌─ CUSTOMER DETAILS ───────────────────────────┐     │
│ │ Search: [🔍______________________]            │     │
│ │ Mobile: [___________]  Name: [___________]    │     │
│ │ Address: [___________________________]        │     │
│ │ [➕ New Customer]                             │     │
│ └──────────────────────────────────────────────┘     │
│ ┌─ AC DETAILS ─────────────────────────────────┐     │
│ │ Brand: [▼ Select]  Type: [▼ Split/Window]    │     │
│ │ Ton: [▼ 1.5]  Star: [▼ 3]  Inverter: [▼ Yes]│     │
│ └──────────────────────────────────────────────┘     │
│ ┌─ TECHNICIAN ────────────────────────────────┐     │
│ │ Technician: [▼ Select Technician]             │     │
│ └──────────────────────────────────────────────┘     │
│ ┌─ ITEMS ─────────────────────────────────────┐     │
│ │ Type│ Item Name     │ Qty│ Rate│ Amount      │     │
│ ├─────┼───────────────┼────┼────┼─────────────┤     │
│ │Serv.│ Gas Filling   │ 1  │ 500│ 500         │     │
│ │Part │ Compressor    │ 1  │3500│ 3500        │     │
│ │ [➕ Add Row]                         [🗑️ Del]│     │
│ └──────────────────────────────────────────────┘     │
│ ┌─ TOTALS ────────────────────────────────────┐     │
│ │ Subtotal:                      ₹4,000.00     │     │
│ │ GST (18%):                    ₹720.00        │     │
│ │ ──────────────────────────────────────────   │     │
│ │ TOTAL:                        ₹4,720.00      │     │
│ │ Advance: [___________]  Balance: ₹4,720.00   │     │
│ │ Payment Mode: [▼ Cash]                       │     │
│ └──────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────┘

NEW INVOICE KAISE KAAM KARTA HAI:
1. Customer Section:
   a. "Search" field mein user phone ya name type karta hai
   b. search_widget.py ka QuickCustomerSearch — har 300ms debounce ke baad DB se search
   c. Search results dropdown mein dikhte hain
   d. User kisi customer par click karta hai → customer_selected(dict) signal emit
   e. Signal se mobile, name, address fields auto-fill ho jate hain
   f. Agar customer nahi mila → "New Customer" button click → inline form se create
   g. Customer create → insert in DB → naya ID aata hai

2. AC Details:
   a. Brand dropdown → DB se ac_brands table fetch
   b. AC Type, Ton, Star, Inverter → master data se pre-filled options
   c. Sab manual select karna hota hai

3. Items Table:
   a. "Add Row" button → nayi row insert karta hai items table mein
   b. Har row mein: Type (Service/Part dropdown), Item Name (service/part se fetch), Qty, Rate, Amount
   c. Rate change → Amount = Qty × Rate auto-calculate
   d. Koi bhi row delete kar sakte hain
   e. Total items ka Amount → Subtotal update hota hai

4. Totals:
   a. Subtotal = sum of all item amounts
   b. GST = Subtotal × 18% (configurable in config.py GST_PERCENTAGE)
   c. Total = Subtotal + GST
   d. Advance user enter karta hai → Balance = Total - Advance
   e. Payment Mode: Cash/UPI/Card/NetBanking

5. Save Invoice Button click:
   a. invoice_controller.create_invoice(data) call hota hai
   b. Yeh 6-step TRANSACTION hai:
      Step 1: mobile number se customer check karo → mila toh use karo, nahi toh create karo
      Step 2: AC brand check karo → mila toh use, nahi toh create
      Step 3: Technician fetch karo (by ID)
      Step 4: INSERT into invoices table (invoice_number auto-generate)
      Step 5: INSERT each item into invoice_items table
      Step 6: Agar Part items hain → stock_quantity deduct karo (UPDATE parts)
      Agar koi bhi step fail → ROLLBACK (sab kuch undi ho jata hai)
   c. Success → PDFGenerator.invoice_pdf(invoice_data) call → pdfs/INV-{number}.pdf save
   d. EventBus.invoice_created.emit() — doosre views ko pata chal jaata hai
   e. Success message: "✅ Invoice INV1001 created successfully!"
   f. Form reset hota hai (naye invoice ke liye ready)

6. Reset Button → poora form clear kar deta hai
```

### 3.3 INVOICE LIST (invoice_view.py - Tab 2 / invoice_management_view.py)

```
UI STRUCTURE:
┌──────────────────────────────────────────────────────┐
│ 📋 Invoices                               [➕ Export]│
├──────────────────────────────────────────────────────┤
│ Search: [________________]  Status: [▼ All]          │
│ From: [📅__/__/____]  To: [📅__/__/____]  [🔍Search]│
├──────────────────────────────────────────────────────┤
│ ┌────┬──────┬────────┬────────┬───────┬──────┬──────┐│
│ │ #  │ Inv# │ Custo- │ Amount │Status │Date  │Action││
│ │    │      │ mer    │        │       │      │      ││
│ ├────┼──────┼────────┼────────┼───────┼──────┼──────┤│
│ │ 1  │ 1001 │ Ram    │₹4,720  │✅Paid │20-05 │ [👁️] ││
│ │ 2  │ 1002 │ Shyam  │₹2,500  │⏳Pend.│19-05 │ [👁️] ││
│ │ 3  │ 1003 │ Mohan  │₹6,000  │🟡Part.│18-05 │ [👁️] ││
│ └────┴──────┴────────┴────────┴───────┴──────┴──────┘│
│                                    Page: [1] of [10]  │
│ Right-click menu: [View] [Edit] [Download PDF]        │
│                   [Email] [WhatsApp] [Print] [Delete]  │
└──────────────────────────────────────────────────────┘

INVOICE LIST KAISE KAAM KARTA HAI:
1. View load hote hi _load_invoices() call hota hai
2. invoice_controller.get_all_invoices(search, status, from_date, to_date) call
3. SQL query invoices table se data laati hai (with search/filter conditions)
4. Table populate hota hai har invoice ke liye ek row
5. Status ke hisaab se color:
   - 'Paid' → green text/badge
   - 'Pending' → amber/red text/badge
   - 'Partial' → yellow text/badge
6. Search/Filter:
   a. User search field mein type karta hai
   b. Ya status combo box change karta hai
   c. Ya date range select karta hai
   d. "Search" button click → _load_invoices() phir se call hota hai with new filters
7. Right-click menu (context menu):
   - View → invoice detail dialog
   - Edit → edit_invoice_dialog open (sab fields editable)
   - Download PDF → PDFGenerator se PDF generate/existing PDF open
   - Email → email_invoice_dialog (to, subject, message, attach PDF)
   - WhatsApp → bulk_whatsapp_dialog ya single WhatsApp message
   - Print → send PDF to printer
   - Delete → soft delete (is_active=FALSE)
8. Export button → openpyxl se Excel file export
```

### 3.4 EDIT INVOICE DIALOG (edit_invoice_dialog.py)

```
UI STRUCTURE:
┌──────────────────────────────────────────────────────┐
│ ✏️ Edit Invoice - INV1001            [❌Cancel][💾Save]│
├──────────────────────────────────────────────────────┤
│ ┌─ Tab 1: Customer & AC Details ────────────────┐   │
│ │ Customer Name: [________] Mobile: [________]  │   │
│ │ Address: [_____________________________]       │   │
│ │ AC Brand: [▼] Type: [▼] Ton: [▼]             │   │
│ │ Star: [▼] Inverter: [▼]                       │   │
│ └──────────────────────────────────────────────┘   │
│ ┌─ Tab 2: Items ──────────────────────────────┐   │
│ │ [Same as New Invoice items table]            │   │
│ │ [➕ Add Row]  [🗑️ Delete Selected]            │   │
│ └──────────────────────────────────────────────┘   │
│ ┌─ Tab 3: Payment & Summary ──────────────────┐   │
│ │ Subtotal: ₹4,000   GST: ₹720   Total:₹4,720│   │
│ │ Advance: [₹2,000]  Balance: ₹2,720           │   │
│ │ Payment Mode: [▼ Cash]  Status:[▼ Paid]     │   │
│ └──────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘

EDIT INVOICE KAISE KAAM KARTA HAI:
1. Dialog constructor mein invoice_data pass hota hai
2. Tabs ke andar sab fields existing values se pre-fill hote hain
3. User jo change karna chahe edit karta hai
4. Save click:
   a. Sab fields read karo
   b. Validation karo (validators.py)
   c. InvoiceController.update_invoice(id, updated_data) call
   d. Database mein UPDATE query chalti hai
   e. Success message dikhta hai
   f. Dialog close hota hai, list refresh hoti hai
```

### 3.5 CUSTOMER MANAGEMENT (customer_view.py)

```
UI STRUCTURE:
┌──────────────────────────────────────────────────────┐
│ 👥 Customers                    [➕ Add] [🗑️ Delete] │
├──────────────────────────────────────────────────────┤
│ Search: [🔍________________]                        │
├───────────────────────┬──────────────────────────────┤
│ ┌─── Customer Table ──┤ ┌─── Right Pane Tabs ───┐   │
│ │ Name  │Mobile│City │ │ [Details] [Invoices]    │   │
│ ├───────┼──────┼─────┤ │                         │   │
│ │ Ram   │98XXX │Delhi│ │ Name: Ram Sharma        │   │
│ │ Shyam │97XXX │Noida│ │ Mobile: 98XXXXXXXX      │   │
│ │ Mohan │96XXX │Gurga│ │ Email: ram@email.com    │   │
│ │ ...   │      │     │ │ Address: 123, Street     │   │
│ │       │      │     │ │ City: Delhi, Pincode: XX│   │
│ │       │      │     │ │ GSTIN: XXAAAAX...       │   │
│ │       │      │     │ │ Total Inv: 12  ₹45,000  │   │
│ │       │      │     │ │ Paid: ₹40K  Bal: ₹5K    │   │
│ │       │      │     │ │ [✏️ Edit] [📒 Ledger]    │   │
│ └───────┴──────┴─────┘ │                         │   │
│                         │ [Invoices Tab me:]       │   │
│                         │ Inv#│Date│Amt│Status     │   │
│                         ├─────┼────┼───┼──────────┤   │
│                         │1001 │1May│4.7│✅Paid    │   │
│                         │1002 │5May│2.5│⏳Pending │   │
│                         └─────────────────────────┘   │
└──────────────────────────────────────────────────────┘

CUSTOMER VIEW KAISE KAAM KARTA HAI:
1. Left pane: QTableWidget mein customers ki list
   - Columns: Name, Mobile, City, Total Invoices, Total Billed, Balance
   - Data: customer_controller.get_all_customers(search_term) se aata hai
   - get_all_customers() SQL subqueries use karta hai:
     SELECT c.*, 
       (SELECT COUNT(*) FROM invoices WHERE customer_id=c.id) as invoices_count,
       (SELECT COALESCE(SUM(total_amount),0) FROM invoices WHERE customer_id=c.id) as total_billed,
       (SELECT COALESCE(SUM(total_amount),0) - COALESCE(SUM(advance_payment),0) FROM invoices WHERE customer_id=c.id) as balance
     FROM customers c WHERE c.is_active=TRUE
   - Search term → WHERE name LIKE '%term%' OR mobile LIKE '%term%'

2. Right pane: QTabWidget with 2 tabs
   - "Details" tab: Customer ki saari info editable form mein
     * "Edit" button → customer_controller.update_customer(id, data)
     * "Ledger" button → CustomerLedgerDialog open (full account statement)
     * "Delete" → soft delete (is_active=FALSE, deleted_at=NOW())
   - "Invoices" tab: Is customer ke saare invoices ki table
     * customer_controller.get_customer_by_id(id) → subquery se stats laata hai
     * Total invoices count, total billed, paid, pending balance

3. Search bar: User type karta hai → 300ms debounce → DB search → table refresh

4. Add Customer button → dialog open → name, mobile, address, etc → save → table refresh
```

### 3.6 TECHNICIAN MANAGEMENT (technician_view.py)

```
UI STRUCTURE:
┌──────────────────────────────────────────────────────┐
│ 🔧 Technicians                  [➕ Add] [🗑️ Delete] │
├───────────────────────┬──────────────────────────────┤
│ ┌── Technician Table ─┤ ┌── Right Pane Tabs ──────┐  │
│ │ Name  │Mobile│Spec  │ │ [Details] [Work][Cust.] │  │
│ ├───────┼──────┼─────┤ │                          │  │
│ │ Raju  │98XXX │Split│ │ Name: Raju Verma         │  │
│ │ Sohan │97XXX │Window│ │ Mobile: 98XXXXXXXX       │  │
│ │ Amit  │96XXX │Both  │ │ Specialisation: Split AC │  │
│ │       │      │     │ │ Commission: 10% Per Job  │  │
│ │       │      │     │ │ Total Jobs: 45            │  │
│ │       │      │     │ │ Commission Earned: ₹4,500 │  │
│ │       │      │     │ │ [✏️ Edit] [🗑️ Delete]     │  │
│ └───────┴──────┴─────┘ │                          │  │
│                         └──────────────────────────┘  │
└──────────────────────────────────────────────────────┘

TECHNICIAN VIEW KAISE KAAM KARTA HAI:
1. technician_controller.get_all_technicians() → DB se sab technicians fetch
2. Left table: name, mobile, specialisation, commission details
3. Right pane tabs:
   - Details: editable form (name, mobile, email, address, specialisation, commission type/rate)
   - Work: is technician ke saare assigned jobs ki list
   - Customers: jin customers ke paas yeh technician gaya
4. Add: dialog → fields → INSERT into technicians table
5. Edit: update_technician(id, data) → UPDATE query
6. Delete: soft delete (is_active=FALSE)
```

### 3.7 SETTINGS (settings_view.py)

```
UI STRUCTURE:
┌──────────────────────────────────────────────────────┐
│ ⚙️ Settings                                           │
├──────────────────────────────────────────────────────┤
│ ┌─ [Profile] [Shop Details] [Master Data] ────────┐  │
│ │                                                   │  │
│ │ TAB 1 - PROFILE:                                  │  │
│ │ Username: admin (read-only)                       │  │
│ │ Full Name: [___________]                          │  │
│ │ Email: [___________]                              │  │
│ │ Phone: [___________]                              │  │
│ │ Role: Admin (read-only)                           │  │
│ │ [💾 Save Profile]                                 │  │
│ │ ─── CHANGE PASSWORD ───                           │  │
│ │ Current Password: [__________]                    │  │
│ │ New Password: [__________]  [STRENGTH: ████░░]    │  │
│ │ Confirm Password: [__________]                    │  │
│ │ [🔑 Change Password]                              │  │
│ │                                                   │  │
│ │ TAB 2 - SHOP DETAILS:                             │  │
│ │ Shop Name: [Ansh Air Cool______________]          │  │
│ │ Owner Name: [________________________]            │  │
│ │ Address: [_____________________________]          │  │
│ │ City: [___] State: [___] Pincode: [______]        │  │
│ │ Phone: [___________] Email: [___________]         │  │
│ │ GSTIN: [________________]                         │  │
│ │ Logo: [📁 Browse...]  [current: logo.png]         │  │
│ │ [💾 Save Shop Details]                            │  │
│ │                                                   │  │
│ │ TAB 3 - MASTER DATA:                              │  │
│ │ [Services] [Parts] [AC Brands] [Technicians]      │  │
│ │ ── Services sub-tab:                              │  │
│ │ ┌───┬──────────┬──────┬─────────┬─────────┐      │  │
│ │ │ # │ Name     │ Rate │ GST App │ Actions │      │  │
│ │ ├───┼──────────┼──────┼─────────┼─────────┤      │  │
│ │ │ 1 │ Gas Fill │ ₹500 │ ✅ Yes  │ [✏️][🗑️] │      │  │
│ │ │ 2 │ AC Serv. │ ₹800 │ ✅ Yes  │ [✏️][🗑️] │      │  │
│ │ └───┴──────────┴──────┴─────────┴─────────┘      │  │
│ │ [➕ Add Service]                                   │  │
│ └──────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘

SETTINGS KAISE KAAM KARTA HAI:
1. Tab 1 - Profile:
   a. User details dikhte hain (session se fetch)
   b. "Save Profile" → session_manager.refresh_session() aur DB update
   c. Change Password:
      - Current password verify (bcrypt check)
      - New password strength check
      - Confirm match check
      - All pass → auth_controller.change_password() → UPDATE users SET password_hash
      - Audit log: PASSWORD_CHANGE

2. Tab 2 - Shop Details:
   a. shop_details table se data fetch (setting_controller.get_shop_details())
   b. Edit karo → Save → UPDATE shop_details SET ... WHERE id=1
   c. EventBus.shop_details_updated.emit() → doosre views ko pata chale
   d. Invoice PDF mein yeh details use hoti hain

3. Tab 3 - Master Data:
   a. Services: service_name, description, default_rate, gst_applicable
      - Add → INSERT INTO services
      - Edit → UPDATE services
      - Delete → soft delete
      - Invoice items dropdown mein yeh services dikhti hain
   b. Parts: part_name, default_rate, description, stock_quantity, stock_alert_level
      - Inventory management ke liye use hota hai
   c. AC Brands: brand_name, ac_type, ton_capacity, star_rating, inverter_type
      - Invoice AC details dropdown mein dikhta hai
   d. Changes → EventBus.master_data_updated.emit(data_type) → all views refresh
```

### 3.8 AMC CONTRACTS (amc_view.py)

```
UI STRUCTURE:
┌──────────────────────────────────────────────────────┐
│ 📅 AMC Contracts                                     │
├──────────────────────────────────────────────────────┤
│ ┌─ [New AMC] [AMC List] [Visit Schedule] ─────────┐  │
│ │                                                   │  │
│ │ TAB 1 - NEW AMC CONTRACT:                         │  │
│ │ Customer: [▼ Select Customer]  [or 🔍 Search]    │  │
│ │ Contract Type: [▼ Gold/Silver/Basic]              │  │
│ │ Start Date: [📅__/__/____]  End: [📅__/__/____]  │  │
│ │ Contract Amount: [₹___________]                   │  │
│ │                                                   │  │
│ │ ── AC UNITS (Add at least 1) ──                   │  │
│ │ ┌───┬──────┬──────┬─────┬──────────┬────────┐    │  │
│ │ │ # │ Brand│ Type │ Ton │ Serial # │ Actions│    │  │
│ │ ├───┼──────┼──────┼─────┼──────────┼────────┤    │  │
│ │ │ 1 │ LG   │Split │ 1.5 │ ABC123   │ [🗑️]   │    │  │
│ │ └───┴──────┴──────┴─────┴──────────┴────────┘    │  │
│ │ [➕ Add Unit]                                       │  │
│ │                                                   │  │
│ │ ── VISIT SCHEDULE (Auto-generated) ──              │  │
│ │ Quarterly visits suggested:                        │  │
│ │ ✅ 20-Aug-2026  ✅ 20-Nov-2026  ❓ 20-Feb-2027    │  │
│ │                                                   │  │
│ │ [💾 Save AMC Contract]                             │  │
│ │                                                   │  │
│ │ TAB 2 - AMC LIST:                                  │  │
│ │ Search: [______]  Status: [▼ All/Active/Expired]   │  │
│ │ ┌───┬────────┬──────┬─────────┬───────┬────────┐  │  │
│ │ │ # │ Cust.  │ Type │ Amount  │ Status│ Actions│  │  │
│ │ ├───┼────────┼──────┼─────────┼───────┼────────┤  │  │
│ │ │ 1 │ Ram    │ Gold │ ₹5,000  │ ✅Act.│ [👁️]   │  │
│ │ │ 2 │ Shyam  │ Basic│ ₹2,000  │ ⏳Exp.│ [Renew]│  │  │
│ │ └───┴────────┴──────┴─────────┴───────┴────────┘  │  │
│ │                                                   │  │
│ │ TAB 3 - VISIT SCHEDULE:                            │  │
│ │ ┌───┬────────┬──────────┬──────────┬────────┬───┐ │  │
│ │ │ # │ Cust.  │ Date     │ Techn.   │ Status │...│ │  │
│ │ ├───┼────────┼──────────┼──────────┼────────┼───┤ │  │
│ │ │ 1 │ Ram    │ 20-Aug   │ Raju     │Scheduled│   │ │  │
│ │ │ 2 │ Ram    │ 20-Nov   │ —        │Pending  │   │ │  │
│ │ └───┴────────┴──────────┴──────────┴────────┴───┘ │  │
│ │ Double-click → Mark Completed                      │  │
│ └──────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘

AMC KAISE KAAM KARTA HAI:
1. Tab 1 - New AMC:
   a. Customer select (dropdown ya search)
   b. Contract type, dates, amount set karo
   c. "Add Unit" button → ek nayi AC unit row add hoti hai (brand, type, ton, serial)
   d. Multiple units add kar sakte hain (e.g., ghar mein 3 AC)
   e. Visit schedule auto-generate (contract period ke hisaab se quarterly)
   f. "Save" → INSERT INTO amc_contracts + amc_units + amc_visits (3 tables)
   g. Audit log: CREATE with entity_type='AMC'

2. Tab 2 - AMC List:
   a. Saare contracts dikhte hain with status
   b. Search by customer name, filter by status
   c. Actions: View details, Edit, Renew (extend date), Mark Expired

3. Tab 3 - Visit Schedule:
   a. Saari scheduled visits dikhti hain
   b. Double-click → status change kar sakte hain (Scheduled → Completed)
   c. Technician assign kar sakte hain
   d. Notes add kar sakte hain
```

### 3.9 DAILY LOGS (daily_log_view.py)

```
UI STRUCTURE:
┌──────────────────────────────────────────────────────┐
│ 📝 Daily Logs                       [➕ Add Entry]   │
├───────────────────────┬──────────────────────────────┤
│ ┌── Log Table ────────┤ ┌── Summary Pane ─────────┐  │
│ │ Date  │Cust│Tech│   │ │ 📊 Summary for Period   │  │
│ │       │    │    │   │ │                          │  │
│ │20-May │Ram │Raju│   │ │ Petrol Expense: ₹1,200  │  │
│ │19-May │Shym│Soh │   │ │ Parts Cost:    ₹3,500  │  │
│ │18-May │Mhn │Amt │   │ │ ────────────────────── │  │
│ │       │    │    │   │ │ Total Expense: ₹4,700  │  │
│ │       │    │    │   │ │ Total Profit:  ₹8,300  │  │
│ │       │    │    │   │ │ ────────────────────── │  │
│ │       │    │    │   │ │ Net Earnings: ₹3,600   │  │
│ │       │    │    │   │ │                          │  │
│ │       │    │    │   │ │ Log Entries: 12          │  │
│ └───────┴────┴────┴───┘ └──────────────────────────┘  │
└──────────────────────────────────────────────────────┘

DAILY LOG KAISE KAAM KARTA HAI:
1. Log table: daily_logs table se data fetch (date DESC, LIMIT 100)
2. Har entry mein: date, customer, technician, service_type, petrol_expense, parts_cost, total_expense, profit
3. Add Entry dialog:
   a. Date (default: today), Customer (search/select), Technician (select)
   b. Service Type description
   c. Petrol Expense (₹ amount), Parts Cost (₹ amount)
   d. Total Expense = Petrol + Parts (auto-calculate)
   e. Profit = Service Charge - Total Expense (user enter ya auto)
   f. Save → INSERT INTO daily_logs
4. Summary pane: current filter period ke hisaab se totals dikhata hai
   - Petrol, Parts, Total Expense, Total Profit, Count
   - SQL: SUM(petrol_expense), SUM(parts_cost), SUM(total_expense), SUM(profit)
5. Date filter: From/To select → log table + summary refresh
6. Edit/Delete: per entry available
```

### 3.10 ONLINE REQUESTS (online_request_view.py)

```
UI STRUCTURE:
┌──────────────────────────────────────────────────────┐
│ 🌐 Online Requests              [🔄 Auto-refresh:30s] │
│ 🔴 Pending: 5                                        │
├──────────────────────────────────────────────────────┤
│ Search: [______________]  Status: [▼ All]            │
├──────────────────────────────────────────────────────┤
│ ┌──┬──────┬────────┬───────┬────────┬──────┬──────┐  │
│ │ #│ Date │ Name   │ Phone │ Service│Status│ Act. │  │
│ ├──┼──────┼────────┼───────┼────────┼──────┼──────┤  │
│ │ 1│20May │ Rahul  │98XXX  │ Repair │🔴 Un.│ [✓]  │  │
│ │ 2│19May │ Priya  │97XXX  │ AMC    │🟡Con.│ [✓]  │  │
│ │ 3│18May │ Ankit  │96XXX  │ Inst.  │✅ Cv.│ [✓]  │  │
│ │ 4│17May │ Neha   │95XXX  │ Repair │❌ Rej.│ [✓]  │  │
│ └──┴──────┴────────┴───────┴────────┴──────┴──────┘  │
│                                                        │
│ Toast (when new request arrives):                      │
│ ┌──────────────────────────────────────────────────┐  │
│ │ New Request: Rahul - AC Service 📞 98XXXXXXXX    │  │
│ │ [Close] (auto-dismiss 5s)                        │  │
│ └──────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘

ONLINE REQUEST KAISE KAAM KARTA HAI:
1. Website (external) se service requests contact_messages table mein aate hain
2. Desktop software har 30 second mein auto-refresh karta hai:
   a. QTimer(30000) — har 30s par _refresh_data() call
   b. online_request_controller.get_all_contact_messages() fetch
   c. Table update hoti hai with latest data
   d. Pending count badge update hota hai
3. New request detection:
   a. Previous data se current data compare
   b. Naya request mila → toast notification show (5 second auto-dismiss)
   c. Sound alert bajta hai (QApplication.beep() ya custom sound)
4. Status management:
   - unread → user ne abhi tak nahi dekha
   - read → user ne dekha
   - Contacted → user ne customer se baat ki
   - Converted → request se customer/invoice bana
   - Rejected → request reject
   - Status change → online_request_controller.update_message_status(id, status)
5. Double-click → full detail dialog: name, phone, email, message, preferred date, time slot, address
6. Delete → soft delete (is_active=FALSE)
7. Statistics footer: Total, Pending, Contacted, Converted, Rejected counts
```

### 3.12 INVENTORY (inventory_view.py)

```
UI STRUCTURE:
┌──────────────────────────────────────────────────────┐
│ 📦 Inventory                        [➕ Add Part]    │
├──────────────────────────────────────────────────────┤
│ Search: [________________]                           │
├──────────────────────────────────────────────────────┤
│ ┌──┬──────────┬───────┬──────┬──────┬────────┬────┐ │
│ │ #│ Part     │ Rate  │Stock │Alert │ Status │Act.│ │
│ │  │ Name     │       │ Qty  │Level │        │    │ │
│ ├──┼──────────┼───────┼──────┼──────┼────────┼────┤ │
│ │ 1│Compressor│₹3,500 │  5   │  3   │ ✅ Ok  │[✏️]│ │
│ │ 2│Gas Cyl.  │₹1,200 │  1   │  5   │ 🔴 LOW │[✏️]│ │
│ │ 3│Fan Motor │₹1,800 │  8   │  2   │ ✅ Ok  │[✏️]│ │
│ └──┴──────────┴───────┴──────┴──────┴────────┴────┘ │
│ Summary: Total: 20 Parts | Low Stock: 3 | Qty: 145  │
└──────────────────────────────────────────────────────┘

INVENTORY KAISE KAAM KARTA HAI:
1. parts table se data fetch (is_active=TRUE)
2. Agar stock_quantity <= stock_alert_level → row red highlight (LOW STOCK)
3. Search by part name
4. Add Part: name, rate, description, stock qty, alert level → INSERT
5. Edit: UPDATE parts
6. Adjust Stock dialog:
   a. Current stock dikhta hai
   b. Quantity change (+ ya -) enter karo
   c. Reason (e.g., "New Purchase", "Used in Service")
   d. inventory_controller.adjust_stock(id, qty_change, reason) call
   e. UPDATE parts SET stock_quantity
   f. INSERT INTO stock_movements (history)
7. Stock Movements: har part ka full history dekha ja sakta hai
8. Summary: total parts count, low stock count, total quantity
```

### 3.13 REPORTS (report_view.py)

```
UI STRUCTURE:
┌──────────────────────────────────────────────────────┐
│ 📈 Reports                                            │
├──────────────────────────────────────────────────────┤
│ ┌─ [Profit & Loss] [GST Report] ──────────────────┐  │
│ │                                                   │  │
│ │ TAB 1 - PROFIT & LOSS:                            │  │
│ │ Year: [▼ 2026]                                    │  │
│ │ ┌──────┬──────────┬─────────┬────────┬────────┐  │  │
│ │ │Month │ Revenue  │ Expense │ Profit │ Margin │  │  │
│ │ ├──────┼──────────┼─────────┼────────┼────────┤  │  │
│ │ │ Jan  │ ₹45,000  │ ₹12,000 │ ₹33,000│  73%   │  │  │
│ │ │ Feb  │ ₹38,000  │ ₹10,500 │ ₹27,500│  72%   │  │  │
│ │ │ ...  │          │         │        │        │  │  │
│ │ │ Dec  │ ₹52,000  │ ₹15,000 │ ₹37,000│  71%   │  │  │
│ │ ├──────┼──────────┼─────────┼────────┼────────┤  │  │
│ │ │Total │₹5,80,000 │₹1,50,000│₹4,30,00│  74%   │  │  │
│ │ └──────┴──────────┴─────────┴────────┴────────┘  │  │
│ │                                                   │  │
│ │ Charts: Revenue vs Expense (Bar) + Profit (Line)   │  │
│ │                                                   │  │
│ │ TAB 2 - GST REPORT:                                │  │
│ │ Month: [▼ May]  Year: [▼ 2026]                    │  │
│ │ ┌──┬────────┬──────────┬──────┬──────┬───────┐   │  │
│ │ │ #│ Invoice│ Customer │ Tax. │ GST% │ GST ₹ │   │  │
│ │ ├──┼────────┼──────────┼──────┼──────┼───────┤   │  │
│ │ │ 1│ 1001   │ Ram      │ ₹4K  │ 18%  │ ₹720  │   │  │
│ │ │ 2│ 1002   │ Shyam    │ ₹2K  │ 18%  │ ₹360  │   │  │
│ │ └──┴────────┴──────────┴──────┴──────┴───────┘   │  │
│ │ Total Taxable: ₹6,000  |  Total GST: ₹1,080       │  │
│ │ [📄 Export to PDF]                                 │  │
│ └──────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘

REPORTS KAISE KAAM KARTA HAI:
1. Tab 1 - Profit & Loss:
   a. Year select karo (default: current year)
   b. _load_pnl() → report_controller.get_monthly_profit_loss(year)
   c. SQL queries:
      - Revenue: SELECT MONTH(invoice_date), SUM(total_amount) FROM invoices WHERE YEAR(invoice_date)=year AND is_active=TRUE GROUP BY MONTH
      - Expense: SELECT MONTH(log_date), SUM(total_expense) FROM daily_logs WHERE YEAR(log_date)=year AND is_active=TRUE GROUP BY MONTH
   d. 12 months ka data table mein dikhta hai
   e. Profit = Revenue - Expense (per month)
   f. Bar chart: revenue vs expense
   g. Line chart: profit trend
   h. Total row at bottom: sum of all months

2. Tab 2 - GST Report:
   a. Month + Year select karo
   b. _load_gst() → report_controller.get_gst_report(month, year)
   c. Invoices ka data with GST breakdown
   d. Total taxable amount, total GST collected
   e. "Export to PDF" → ReportLab se GST report PDF generate
```

### 3.14 DIALOGS

#### A. REMINDER DIALOG (reminder_dialog.py)

```
🔔 REMINDERS & ALERTS (Modal, 800×500)
├── Tab 1: Pending Payments
│   ┌───┬──────────┬─────────┬─────────┬──────────┬──────┐
│   │ # │ Customer │ Invoice │ Balance │   Date   │Action│
│   ├───┼──────────┼─────────┼─────────┼──────────┼──────┤
│   │ 1 │ Ram      │ INV1002 │ ₹2,500  │ 19-05-26 │📱Send│
│   │ 2 │ Shyam    │ INV1005 │ ₹1,200  │ 15-05-26 │📱Send│
│   └───┴──────────┴─────────┴─────────┴──────────┴──────┘
├── Tab 2: AMC Expiry
│   ┌───┬──────────┬──────┬─────────┬──────────┬──────┐
│   │ # │ Customer │ Type │ Amount  │ End Date │Action│
│   ├───┼──────────┼──────┼─────────┼──────────┼──────┤
│   │ 1 │ Mohan    │ Gold │ ₹5,000  │ 25-05-26 │📱Send│
│   └───┴──────────┴──────┴─────────┴──────────┴──────┘

KAISE KAAM KARTA HAI:
- SMSReminder class se data fetch
- Pending Payments: invoices where balance > 0 AND date > 7 days old
- AMC Expiry: contracts expiring within next 7 days
- "Send" → WhatsApp link open with pre-generated message (Hindi mein)
```

#### B. CUSTOMER LEDGER (customer_ledger_dialog.py)

```
📒 CUSTOMER LEDGER - Ram Sharma (Modal, 800×500)
├── Summary Cards:
│   [Total Billed: ₹45,000] [Total Paid: ₹40,000]
│   [Balance: ₹5,000] [Invoices: 12]
├── Date Filter: From [📅] to [📅] [🔍 Show]
├── ┌──┬──────────┬──────────────┬───────┬───────┬────────┐
│    │ #│   Date   │  Description │ Debit │ Credit│ Balance│
│    ├──┼──────────┼──────────────┼───────┼───────┼────────┤
│    │ 1│01-01-26  │ INV1001      │ ₹4,720│   —   │ ₹4,720 │
│    │ 2│05-01-26  │ Payment Cash │   —   │₹4,720 │   ₹0   │
│    │ 3│15-03-26  │ INV1020      │ ₹6,000│   —   │ ₹6,000 │
│    └──┴──────────┴──────────────┴───────┴───────┴────────┘

KAISE KAAM KARTA HAI:
- Customer ID ke hisaab se saare invoices + payments fetch
- Debit = invoice amount, Credit = payment amount
- Balance running calculate (har transaction ke baad)
- Date filter ke saath
```

#### C. EMAIL INVOICE (email_invoice_dialog.py)

```
📧 EMAIL INVOICE (Modal, 500px wide)
├── To: [ram@email.com________________________]
├── Subject: [Invoice INV1001 from Ansh Air Cool]
├── Message:
│   Dear Ram,
│   Please find attached invoice INV1001.
│   Total: ₹4,720
│   Thank you for your business!
├── PDF: 📎 Invoice_INV1001.pdf [Browse] [Generate]
├── [❌ Cancel] [📤 Send Email]

KAISE KAAM KARTA HAI:
- SMTP config se email send (config ya env se settings)
- PDF generate ya existing PDF attach
- "Send Email" → smtplib se email bhej
- Success/failure message dikhata hai
```

#### D. BULK WHATSAPP (bulk_whatsapp_dialog.py)

```
📱 BULK WHATSAPP / SMS (Modal, 700×550)
├── Template: [▼ Pending Payment Reminder]
├── Message Preview:
│   Namaste {name}!
│   Aapke invoice #{inv} ka ₹{balance}
│   balance pending hai.
│   Kripya jald se jald payment karein.
│   Ansh Air Cool 📞 90000 00000
├── ☑ Select All | [3 customers selected]
├── ┌──┬──────────┬──────────┬─────────┬─────────┐
│    │ ☐│ Customer │  Phone   │  Pending│  Action │
│    ├──┼──────────┼──────────┼─────────┼─────────┤
│    │ ☑│ Ram      │ 98XXXXXX │ ₹2,500  │ 📱 Send │
│    │ ☐│ Shyam    │ 97XXXXXX │ ₹1,200  │ 📱 Send │
│    └──┴──────────┴──────────┴─────────┴─────────┘
├── [❌ Cancel] [📤 Send to Selected]

KAISE KAAM KARTA HAI:
- Templates: Custom, Pending Payment, AMC Expiry, Service Follow-up, Festival Greeting
- {name}, {mobile}, {inv}, {balance} → actual values se replace hote hain
- Select customers → "Send" → har customer ke liye WhatsApp URL open
- WhatsApp URL: https://wa.me/91{mobile}?text={message}
- {message} URL-encode ho kar URL mein add hota hai
```

#### E. EDIT INVOICE DIALOG (edit_invoice_dialog.py)

```
Already covered in section 3.4 above.
Full 3-tab dialog with customer, items, payment editing.
```

---

## 4. DATABASE KAISE KAAM KARTA HAI

### 4.1 Connection Flow

```
Koi bhi view/controller DB se data lena chahta hai:
1. DatabaseConnection() — singleton instance lete hain (ek hi instance, baar baar new nahi)
2. execute_query(sql, params, fetch_one/fetch_all) call karte hain
3. execute_query() kya karta hai:
   a. self._lock.acquire() — thread safety ke liye lock
   b. ensure_connection() — check karta hai connection alive hai ya nahi
   c. Agar connection dead → reconnect karta hai
   d. cursor = self._conn.cursor(dictionary=True) — DictCursor
   e. cursor.execute(sql, params) — parameterized query (SQL injection safe)
   f. Agar fetch_one → cursor.fetchone()
   g. Agar fetch_all → cursor.fetchall()
   h. cursor.close()
   i. Lock release
   j. Log query with duration (logger mein)
   k. Return result
4. Agar OperationalError (connection lost) → ensure_connection() reconnect karega aur retry
5. Agar koi aur error → exception raise hota hai → caller catch karta hai

DatabaseContext:
   with DatabaseContext() as db:
       db.execute_query(...)
   → Context manager, exception pe auto-rollback, success pe auto-commit
```

### 4.2 Soft Delete Pattern

```
Saare tables mein:
- is_active BOOLEAN DEFAULT TRUE
- deleted_at TIMESTAMP NULL
- deleted_by INT NULL (user_id)

"Delete" ka matlab:
  UPDATE table SET is_active=FALSE, deleted_at=NOW() WHERE id=X

"Restore" ka matlab:
  UPDATE table SET is_active=TRUE, deleted_at=NULL WHERE id=X

Har query mein condition:
  WHERE is_active = TRUE
```

### 4.3 Invoice Number Auto-Generation

```
INVOICE_PREFIX = "INV"  (config.py)
INVOICE_START_NUMBER = 1001

get_next_invoice_number():
  SELECT COALESCE(MAX(id), 0) + 1 FROM invoices
  → naya number = 1000 + last_id (ya start_number)
  invoice_number = f"{INVOICE_PREFIX}{naya_number}"
```

---

## 5. UTILITY FUNCTIONS KAISE KAAM KARTI HAIN

### 5.1 PDF Generator (pdf_generator.py)

```
PDF INVOICE STRUCTURE:
┌──────────────────────────────────────────────────┐
│  [LOGO]      Ansh Air Cool                       │
│              Shop Address, City                   │
│              Phone: 98XXXXXXXX  GST: XXAAAAX     │
├──────────────────────────────────────────────────┤
│  INVOICE                                         │
│  Inv #: INV1001           Date: 20-05-2026       │
├──────────────────────────────────────────────────┤
│  Bill To:                                        │
│  Ram Sharma                                      │
│  123, Street, Delhi - 110001                     │
│  Mobile: 98XXXXXXXX                              │
├──────────────────────────────────────────────────┤
│  AC Details:                                     │
│  Brand: LG | Type: Split | Ton: 1.5             │
│  Star: 3 | Inverter: Yes                        │
├──────────────────────────────────────────────────┤
│  Technician: Raju Verma                          │
├──────────────────────────────────────────────────┤
│  ┌──────────┬─────────┬─────┬──────┬─────────┐  │
│  │ Item     │   Rate  │ Qty │ Amt  │  GST    │  │
│  ├──────────┼─────────┼─────┼──────┼─────────┤  │
│  │Gas Fill  │   500   │  1  │ 500  │  90     │  │
│  │Compressor│  3500   │  1  │ 3500 │  630    │  │
│  ├──────────┼─────────┼─────┼──────┼─────────┤  │
│  │          │         │     │4000  │  720    │  │
│  ├──────────┴─────────┴─────┴──────┼─────────┤  │
│  │  TOTAL (incl GST)              │ 4,720   │  │
│  │  Advance Paid                  │ 2,000   │  │
│  │  Balance Due                   │ 2,720   │  │
│  ├──────────────────────────────────────────┤  │
│  │  Payment: Pending                         │  │
│  │  Payment Mode: Cash                       │  │
├──────────────────────────────────────────────────┤
│  Terms & Conditions:                             │
│  1. Payment due within 30 days                  │
│  2. Service warranty 90 days                    │
│  3. Parts warranty as per manufacturer          │
├──────────────────────────────────────────────────┤
│               Authorised Signature               │
│               Ansh Air Cool                     │
└──────────────────────────────────────────────────┘

Colors: Dark Blue Header (#1F4E79), Light Blue BG (#E3F2FD), Yellow Total (#FFC000)
Fonts: Helvetica (clean professional)
Page: A4, landscape ya portrait
```

### 5.2 Theme Manager (unified_theme.py)

```
Kya karta hai:
1. get_colors() → current color dict return (dark theme ke colors)
2. apply_palette(widget) → QPalette apply karta hai:
   - Window → #0f172a (bg)
   - WindowText → #f1f5f9 (fg)
   - Base → #1e293b (card_bg)
   - Button → #334155 (border/hover)
   - Highlight → #22d3ee (primary)
   - etc.
3. get_main_stylesheet() → poora CSS-style string return karta hai jo saare Qt widgets ko style karta hai
   - QPushButton, QLineEdit, QTableWidget, QTabWidget, QComboBox, QSpinBox, QScrollBar, etc.
4. apply_table_theme(table) → alternate row colors + header style table par apply

Theme fixed hai (dark mode hi hai, light mode nahi hai)
```

### 5.3 Validators (validators.py)

```
Har input field ka validation kaise hota hai:

validate_name("Ram Sharma") → True
validate_name("") → False, "Name is required"
validate_name("a") → False, "Name must be at least 2 characters"

validate_mobile("9876543210") → True
validate_mobile("1234567890") → False, "Invalid Indian mobile number" (1 se start)
validate_mobile("98765") → False, "10 digits required"

validate_email("ram@email.com") → True
validate_email("invalid") → False, "Invalid email address"
validate_email("") → True, "" (email optional hai)

validate_amount("500") → True
validate_amount("-100") → False, "Amount cannot be negative"
validate_amount("999999999") → False, "Amount is too large"

validate_gst("27AABCD1234D1ZX") → True (15 chars Indian GST format)
validate_gst("invalid") → False
```

### 5.4 Formatters (formatters.py)

```
format_currency(1234567.89) → "₹12,34,567.89" (Indian style: lakh/crore)
format_currency(50000000) → "₹5.00Cr"
format_currency(123456) → "₹1,23,456.00"

format_date("2026-05-20") → "20-05-2026"
format_date("2026-05-20", "%Y-%m-%d") → "2026-05-20"

format_datetime("2026-05-20T14:30:00") → "20-05-2026 02:30 PM"

format_mobile("9876543210") → "+91 98765 43210"
```

### 5.5 Session Manager (session_manager.py)

```
Session kaise kaam karta hai:
1. get_session() → global SessionManager instance return
2. SessionManager singleton hai (poore app mein ek hi instance)
3. login(user_data) call → session start hota hai
   - current_user = user_data
   - login_time = datetime.now()
   - session_id = "session_{id}_{timestamp}"
   - Audit log: LOGIN
4. logout() call → session end hota hai
   - Audit log: LOGOUT
   - current_user = None
5. get_current_user() → logged-in user ka data return (ya None)
6. is_admin() → role check karta hai
7. refresh_session() → profile update ke baad session sync karta hai
8. Thread-safe (threading.Lock())
```

### 5.6 Event Bus (event_bus.py)

```
Pub-Sub system jo views ko communicate karne deta hai bina ek doosre ke baare mein jaane:

Signals:
  settings_updated(dict) → settings save hone par
  master_data_updated(str) → services/parts/brands change par
  shop_details_updated(dict) → shop details edit hone par
  user_profile_updated(dict) → profile update hone par
  invoice_created(dict) → naya invoice banne par
  customer_updated(dict) → customer data change hone par

Kaise use karta hai:
  1. Koi view/controller emit karta hai:
     get_event_bus().emit_invoice_created(invoice_data)
  2. Doosra view connect karta hai:
     get_event_bus().invoice_created.connect(self._on_invoice_created)
  3. Jab emit hoga → _on_invoice_created() automatically call hoga

Debounce: 100ms timer — agar ek saath multiple updates aayein, toh ek hi baar fire hoga
```

### 5.7 Logger (logger.py)

```
Logging kaise kaam karta hai:

setup_logging() → 4 loggers create karta hai:
  1. 'app' → AC_Service_Billing.log (general app logs)
  2. 'security' → AC_Service_Billing_security.log (login/logout/security events)
  3. 'database' → AC_Service_Billing_database.log (SQL queries)
  4. 'error' → AC_Service_Billing_errors.log (sirf errors)

Har logger ke do handlers hote hain:
  - Console handler → colored output (Cyan=DEBUG, Green=INFO, Yellow=WARN, Red=ERROR, Magenta=CRITICAL)
  - File handler → RotatingFileHandler (10MB max, backups rotate)

Log format: "2026-05-20 14:30:00 | INFO     | app | function:42 | message"

Convenience functions:
  log_info("Invoice created")
  log_error("Database connection failed", exc_info=True)
  log_security_event("LOGIN", username="admin")
  log_database_query("SELECT * FROM invoices", duration="0.023s")
```

### 5.8 Audit Trail (audit.py)

```
Saare important operations log hote hain audit_log table mein:

AuditLogger.log(action, entity_type, entity_id, details)

Action types:
  LOGIN, LOGOUT, CREATE, UPDATE, DELETE, RESTORE,
  PAYMENT, EXPORT, PRINT, BACKUP, SETTINGS,
  PASSWORD_CHANGE, USERNAME_CHANGE

Helper functions:
  log_login(user_data) → "User admin logged in"
  log_create("Invoice", 1001, "Created INV1001 for Ram")
  log_update("Customer", 5, "Updated mobile number")
  log_delete("Technician", 3, "Deleted technician Raju")
  log_payment(1001, "₹2000 received via UPI")

get_logs(limit=100, action=None, entity_type=None, user_id=None)
  → audit_log table se filtered logs fetch
```

### 5.9 Chart Widgets (chart_widgets.py)

```
4 chart widgets, sab QPainter se custom draw:

1. BarChartWidget:
   - set_data([{'label':'Jan','value':45000}, {'label':'Feb','value':38000}, ...])
   - paintEvent mein: axis draw, bars draw (width = chart_width/n * 0.6), value labels
   - Min height: 200px
   - Colors: default bar #3498DB, highlight #2ECC71, lowlight #E74C3C

2. PieChartWidget:
   - set_data([{'label':'Cash','value':60}, {'label':'UPI','value':30}, {'label':'Card','value':10}])
   - Donut ya solid pie (configurable)
   - Percentage labels on slices
   - Legend on side

3. HorizontalBarChartWidget:
   - Horizontal bars (good for comparison)
   - set_data() same format

4. LineChartWidget:
   - Line graph for trends
   - Points + lines
```

### 5.10 Shortcut Manager (shortcut_manager.py)

```
Keyboard shortcuts setup:

Default shortcuts (DB se override ho sakte hain):
  Ctrl+N → New Invoice
  Ctrl+F → Search
  F5     → Refresh
  Ctrl+D → Dashboard
  Ctrl+Shift+C → Customers
  Ctrl+, → Settings
  Ctrl+P → Print
  Ctrl+L → Daily Logs
  Ctrl+T → Technicians
  Ctrl+M → Manage Invoices
  Ctrl+K → AMC Contracts

load_shortcuts():
  1. DEFAULT_SHORTCUTS memory mein load
  2. DB se app_settings table mein 'shortcut_%' keys check
  3. Agar DB mein koi shortcut hai → default override
  4. QShortcut(QKeySequence(key), parent, callback) register

save_shortcut(name, key_sequence):
  INSERT/UPDATE INTO app_settings WHERE setting_key = 'shortcut_{name}'
```

### 5.11 SMS/WhatsApp Reminder (sms_reminder.py)

```
Reminder generation:

get_pending_payment_reminders():
  SQL: SELECT invoices WHERE balance>0 AND payment_status IN ('Pending','Partial')
       AND DATEDIFF(NOW(), created_at) >= 7
  LIMIT 20

get_amc_expiry_reminders(days=7):
  SQL: SELECT amc_contracts WHERE status='Active'
       AND end_date BETWEEN TODAY AND TODAY+7
  LIMIT 20

generate_pending_message(reminder):
  Hindi text: "Namaste {name}! Aapke invoice #{inv} ka ₹{balance} balance pending hai. Kripya jald se jald payment karein. Ansh Air Cool"

generate_amc_message(reminder):
  Hindi text: "Namaste {name}! Aapka {type} {end_date} ko expire ho raha hai. Kripya renewal ke liye sampark karein. Ansh Air Cool"
```

---

## 6. ARCHITECTURE DIAGRAM

```
┌─────────────────────────────────────────────────────────────────────┐
│                         main.py                                      │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────────────────┐   │
│  │ Splash   │───→│ LoginWindow  │───→│      MainWindow          │   │
│  │ Screen   │    │ (or bypass)  │    │  ┌────────────────────┐  │   │
│  └──────────┘    └──────────────┘    │  │    Sidebar (13     │  │   │
│                                       │  │    Nav Items)      │  │   │
│                                       │  ├────────────────────┤  │   │
│                                       │  │  QStackedWidget   │  │   │
│                                       │  │  ┌──────────────┐ │  │   │
│                                       │  │  │ Dashboard    │ │  │   │
│                                       │  │  │ Invoice      │ │  │   │
│                                       │  │  │ Customer     │ │  │   │
│                                       │  │  │ Technician   │ │  │   │
│                                       │  │  │ Settings     │ │  │   │
│                                       │  │  │ AMC          │ │  │   │
│                                       │  │  │ Daily Log    │ │  │   │
│                                       │  │  │ Online Req.  │ │  │   │
│                                       │  │  │ Reports      │ │  │   │
│                                       │  │  │ Inventory    │ │  │
│                                       │  │  └──────────────┘ │  │
│                                       │  └────────────────────┘  │   │
│                                       │  Status Bar: User/Time/DB│   │
│                                       └──────────┬───────────────┘   │
└──────────────────────────────────────────────────┼───────────────────┘
                                                   │
            ┌──────────────────────────────────────┼──────────────────────────┐
            │                                      │                          │
       ┌────┴────┐                     ┌───────────┴──────────┐    ┌─────────┴────────┐
       │  Views  │                     │    Controllers       │    │  Event Bus       │
       │  (UI)   │───── calls ────────→│   (Business Logic)   │    │  (Pub-Sub)       │
       └─────────┘                     └───────────┬──────────┘    └─────────┬────────┘
                                                   │                          │
                                                   │ calls                    │ signals
                                                   │                          │
                                            ┌──────┴──────┐                  │
                                            │  Database   │                  │
                                            │   Layer     │                  │
                                            │ ┌─────────┐ │                  │
                                            │ │ db_conn │ │                  │
                                            │ │ models  │ │                  │
                                            │ │ queries │ │                  │
                                            │ └────┬────┘ │                  │
                                            └──────┼──────┘                  │
                                                   │                         │
                                            ┌──────┴──────┐                 │
                                            │   MySQL DB  │◄────────────────┘
                                            │ Desktop_sw  │
                                            └─────────────┘

┌────────────────────────────────────────────────────────────┐
│                    UTILITIES LAYER                          │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌─────────┐ ┌────────┐  │
│  │Theme   │ │PDF Gen │ │Validat.│ │Format.  │ │Session │  │
│  │Manager │ │        │ │        │ │         │ │Manager │  │
│  ├────────┤ ├────────┤ ├────────┤ ├─────────┤ ├────────┤  │
│  │Logger  │ │Charts  │ │Search  │ │Shortcut │ │Audit   │  │
│  │        │ │Widgets │ │Widget  │ │Manager  │ │Trail   │  │
│  ├────────┤ ├────────┤ ├────────┤ ├─────────┤ ├────────┤  │
│  │Event   │ │SMS/    │ │Language│ │Config   │ │Backup  │  │
│  │Bus     │ │WhatsApp│ │(i18n)  │ │(config) │ │        │  │
│  └────────┘ └────────┘ └────────┘ └─────────┘ └────────┘  │
└────────────────────────────────────────────────────────────┘
```

---

## 7. DATA FLOW — HAR FEATURE KA COMPLETE FLOW

### 7.1 Invoice Create Flow

```
User click "Save Invoice"
  ↓
invoice_view.py: _save_invoice()
  ↓  Validate sab fields (validators.py)
  ↓
InvoiceController.create_invoice(data)
  ↓  BEGIN TRANSACTION
  ├─ Step 1: Check customer by mobile → SELECT * FROM customers WHERE mobile=%s
  │          Agar nahi mila → INSERT INTO customers (name, mobile, address, ...)
  │
  ├─ Step 2: Check AC brand → SELECT * FROM ac_brands WHERE brand_name=%s AND type=%s
  │          Agar nahi mila → INSERT INTO ac_brands (brand_name, ac_type, ton_capacity, ...)
  │
  ├─ Step 3: Get technician → SELECT * FROM technicians WHERE id=%s
  │
  ├─ Step 4: Get next invoice number → SELECT COALESCE(MAX(id),0)+1 FROM invoices
  │          Generate: "INV" + (1000 + new_id)
  │          INSERT INTO invoices (invoice_number, customer_id, ac_brand_id, ...)
  │
  ├─ Step 5: For each item → INSERT INTO invoice_items (invoice_id, item_type, item_id, ...)
  │
  ├─ Step 6: For each part item → UPDATE parts SET stock_quantity = stock_quantity - qty
  │
  └─ COMMIT (agar sab successful)
     ↓
  Agar koi bhi step fail → ROLLBACK (sab undo)
  ↓
EventBus.emit_invoice_created(invoice_data) → dashboard ko pata chal gaya
  ↓
PDFGenerator.generate_invoice(invoice_data)
  ↓  ReportLab se A4 PDF create
  ↓  pdfs/INV1001.pdf save
  ↓
"✅ Invoice INV1001 created successfully!" message show
  ↓
Form reset for next invoice
```

### 7.2 Payment Collection Flow

```
User clicks "Collect Payment" on an invoice
  ↓
Invoice Management / Invoice View
  ↓
Payment dialog opens:
  - Invoice #, Customer, Total, Already Paid, Balance Due
  - Input: Amount, Payment Mode (Cash/UPI/Card/NetBanking), Date
  ↓
Save button click
  ↓
INSERT INTO payments (invoice_id, amount, payment_mode, payment_date, ...)
  ↓
UPDATE invoices SET 
  advance_payment = advance_payment + amount,
  balance_amount = total_amount - advance_payment,
  payment_status = CASE 
    WHEN balance_amount <= 0 THEN 'Paid'
    WHEN advance_payment > 0 THEN 'Partial' 
    ELSE 'Pending'
  END
WHERE id = invoice_id
  ↓
AuditLog.log('PAYMENT', 'Invoice', invoice_id, "₹{amount} received via {mode}")
  ↓
EventBus.emit_invoice_created(updated_invoice)
  ↓
"✅ Payment recorded successfully!" message
  ↓
Table refresh
```

### 7.3 AMC Renewal Flow

```
User clicks "Renew" on an expiring AMC contract
  ↓
Dialog: New End Date, New Amount (optional)
  ↓
Save:
  1. UPDATE amc_contracts SET end_date = new_end_date, 
     contract_amount = new_amount (if changed), updated_at=NOW()
  2. Auto-generate new visit schedule for the extended period
     INSERT INTO amc_visits (amc_contract_id, visit_date, ...)
  3. UPDATE amc_contracts SET amc_status = 'Active'
  ↓
Table refresh
```

### 7.4 Online Request Status Change Flow

```
User selects a contact message
  ↓
Dropdown/Button: Change Status
  ↓
UPDATE contact_messages SET status = new_status, updated_at = NOW()
  ↓
Agar status = 'Converted':
  → Customer create karne ka option deta hai (name, phone already hai)
  → Agar create kiya → EventBus.emit_customer_updated()
  → Invoice create karne ka option
  ↓
Table refresh
  ↓
Statistics update (pending count, converted count, etc.)
```

### 7.5 Stock Adjustment Flow

```
User clicks "Adjust Stock" on a part
  ↓
Dialog shows: Current Stock: 5
  Input: Quantity Change (+5 for purchase, -2 for used)
  Reason: "New Purchase from Supplier X" / "Used in Service INV1002"
  ↓
Validate: new quantity >= 0 (stock negative nahi ho sakta)
  ↓
UPDATE parts SET stock_quantity = stock_quantity + change WHERE id = part_id
  ↓
INSERT INTO stock_movements (part_id, quantity_change, new_quantity, reason, created_at)
  ↓
If new quantity <= alert_level → warning dikhata hai "Low Stock!"
  ↓
Table refresh → row highlight update
```

---

## 8. SECURITY

| Feature | Kaise Kaam Karta Hai |
|---|---|
| **Password Hashing** | bcrypt — password ko hash karke store karta hai, plain text kabhi nahi |
| **Account Lockout** | 5 failed attempts → 15 minutes ke liye account lock. failed_login_attempts table mein attempts store |
| **SQL Injection Protection** | Saare queries parameterized hain (`%s` placeholders), user input kabhi direct SQL mein nahi jaata |
| **Soft Delete** | Koi bhi data permanently delete nahi hota, sirf `is_active=FALSE` hota hai |
| **Audit Trail** | Har important action log hota hai — kaun, kya, kab, kis entity par |
| **Input Validation** | User input kabhi bina validate kiye DB mein nahi jaata (validators.py) |
| **Env Validation** | DB_PASSWORD missing hai toh app start hi nahi hota |
| **Session Tracking** | Session ID, login time, user info — poora track rakhta hai |

---

## 9. PERFORMANCE

| Optimization | Explanation |
|---|---|
| **Single Dashboard Query** | 7 stats ek hi SQL query mein — 7 alag queries nahi |
| **Connection Pooling** | pool_size=5 — har baar naya connection nahi banata |
| **Subquery Stats** | Customer list mein totals SQL subquery se — Python loop nahi |
| **Event Bus Debounce** | 100ms — ek saath 10 update aaye toh sirf ek baar fire |
| **Search Debounce** | 300ms — user typing rokne ke baad hi search kare |
| **Worker Thread** | Heavy operations (PDF, DB) background thread mein — UI freeze nahi hota |
| **Log Rotation** | 10MB file size → auto-rotate, 5 backup files, disk full nahi hota |
| **LIMIT on Queries** | Sab list queries mein LIMIT 100/200 — zyada data ek saath nahi laata |
| **Singleton Pattern** | DB connection, session, theme, event bus — ek hi instance, baar baar initialize nahi |

---

## 10. KNOWN ISSUES / LIMITATIONS

| Issue | Detail |
|---|---|
| **Dark Theme Only** | Sirf dark mode hai, light mode ka option nahi hai |
| **Single User** | Login system hai lekin primarily single-user desktop app hai |
| **Local MySQL** | Cloud database support nahi hai, sirf localhost |
| **No REST API** | API layer nahi hai, sirf desktop app |
| **WhatsApp via Browser** | WhatsApp Business API nahi, sirf wa.me link open karta hai browser mein |
| **SMTP Email** | SMTP config chahiye, OAuth/Gmail API integration nahi hai |
| **No Test Suite** | Unit tests ya integration tests nahi hain |
| **No Migrations** | DB schema manually create karna padta hai, migration tool nahi hai |
| **Indian Locale** | en_IN.UTF-8 Windows par available nahi ho sakta |
| **Segoe UI Font** | Windows-specific font, Linux/Mac par different dikhega |
| **Single Currency** | Sirf Indian Rupee (₹) support |
| **Single Company** | Ek installation mein sirf ek shop/company |

---

## 11. FILE-WISE BREAKDOWN

| File | Lines (approx) | Kya Karta Hai |
|---|---|---|
| `main.py` | 216 | App startup, splash, login bypass, main window launch |
| `config.py` | 170 | DB config, colors, fonts, paths, env validation |
| `database/db_connection.py` | ~200 | Thread-safe MySQL singleton, auto-reconnect, query logging |
| `database/models.py` | ~120 | 11 dataclasses for all entities |
| `database/queries.py` | ~400 | All SQL queries organized by feature |
| `views/main_window.py` | ~300 | Sidebar + stacked widget shell |
| `views/login_view.py` | ~250 | Full-screen glassmorphism login |
| `views/enhanced_dashboard_view.py` | ~400 | 8 metric cards, 4 charts, summary table |
| `views/invoice_view.py` | ~500 | Tabbed: create + list invoices |
| `views/invoice_management_view.py` | ~350 | Full invoice table with right-click actions |
| `views/customer_view.py` | ~350 | Splitter: customer table + details/invoices |
| `views/technician_view.py` | ~300 | Splitter: technician table + details/work/customers |
| `views/settings_view.py` | ~500 | Tabbed: profile, shop, master data |
| `views/amc_view.py` | ~400 | 3 tabs: new AMC, list, visit schedule |
| `views/daily_log_view.py` | ~250 | Log table + expense/profit summary |
| `views/online_request_view.py` | ~300 | Auto-refresh table, toast, sound alerts |
| `views/inventory_view.py` | ~250 | Parts table, low-stock, stock adjustments |
| `views/report_view.py` | ~350 | P&L + GST report with charts |
| `views/reminder_dialog.py` | 200 | Pending payments + AMC expiry reminders |
| `views/customer_ledger_dialog.py` | 209 | Customer account statement |
| `views/email_invoice_dialog.py` | 237 | Send invoice via email |
| `views/bulk_whatsapp_dialog.py` | 208 | Bulk WhatsApp to customers |
| `views/edit_invoice_dialog.py` | 496 | Full 3-tab invoice editing |
| `controllers/auth_controller.py` | ~200 | Login, bcrypt, lockout |
| `controllers/dashboard_controller.py` | ~80 | Single-query dashboard stats |
| `controllers/invoice_controller.py` | ~200 | Transactional invoice CRUD |
| `controllers/customer_controller.py` | ~120 | Customer CRUD with subqueries |
| `controllers/technician_controller.py` | ~80 | Technician CRUD |
| `controllers/settings_controller.py` | ~150 | Shop + master data CRUD |
| `controllers/report_controller.py` | ~100 | P&L + GST queries |
| `controllers/inventory_controller.py` | 66 | Parts + stock movements |
| `controllers/online_request_controller.py` | 62 | Contact message management |
| `utils/unified_theme.py` | ~300 | Theme singleton, QPalette, stylesheet |
| `utils/pdf_generator.py` | 854 | Full A4 GST invoice PDF |
| `utils/validators.py` | 368 | Input validation |
| `utils/formatters.py` | 444 | Currency, date, mobile formatting |
| `utils/session_manager.py` | 259 | Session singleton, thread-safe |
| `utils/logger.py` | 246 | 4 log files, rotation, colored console |
| `utils/event_bus.py` | 89 | Pub-sub with debounce |
| `utils/shortcut_manager.py` | 142 | Customizable keyboard shortcuts |
| `utils/sms_reminder.py` | 82 | WhatsApp message templates |
| `utils/language.py` | 301 | English + Hindi translations |
| `utils/chart_widgets.py` | 276 | 4 custom QPainter charts |
| `utils/search_widget.py` | 149 | Type-ahead customer search |
| `utils/audit.py` | 100 | Audit trail for all operations |

---

## 12. SETUP & DEPLOYMENT CHECKLIST

- [ ] MySQL install karo aur `Desktop_software` database create karo
- [ ] Saari tables create karo (SQL schema)
- [ ] `users` table mein admin user insert karo: `INSERT INTO users (username, password_hash, full_name, role, is_active) VALUES ('admin', '{bcrypt_hash}', 'Admin', 'admin', TRUE)`
- [ ] `.env` file banao: `DB_PASSWORD=your_password`
- [ ] `main.py` mein `LOGIN_ENABLED = True` set karo
- [ ] `assets/logo.png` aur `assets/login_page.png` images dalo
- [ ] `config.py` mein WhatsApp number, GST%, invoice prefix set karo
- [ ] PyInstaller se build karo: `pyinstaller main.spec` (hidden imports ke saath)
- [ ] Test karo: invoice create, PDF generate, email, WhatsApp

---

*14 Views, 10 Controllers, 11 Database Models, 14 Utils, 5 Dialogs — total 50+ source files*
