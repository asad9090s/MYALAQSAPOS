"""
POS Mobile - SQLite Database Layer
Aap ke Tkinter TextFileDB ka mobile version - same schema + behavior
"""
import sqlite3
import os
from datetime import datetime


class MobileDB:
    """SQLite-based database for Android. File location: app's data dir."""

    def __init__(self, db_path=None):
        if db_path is None:
            # Android app data dir (works on both desktop + Android)
            db_path = self._get_default_path()
        self.db_path = db_path
        self._init_schema()

    def _get_default_path(self):
        """Get writable path - works on Android + Desktop"""
        try:
            from android.storage import app_storage_path  # type: ignore
            base = app_storage_path()
        except ImportError:
            # Desktop fallback
            base = os.path.expanduser("~/.pos_mobile")
            os.makedirs(base, exist_ok=True)
        return os.path.join(base, "pos.db")

    def _conn(self):
        """Create a new connection (Kivy/Android requires fresh conn per call)"""
        c = sqlite3.connect(self.db_path)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA foreign_keys = ON")
        return c

    def _init_schema(self):
        """Create all tables if not exist"""
        with self._conn() as c:
            c.executescript("""
            CREATE TABLE IF NOT EXISTS frmClass (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS frmProducts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                barcode TEXT DEFAULT '',
                price REAL DEFAULT 0,
                stock INTEGER DEFAULT 0,
                PurchasePrice REAL DEFAULT 0,
                Minimumq INTEGER DEFAULT 0,
                discount REAL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS frmStudentInfo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                fatherName TEXT DEFAULT 'N/A',
                Phone TEXT DEFAULT 'N/A',
                idclass INTEGER,
                currentyear INTEGER,
                idshift INTEGER DEFAULT 1,
                datetimecreated TEXT
            );

            CREATE TABLE IF NOT EXISTS saleMaster (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                InvoiceNumber TEXT UNIQUE NOT NULL,
                idstudent INTEGER,
                total REAL DEFAULT 0,
                datetimecreated TEXT,
                paid REAL DEFAULT 0,
                Comments TEXT DEFAULT 'N/A',
                paymentType TEXT DEFAULT 'Cash',
                paymentMethod TEXT DEFAULT '',
                paymentReference TEXT DEFAULT '',
                created_by TEXT DEFAULT 'MobileUser'
            );

            CREATE TABLE IF NOT EXISTS frmsaledetail (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                idproduct INTEGER,
                quantity INTEGER,
                idsaleMaster INTEGER,
                price REAL,
                discount REAL DEFAULT 0,
                saledate TEXT,
                FOREIGN KEY (idsaleMaster) REFERENCES saleMaster(id)
            );

            CREATE TABLE IF NOT EXISTS onlinePayments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                idsaleMaster INTEGER,
                InvoiceNumber TEXT,
                idstudent INTEGER,
                customername TEXT,
                paymentmethod TEXT,
                reference TEXT,
                amount REAL,
                datetimecreated TEXT
            );

            CREATE TABLE IF NOT EXISTS frmVendor (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                address TEXT DEFAULT '',
                phone TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS frmCategories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT,
                description TEXT,
                amount REAL,
                payment_method TEXT,
                reference TEXT,
                datetimecreated TEXT
            );

            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT,
                full_name TEXT,
                role TEXT DEFAULT 'cashier',
                active INTEGER DEFAULT 1,
                datetimecreated TEXT
            );

            -- Seed default customer if empty
            INSERT OR IGNORE INTO frmStudentInfo (id, name, fatherName, Phone)
            VALUES (1, 'Walk-in Customer', 'N/A', '0000000000');

            -- Seed default user
            INSERT OR IGNORE INTO users (id, username, password, full_name, role)
            VALUES (1, 'admin', 'admin', 'Administrator', 'admin');
            """)

    # ════════════════════════════════════════════════════════════
    # PRODUCTS
    # ════════════════════════════════════════════════════════════
    def get_products(self, search=""):
        with self._conn() as c:
            if search:
                rows = c.execute(
                    "SELECT * FROM frmProducts WHERE name LIKE ? OR barcode LIKE ? ORDER BY name",
                    (f"%{search}%", f"%{search}%")
                ).fetchall()
            else:
                rows = c.execute("SELECT * FROM frmProducts ORDER BY name").fetchall()
            return [dict(r) for r in rows]

    def get_product_by_barcode(self, barcode):
        with self._conn() as c:
            r = c.execute("SELECT * FROM frmProducts WHERE barcode = ?", (barcode,)).fetchone()
            return dict(r) if r else None

    def get_product_by_id(self, pid):
        with self._conn() as c:
            r = c.execute("SELECT * FROM frmProducts WHERE id = ?", (pid,)).fetchone()
            return dict(r) if r else None

    def add_product(self, name, barcode, price, stock, purchase_price=0, min_qty=0, discount=0):
        with self._conn() as c:
            cur = c.execute(
                "INSERT INTO frmProducts (name, barcode, price, stock, PurchasePrice, Minimumq, discount) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (name, barcode, price, stock, purchase_price, min_qty, discount)
            )
            return cur.lastrowid

    def update_product_stock(self, pid, change):
        with self._conn() as c:
            c.execute("UPDATE frmProducts SET stock = stock + ? WHERE id = ?", (change, pid))

    # ════════════════════════════════════════════════════════════
    # CUSTOMERS
    # ════════════════════════════════════════════════════════════
    def get_customers(self, search=""):
        with self._conn() as c:
            if search:
                rows = c.execute(
                    "SELECT s.*, c.name as className FROM frmStudentInfo s "
                    "LEFT JOIN frmClass c ON s.idclass = c.id "
                    "WHERE s.name LIKE ? OR s.Phone LIKE ? ORDER BY s.name",
                    (f"%{search}%", f"%{search}%")
                ).fetchall()
            else:
                rows = c.execute(
                    "SELECT s.*, c.name as className FROM frmStudentInfo s "
                    "LEFT JOIN frmClass c ON s.idclass = c.id ORDER BY s.name"
                ).fetchall()
            return [dict(r) for r in rows]

    def get_customer_by_id(self, cid):
        with self._conn() as c:
            r = c.execute(
                "SELECT s.*, c.name as className FROM frmStudentInfo s "
                "LEFT JOIN frmClass c ON s.idclass = c.id WHERE s.id = ?", (cid,)
            ).fetchone()
            return dict(r) if r else None

    def add_customer(self, name, shop, phone, class_id=None):
        with self._conn() as c:
            cur = c.execute(
                "INSERT INTO frmStudentInfo (name, fatherName, Phone, idclass, currentyear, idshift, datetimecreated) "
                "VALUES (?, ?, ?, ?, ?, 1, ?)",
                (name, shop, phone, class_id, datetime.now().year, datetime.now().strftime("%Y-%m-%d"))
            )
            return cur.lastrowid

    # ════════════════════════════════════════════════════════════
    # SALES
    # ════════════════════════════════════════════════════════════
    def save_sale(self, items, customer_id, total, paid, comments="N/A",
                  pay_type="Cash", pay_method="", pay_ref="", issued_by="MobileUser",
                  bill_disc=0, cash_disc=0, disc_mode="EveryItem"):
        """Save complete sale in transaction. Returns (invoice_number, balance)."""
        invoice_num = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        net_total = max(0, total - cash_disc)
        balance = max(0, net_total - paid)

        if customer_id is None:
            customer_id = 1  # Walk-in

        item_count = max(1, len(items))
        with self._conn() as c:
            cur = c.execute(
                "INSERT INTO saleMaster (InvoiceNumber, idstudent, total, datetimecreated, "
                "paid, Comments, paymentType, paymentMethod, paymentReference, created_by) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (invoice_num, customer_id, net_total,
                 datetime.now().strftime("%Y-%m-%d"), paid, comments,
                 pay_type, pay_method if pay_type == "Online" else "",
                 pay_ref if pay_type == "Online" else "", issued_by)
            )
            master_id = cur.lastrowid

            for item in items:
                pid = item['id']
                qty = item['qty']
                price = item['price']
                disc = item.get('disc', 0)

                if disc_mode == "OverAll":
                    final_disc = bill_disc / item_count
                elif disc_mode == "Percentage" and item_count > 0:
                    final_disc = (bill_disc / 100) * (price * qty) / item_count
                else:
                    final_disc = disc

                c.execute(
                    "INSERT INTO frmsaledetail (idproduct, quantity, idsaleMaster, price, discount, saledate) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (pid, qty, master_id, price, final_disc, datetime.now().strftime("%Y-%m-%d"))
                )
                c.execute("UPDATE frmProducts SET stock = stock - ? WHERE id = ? AND stock >= ?",
                          (qty, pid, qty))

            if pay_type == "Online" and pay_method:
                c.execute(
                    "INSERT INTO onlinePayments (idsaleMaster, InvoiceNumber, idstudent, customername, "
                    "paymentmethod, reference, amount, datetimecreated) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (master_id, invoice_num, customer_id, "", pay_method, pay_ref,
                     paid if paid > 0 else net_total, datetime.now().strftime("%Y-%m-%d"))
                )

        return invoice_num, balance

    def get_sale_history(self, limit=50):
        with self._conn() as c:
            rows = c.execute(
                "SELECT m.*, s.name as customer_name FROM saleMaster m "
                "LEFT JOIN frmStudentInfo s ON m.idstudent = s.id "
                "ORDER BY m.id DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(r) for r in rows]

    def get_sale_items(self, master_id):
        with self._conn() as c:
            rows = c.execute(
                "SELECT d.*, p.name as product_name FROM frmsaledetail d "
                "JOIN frmProducts p ON d.idproduct = p.id "
                "WHERE d.idsaleMaster = ?", (master_id,)
            ).fetchall()
            return [dict(r) for r in rows]

    # ════════════════════════════════════════════════════════════
    # DASHBOARD STATS
    # ════════════════════════════════════════════════════════════
    def get_dashboard_stats(self):
        today = datetime.now().strftime("%Y-%m-%d")
        with self._conn() as c:
            today_sales = c.execute(
                "SELECT COUNT(*) as cnt, COALESCE(SUM(total),0) as total FROM saleMaster WHERE datetimecreated = ?",
                (today,)
            ).fetchone()
            total_products = c.execute("SELECT COUNT(*) as cnt FROM frmProducts").fetchone()
            low_stock = c.execute(
                "SELECT COUNT(*) as cnt FROM frmProducts WHERE stock <= Minimumq AND Minimumq > 0"
            ).fetchone()
            total_customers = c.execute("SELECT COUNT(*) as cnt FROM frmStudentInfo").fetchone()
            return {
                'today_sales_count': today_sales['cnt'],
                'today_sales_total': today_sales['total'],
                'total_products': total_products['cnt'],
                'low_stock_count': low_stock['cnt'],
                'total_customers': total_customers['cnt'],
            }

    # ════════════════════════════════════════════════════════════
    # SAMPLE DATA (for first-run testing)
    # ════════════════════════════════════════════════════════════
    def seed_sample_data(self):
        """Add sample products + customers if DB is empty (testing ke liye)"""
        with self._conn() as c:
            cnt = c.execute("SELECT COUNT(*) as cnt FROM frmProducts").fetchone()['cnt']
            if cnt > 0:
                return False

            products = [
                ("Coca Cola 500ml", "89650001", 80, 50, 60, 5, 0),
                ("Pepsi 500ml", "89650002", 80, 40, 60, 5, 0),
                ("Lays Small", "89650003", 50, 30, 35, 5, 0),
                ("Kurkure", "89650004", 50, 25, 35, 5, 0),
                ("Biscuit Prince", "89650005", 30, 100, 20, 10, 0),
                ("Tea Cup", "89650006", 20, 200, 12, 20, 0),
                ("Water Bottle 1.5L", "89650007", 60, 80, 40, 10, 0),
                ("Milk Packet 1L", "89650008", 180, 20, 165, 5, 0),
                ("Bread", "89650009", 120, 15, 100, 5, 0),
                ("Eggs (dozen)", "89650010", 280, 30, 250, 6, 0),
            ]
            c.executemany(
                "INSERT INTO frmProducts (name, barcode, price, stock, PurchasePrice, Minimumq, discount) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)", products
            )

            customers = [
                ("Ali Khan", "Ali Gen Store", "03001234567", None),
                ("Ahmed Raza", "Raza Mart", "03211234567", None),
                ("Bilal Ahmad", "Bilal Traders", "03331234567", None),
                ("Usman Tariq", "Tariq Store", "03451234567", None),
            ]
            c.executemany(
                "INSERT INTO frmStudentInfo (name, fatherName, Phone, idclass, currentyear, datetimecreated) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                [(n, s, p, c, datetime.now().year, datetime.now().strftime("%Y-%m-%d")) for n, s, p, c in customers]
            )
            return True
