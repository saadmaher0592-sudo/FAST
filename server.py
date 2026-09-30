import sqlite3
import random
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

DB_NAME = 'fast70_v2.db'

def get_db_connection():
    conn = sqlite3.connect(DB_NAME, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            national_id TEXT NOT NULL,
            birth_year TEXT NOT NULL,
            balance REAL DEFAULT 0.00,
            spent REAL DEFAULT 20.49,
            orders_count INTEGER DEFAULT 21,
            points REAL DEFAULT 20.50
        )
    ''')
    
    cursor.execute('CREATE TABLE IF NOT EXISTS categories (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL)')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER,
            service_id INTEGER UNIQUE,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            min_val INTEGER NOT NULL,
            max_val INTEGER NOT NULL,
            description TEXT,
            FOREIGN KEY (category_id) REFERENCES categories (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id_num INTEGER UNIQUE NOT NULL,
            user_id INTEGER,
            service_id INTEGER,
            service_name TEXT,
            target_link TEXT,
            quantity INTEGER,
            start_count INTEGER DEFAULT 0,
            remains INTEGER DEFAULT 0,
            total_charge REAL,
            status TEXT DEFAULT 'مكتمل',
            created_at TEXT
        )
    ''')
    
    cursor.execute('''
        INSERT OR IGNORE INTO users (id, username, email, password, national_id, birth_year, balance, spent, orders_count, points)
        VALUES (1, 'saad2abbas6', 'saad@fast.com', '123456', '123456789', '2006', 0.00, 20.49, 21, 20.50)
    ''')
    
    conn.commit()

    categories = [
        (1, '🔥 أفضل الخدمات [التي ننصح بها دائماً]'),
        (2, '🌐 خدمات ممولة حقيقي انستقرام | تيك توك')
    ]
    for cat in categories:
        cursor.execute("INSERT OR IGNORE INTO categories (id, name) VALUES (?, ?)", cat)

    services = [
        (1, 8855, '8855 - ✨ متابعين انستغرام عربي حقيقي مكس متفاعلين', 2.90, 1000, 15000, 'أفضل باقة لرفع المتابعين بحساب سعر تلقائي حسب الكمية المكتوبة.'),
        (2, 8500, '8500 - متابعين انستغرام عربي حقيقية متفاعلين من اعلانات ممولة', 3.00, 1000, 50000, 'جوده عالية جداً [ البدء 24 - 48 ساعه ] [ سيرفر 1 ]')
    ]
    for ser in services:
        cursor.execute("INSERT OR IGNORE INTO services (category_id, service_id, name, price, min_val, max_val, description) VALUES (?, ?, ?, ?, ?, ?, ?)", ser)
        
    conn.commit()
    conn.close()

@app.route('/')
def index(): return app.send_static_file('index.html')

@app.route('/api/auth/register', methods=['POST'])
def api_register():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    national_id = data.get('national_id', '').strip()
    birth_year = data.get('birth_year', '').strip()
    
    if not username or not email or not password or not national_id or not birth_year:
        return jsonify({"status": "error", "message": "جميع حقول التسجيل مطلوبة لحماية حسابك"}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO users (username, email, password, national_id, birth_year, balance, spent, orders_count, points) 
            VALUES (?, ?, ?, ?, ?, 0.00, 20.49, 21, 20.50)
        ''', (username, email, password, national_id, birth_year))
        conn.commit()
        return jsonify({"status": "success", "message": "تم إنشاء حسابك بنجاح!"})
    except sqlite3.IntegrityError:
        return jsonify({"status": "error", "message": "اسم المستخدم أو البريد الإلكتروني مسجل مسبقاً"}), 400
    finally:
        conn.close()

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    user_input = data.get('username', '').strip()
    password = data.get('password', '')
    conn = get_db_connection()
    cursor = conn.cursor()
    user = cursor.execute('SELECT id, username FROM users WHERE (username=? OR email=?) AND password=?', (user_input, user_input, password)).fetchone()
    conn.close()
    if user: return jsonify({"status": "success", "user": {"id": user['id'], "username": user['username']}})
    return jsonify({"status": "error", "message": "بيانات الدخول غير صحيحة"}), 401

# 1. مسار التحقق من البيانات أولاً قبل الإظهار
@app.route('/api/auth/verify-data', methods=['POST'])
def api_verify_data():
    data = request.get_json() or {}
    email = data.get('email', '').strip()
    national_id = data.get('national_id', '').strip()
    birth_year = data.get('birth_year', '').strip()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    user = cursor.execute('SELECT id FROM users WHERE email=? AND national_id=? AND birth_year=?', (email, national_id, birth_year)).fetchone()
    conn.close()
    
    if user:
        return jsonify({"status": "success", "message": "تم التحقق بنجاح! يرجى كتابة كلمة المرور الجديدة الآن."})
    return jsonify({"status": "error", "message": "البيانات المدخلة غير متطابقة مع السجلات المعتمدة لدينا"}), 400

# 2. مسار التحديث النهائي لكمة المرور بعد النجاح
@app.route('/api/auth/update-password', methods=['POST'])
def api_update_password():
    data = request.get_json() or {}
    email = data.get('email', '').strip()
    new_password = data.get('new_password', '')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET password=? WHERE email=?', (new_password, email))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "تمت إعادة تعيين وتحديث كلمة المرور بنجاح!"})

@app.route('/api/account/stats', methods=['POST'])
def api_stats():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    conn = get_db_connection()
    cursor = conn.cursor()
    user = cursor.execute('SELECT spent, orders_count FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if not user: return jsonify({"status": "error", "message": "المستخدم غير موجود"}), 404
    return jsonify({"status": "success", "balance": 0.00, "spent": round(user['spent'], 4), "orders_count": user['orders_count'], "points": round(user['spent'], 2), "level": "VIP"})

@app.route('/api/data/categories', methods=['GET'])
def api_categories():
    conn = get_db_connection()
    cursor = conn.cursor()
    rows = cursor.execute('SELECT * FROM categories ORDER BY id ASC').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/data/services/<int:cat_id>', methods=['GET'])
def api_services(cat_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    rows = cursor.execute('SELECT * FROM services WHERE category_id = ?', (cat_id,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/orders/history/<int:user_id>', methods=['GET'])
def api_order_history(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    rows = cursor.execute('SELECT order_id_num, service_name, target_link, quantity, start_count, remains, total_charge, status, created_at FROM orders WHERE user_id = ? ORDER BY id DESC', (user_id,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/orders/create', methods=['POST'])
def api_create_order():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    service_id = data.get('service_id')
    link = data.get('link')
    qty = int(data.get('quantity', 0))
    conn = get_db_connection()
    cursor = conn.cursor()
    service = cursor.execute('SELECT * FROM services WHERE service_id = ?', (service_id,)).fetchone()
    if not service or qty < service['min_val'] or qty > service['max_val']:
        conn.close()
        return jsonify({"status": "error", "message": "العدد المدخل غير مطابق للحدود"}), 400
    charge = (service['price'] / 1000) * qty
    order_id_rand = random.randint(5300000, 5399999)
    current_time_str = datetime.now().strftime("%H:%M:%S %Y-%m-%d")
    cursor.execute('''
        INSERT INTO orders (order_id_num, user_id, service_id, service_name, target_link, quantity, start_count, remains, total_charge, status, created_at) 
        VALUES (?, ?, ?, ?, ?, ?, 0, 0, ?, 'مكتمل', ?)
    ''', (order_id_rand, user_id, service_id, service['name'], link, qty, charge, current_time_str))
    cursor.execute('UPDATE users SET spent = spent + ?, orders_count = orders_count + 1 WHERE id = ?', (charge, user_id))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": f"تم حفظ وتأكيد الطلب برقم المعرّف الحقيقي: {order_id_rand}."})

if __name__ == '__main__':
    init_database()
    app.run(host='127.0.0.1', port=5000, debug=True)
