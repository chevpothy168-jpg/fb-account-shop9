import io
import base64
import sqlite3
import os
from flask import Flask, jsonify, render_template_string, request, redirect, url_for, Response
import qrcode
from bakong_khqr import KHQR

app = Flask(__name__)
DB_NAME = "shop.db"
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Bakong Official Token (Valid until January 19, 2027)
BAKONG_TOKEN = "eyJhbGciOiJIUzI1NilsInR5cCI6IkpXVCJ9.eyJKyXRlXHRpImxkljoIYjknN2E5ZmZmM1NDm1NDeNdEY2NDe2MiJ9LCJpXQioJe3OTI1NTEyMzAsAslmV4ccI6MTgwMDMyMnNzNzIzKpM1dMyNzIzMH0.Sml-Y-R_0DGwDsz7ZDSKPisMdRbZyo2KuCmwft3Wr0o"

# Initialize KHQR Client with your official account chev_pothy3@aclb
khqr_client = KHQR(BAKONG_TOKEN)

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS categories (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE)')
    cursor.execute('''CREATE TABLE IF NOT EXISTS products (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, 
                        price REAL NOT NULL, description TEXT, image TEXT, category_id INTEGER,
                        account_data TEXT, stock INTEGER DEFAULT 0)''')
    cursor.execute('CREATE TABLE IF NOT EXISTS transactions (md5 TEXT PRIMARY KEY, status TEXT NOT NULL, product_id INTEGER)')
    conn.commit()
    
    cursor.execute("SELECT COUNT(*) FROM categories")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO categories (name) VALUES (?)", [('Facebook Account',), ('Facebook Page',)])
        conn.commit()
    conn.close()

@app.route('/')
def index():
    cat_id = request.args.get('cat')
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM categories")
    categories = cursor.fetchall()
    
    if cat_id:
        cursor.execute("SELECT id, name, price, description, image, category_id, stock FROM products WHERE category_id = ?", (cat_id,))
    else:
        cursor.execute("SELECT id, name, price, description, image, category_id, stock FROM products")
    rows = cursor.fetchall()
    conn.close()

    products = [{
        "id": r[0], "name": r[1], "price": r[2], "description": r[3], 
        "image": (r[4] if r[4] and r[4].startswith('http') else url_for('static', filename='uploads/' + r[4]) if r[4] else ''), 
        "category_id": r[5], "stock": r[6]
    } for r in rows]

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="km">
    <head>
        <meta charset="UTF-8"><title>Facebook Account Shop</title>
        <style>
            body { font-family: 'Khmer OS Siemreap', sans-serif; background: #f8f9fa; margin: 0; padding: 0; text-align: center; }
            header { background: #fff; padding: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); position: relative; }
            .admin-link { position: absolute; top: 20px; right: 20px; background: #333; color: white; padding: 8px 15px; text-decoration: none; border-radius: 5px; font-size: 14px; }
            .top-menu { background: #673AB7; padding: 12px 0; margin-bottom: 30px; display: flex; justify-content: center; gap: 20px; flex-wrap: wrap; }
            .top-menu a { color: #fff; text-decoration: none; font-size: 15px; padding: 6px 15px; border-radius: 4px; transition: 0.3s; }
            .top-menu a.active, .top-menu a:hover { background: #ff9800; color: #fff; }
            .product-grid { display: flex; justify-content: center; gap: 20px; flex-wrap: wrap; padding: 0 20px 40px 20px; }
            .product-card { background: white; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.08); width: 240px; padding: 15px; text-align: center; display: flex; flex-direction: column; justify-content: space-between; transition: 0.3s; }
            .product-card:hover { transform: translateY(-5px); }
            .product-card img { max-width: 100%; max-height: 140px; object-fit: contain; border-radius: 8px; margin: 0 auto; }
            .price { color: #e91e63; font-weight: bold; font-size: 18px; margin: 5px 0; }
            .desc { font-size: 12px; color: #666; height: 35px; overflow: hidden; margin-bottom: 10px; }
            .stock-badge { font-size: 12px; font-weight: bold; padding: 3px 8px; border-radius: 4px; display: inline-block; margin-bottom: 8px; }
            .in-stock { background: #e8f5e9; color: #2e7d32; }
            .out-stock { background: #ffebee; color: #c62828; }
            .buy-btn { background: #4CAF50; color: white; border: none; padding: 8px 15px; cursor: pointer; border-radius: 5px; width: 100%; font-family: 'Khmer OS Siemreap', sans-serif; }
            .buy-btn:hover { background: #45a049; }
            .buy-btn.disabled { background: #ccc; cursor: not-allowed; }
        </style>
    </head>
    <body>
        <header>
            <a href="/admin" class="admin-link">⚙️ Admin Panel</a>
            <h1>🛍️ ហាងលក់គណនី Facebook អនឡាញ</h1>
            <p style="color: #666; margin: 5px 0 0 0;">ទូទាត់ប្រាក់ស្វ័យប្រវត្តិតាម KHQR និងទាញយកហ្វាល Account ភ្លាមៗ</p>
        </header>

        <div class="top-menu">
            <a href="/" class="{% if not request.args.get('cat') %}active{% endif %}">🏠 ទាំងអស់</a>
            {% for cat in categories %}
            <a href="/?cat={{ cat[0] }}" class="{% if request.args.get('cat') == cat[0]|string %}active{% endif %}">{{ cat[1] }}</a>
            {% endfor %}
        </div>

        <div class="product-grid">
            {% if products %}
                {% for p in products %}
                <div class="product-card">
                    <div>
                        <img src="{{ p.image }}" alt="{{ p.name }}">
                        <h3 style="margin: 10px 0 5px 0; font-size: 16px;">{{ p.name }}</h3>
                        <div class="desc">{{ p.description }}</div>
                    </div>
                    <div>
                        {% if p.stock > 0 %}
                            <span class="stock-badge in-stock">🟢 មានក្នុងស្តុក ({{ p.stock }})</span>
                            <div class="price">${{ "%.2f"|format(p.price) }}</div>
                            <button class="buy-btn" onclick="location.href='/checkout?id={{ p.id }}'">ទិញឥឡូវនេះ</button>
                        {% else %}
                            <span class="stock-badge out-stock">🔴 អស់ស្តុក (Out of Stock)</span>
                            <div class="price">${{ "%.2f"|format(p.price) }}</div>
                            <button class="buy-btn disabled" disabled>អស់ទំនិញ</button>
                        {% endif %}
                    </div>
                </div>
                {% endfor %}
            {% else %}
                <p style="color: #888; margin-top: 40px; font-size: 16px;">ពុំមានទំនិញនៅក្នុងប្រភេទនេះទេ!</p>
            {% endif %}
        </div>
    </body>
    </html>""", categories=categories, products=products)

@app.route('/checkout')
def checkout():
    product_id = request.args.get('id')
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, description, image, stock FROM products WHERE id = ?", (product_id,))
    r = cursor.fetchone()
    conn.close()
    if not r or r[5] <= 0: return redirect(url_for('index'))
    product = {"id": r[0], "name": r[1], "price": r[2], "description": r[3], "image": (r[4] if r[4] and r[4].startswith('http') else url_for('static', filename='uploads/' + r[4]) if r[4] else '')}
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="km"><head><meta charset="UTF-8"><title>Checkout</title>
    <style>
        body { font-family: 'Khmer OS Siemreap', sans-serif; background: #f4f6f9; text-align: center; margin-top: 30px; }
        .box { background: white; padding: 30px; border-radius: 10px; display: inline-block; width: 380px; text-align: left; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        button { background: #4CAF50; color: white; border: none; padding: 10px; width: 100%; border-radius: 5px; cursor: pointer; margin-top: 10px; font-family: 'Khmer OS Siemreap', sans-serif; }
    </style></head>
    <body><div class="box">
        <a href="/" style="color:#2196F3; text-decoration:none;">← ត្រឡប់ក្រោយ</a>
        <h2>🛒 បញ្ជាក់ការទូទាត់</h2>
        <p>ទំនិញ៖ <strong>{{ product.name }}</strong></p>
        <p><strong>ការពិពណ៌នាលម្អិត៖</strong><br><span style="color:#555; font-size:13px;">{{ product.description }}</span></p>
        <p>តម្លៃសរុប៖ <strong style="color:#e91e63;">${{ "%.2f"|format(product.price) }}</strong></p>
        
        <button id="pay-btn" onclick="startPay({{ product.id }}, {{ product.price }}, '{{ product.name }}')">បង្កើត QR សម្រាប់បង់ប្រាក់</button>
        
        <!-- QR Box initially hidden until user clicks generate -->
        <div id="qr-box" style="display:none; text-align:center; margin-top:15px;">
            <p>សូមស្កេន KHQR (គណនី chev_pothy3@aclb) ដើម្បីទូទាត់៖</p>
            <img id="qr-img" width="200">
            <p style="color:#555; font-size:13px; margin:10px 0;">បន្ទាប់ពីស្កេនបង់ប្រាក់ជោគជ័យ សូមចុចប៊ូតុងខាងក្រោម៖</p>
            <button style="background:#2196F3; font-size:15px; padding:12px;" onclick="confirmPaid()">✅ បានបង់ប្រាក់រួច - យកហ្វាល Account</button>
        </div>
    </div>
    <script>
    let md5Hash = null;
    async function startPay(id, price, name) {
        let payBtn = document.getElementById('pay-btn');
        payBtn.innerText = 'កំពុងបង្កើត QR...';
        payBtn.disabled = true;

        try {
            let res = await fetch('/api/create-qr', {
                method: 'POST', 
                headers: {'Content-Type': 'application/json'}, 
                body: JSON.stringify({product_id: id, amount: price, product_name: name})
            });
            let data = await res.json();
            
            if(data.success) {
                payBtn.style.display = 'none';
                md5Hash = data.md5;
                document.getElementById('qr-img').src = data.qr_image;
                document.getElementById('qr-box').style.display = 'block';
            } else {
                alert('កំហុស៖ ' + (data.message || 'មិនអាចបង្កើត QR បានទេ'));
                payBtn.innerText = 'បង្កើត QR សម្រាប់បង់ប្រាក់';
                payBtn.disabled = false;
            }
        } catch (err) {
            alert('មានបញ្ហាក្នុងការតភ្ជាប់ Server!');
            payBtn.innerText = 'បង្កើត QR សម្រាប់បង់ប្រាក់';
            payBtn.disabled = false;
        }
    }
    async function confirmPaid() {
        if(!md5Hash) {
            alert('សូមបង្កើត QR Code និងស្កេនបង់ប្រាក់ជាមុនសិន!');
            return;
        }
        let res = await fetch('/api/simulate-success', {
            method: 'POST', 
            headers: {'Content-Type': 'application/json'}, 
            body: JSON.stringify({md5: md5Hash})
        });
        let data = await res.json();
        if(data.success) {
            window.location.href = '/download/' + md5Hash;
        } else {
            alert('មានបញ្ហាពេលបញ្ជាក់ការទូទាត់!');
        }
    }
    </script></body></html>""", product=product)

@app.route('/api/create-qr', methods=['POST'])
def create_qr():
    d = request.json
    product_id = d['product_id']
    amount = d['amount']
    product_name = d['product_name']

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT stock FROM products WHERE id = ?", (product_id,))
    prod = cursor.fetchone()
    if not prod or prod[0] <= 0:
        conn.close()
        return jsonify({"success": False, "message": "Out of stock!"})
    conn.close()

    try:
        res = khqr_client.create_qr(
            bank_account="chev_pothy3@aclb",
            merchant_name="Facebook Shop",
            merchant_city="Phnom Penh",
            amount=float(amount),
            currency="USD",
            bill_number=f"INV{product_id}"
        )
        khqr_string = res.qr
        md5 = res.md5
    except Exception as e:
        print("KHQR Generation Error:", e)
        return jsonify({"success": False, "message": "Failed to generate valid KHQR"})

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO transactions (md5, status, product_id) VALUES (?, ?, ?)", (md5, "PENDING", product_id))
    conn.commit()
    conn.close()
    
    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(khqr_string)
    qr.make(fit=True)
    buf = io.BytesIO()
    qr.make_image().save(buf, format="PNG")
    img_b64 = base64.b64encode(buf.getvalue()).decode()
    
    return jsonify({"success": True, "qr_image": f"data:image/png;base64,{img_b64}", "md5": md5})

@app.route('/api/simulate-success', methods=['POST'])
def simulate_success():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE transactions SET status = 'PAID' WHERE md5 = ?", (request.json.get('md5'),))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/download/<md5>')
def download_file(md5):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT status, product_id FROM transactions WHERE md5 = ?", (md5,))
    tx = cursor.fetchone()
    if not tx or tx[0] != 'PAID':
        conn.close()
        return "Unauthorized or Payment not completed!", 403
    
    product_id = tx[1]
    
    cursor.execute("SELECT name, account_data, stock FROM products WHERE id = ?", (product_id,))
    prod = cursor.fetchone()
    
    if not prod or prod[2] <= 0:
        conn.close()
        return "Product out of stock!", 400
        
    p_name, acc_data, current_stock = prod[0], prod[1] or "", prod[2]
    
    lines = [line.strip() for line in acc_data.split('\n') if line.strip()]
    
    if not lines:
        conn.close()
        return "No accounts available!", 400
        
    single_account = lines[0]
    remaining_lines = lines[1:]
    new_account_data = "\n".join(remaining_lines)
    new_stock = len(remaining_lines)
    
    cursor.execute("UPDATE products SET account_data = ?, stock = ? WHERE id = ?", (new_account_data, new_stock, product_id))
    conn.commit()
    conn.close()
    
    return Response(
        single_account,
        mimetype="text/plain",
        headers={"Content-disposition": f"attachment; filename=Facebook_Account_{product_id}.txt"}
    )

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add_category':
            try:
                cursor.execute("INSERT INTO categories (name) VALUES (?)", (request.form.get('category_name'),))
                conn.commit()
            except: pass
        elif action == 'edit_category':
            try:
                cursor.execute("UPDATE categories SET name = ? WHERE id = ?", (request.form.get('category_name'), request.form.get('category_id')))
                conn.commit()
            except: pass
        elif action == 'delete_category':
            cursor.execute("DELETE FROM categories WHERE id = ?", (request.form.get('category_id'),))
            conn.commit()
        elif action == 'add':
            file = request.files.get('image_file')
            img_name = ""
            if file and file.filename != '':
                img_name = file.filename
                file.save(os.path.join(UPLOAD_FOLDER, img_name))
            
            acc_data = request.form.get('account_data', '')
            lines = [l.strip() for l in acc_data.split('\n') if l.strip()]
            stock_val = len(lines)
            
            cursor.execute("INSERT INTO products (name, price, description, image, category_id, account_data, stock) VALUES (?, ?, ?, ?, ?, ?, ?)",
                           (request.form.get('name'), float(request.form.get('price')), request.form.get('description'), img_name, request.form.get('category_id'), acc_data, stock_val))
            conn.commit()
        elif action == 'delete':
            cursor.execute("DELETE FROM products WHERE id = ?", (request.form.get('id'),))
            conn.commit()
        elif action == 'edit':
            file = request.files.get('image_file')
            acc_data = request.form.get('account_data', '')
            lines = [l.strip() for l in acc_data.split('\n') if l.strip()]
            stock_val = len(lines)
            
            if file and file.filename != '':
                img_name = file.filename
                file.save(os.path.join(UPLOAD_FOLDER, img_name))
                cursor.execute("UPDATE products SET name=?, price=?, description=?, image=?, category_id=?, account_data=?, stock=? WHERE id=?",
                               (request.form.get('name'), float(request.form.get('price')), request.form.get('description'), img_name, request.form.get('category_id'), acc_data, stock_val, request.form.get('id')))
            else:
                cursor.execute("UPDATE products SET name=?, price=?, description=?, category_id=?, account_data=?, stock=? WHERE id=?",
                               (request.form.get('name'), float(request.form.get('price')), request.form.get('description'), request.form.get('category_id'), acc_data, stock_val, request.form.get('id')))
            conn.commit()
        return redirect(url_for('admin'))

    cursor.execute("SELECT id, name FROM categories")
    categories = cursor.fetchall()
    cursor.execute("SELECT p.id, p.name, p.price, p.description, p.image, c.name, p.category_id, p.account_data, p.stock FROM products p LEFT JOIN categories c ON p.category_id = c.id")
    rows = cursor.fetchall()
    conn.close()

    products = [{
        "id": r[0], "name": r[1], "price": r[2], "description": r[3], 
        "image": (r[4] if r[4] and r[4].startswith('http') else url_for('static', filename='uploads/' + r[4]) if r[4] else ''), 
        "category_name": r[5] or "គ្មាន", "category_id": r[6], "account_data": r[7], "stock": r[8]
    } for r in rows]

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="km">
    <head><meta charset="UTF-8"><title>Admin Panel</title>
    <style>
        body { font-family: 'Khmer OS Siemreap', sans-serif; background: #f4f6f9; padding: 20px; }
        .container { max-width: 1000px; margin: auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { border: 1px solid #ddd; padding: 8px; font-size: 13px; text-align: left; }
        th { background: #f2f2f2; }
        input, select, textarea { width: 100%; padding: 6px; margin: 3px 0 10px 0; box-sizing: border-box; }
        button { background: #4CAF50; color: white; border: none; padding: 8px 12px; cursor: pointer; border-radius: 5px; font-family: 'Khmer OS Siemreap', sans-serif; }
        .modal { display: none; position: fixed; z-index: 1; left: 0; top: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.4); }
        .modal-content { background: white; margin: 8% auto; padding: 20px; width: 450px; border-radius: 10px; }
    </style></head>
    <body>
    <div class="container">
        <a href="/">← ត្រឡប់ទៅហាងវិញ</a>
        <h2>⚙️ Admin Dashboard</h2>
        
        <h3>📁 គ្រប់គ្រង Menu / Categories</h3>
        <form method="POST" style="display: flex; gap: 10px;">
            <input type="hidden" name="action" value="add_category">
            <input type="text" name="category_name" required placeholder="ឈ្មោះប្រភេទថ្មី">
            <button type="submit" style="height: 34px;">បន្ថែម</button>
        </form>
        <div style="margin: 10px 0 20px 0;">
            {% for cat in categories %}
            <span style="background: #e0e0e0; padding: 5px 10px; border-radius: 5px; display:inline-block; margin:3px; font-size: 13px;">
                {{ cat[1] }}
                <button style="background:#ff9800; color:white; border:none; padding:2px 5px; border-radius:3px; cursor:pointer; font-size:11px; margin-left:5px;" onclick="openEditCat('{{ cat[0] }}', '{{ cat[1] }}')">កែ</button>
                <form method="POST" style="display:inline;">
                    <input type="hidden" name="action" value="delete_category"><input type="hidden" name="category_id" value="{{ cat[0] }}">
                    <button type="submit" style="background:none; color:red; border:none; cursor:pointer; padding:0; font-weight:bold; margin-left:3px;" onclick="return confirm('លុប?')">×</button>
                </form>
            </span>
            {% endfor %}
        </div>

        <h3>➕ បន្ថែមទំនិញថ្មី (Paste Accounts 1 គណនីក្នុង ១ បន្ទាត់)</h3>
        <form method="POST" enctype="multipart/form-data">
            <input type="hidden" name="action" value="add">
            <label>ឈ្មោះទំនិញ៖</label><input type="text" name="name" required>
            <label>Category៖</label><select name="category_id" required>
                <option value="">-- ជ្រើសរើស --</option>{% for cat in categories %}<option value="{{ cat[0] }}">{{ cat[1] }}</option>{% endfor %}
            </select>
            <label>តម្លៃ ($)：</label><input type="number" step="0.01" name="price" required>
            <label>ការពិពណ៌នា៖</label><textarea name="description"></textarea>
            <label style="color:#d9534f; font-weight:bold;">បញ្ជី Account (១ បន្ទាត់ = ១ គណនី):</label>
            <textarea name="account_data" rows="5" placeholder="user1|pass1|2fa1&#10;user2|pass2|2fa2&#10;user3|pass3|2fa3" required></textarea>
            <label>រូបភាព៖</label><input type="file" name="image_file" accept="image/*" required>
            <button type="submit">រក្សាទុកទំនិញ</button>
        </form>

        <h3>📋 បញ្ជីទំនិញទាំងអស់</h3>
        <table>
            <tr><th>ID</th><th>រូប</th><th>ឈ្មោះ</th><th>Category</th><th>តម្លៃ</th><th>ស្តុក (Stock)</th><th>សកម្មភាព</th></tr>
            {% for p in products %}
            <tr>
                <td>{{ p.id }}</td><td><img src="{{ p.image }}" width="35" height="35" style="object-fit:cover;"></td>
                <td>{{ p.name }}</td><td>{{ p.category_name }}</td><td>${{ "%.2f"|format(p.price) }}</td>
                <td><strong>{{ p.stock }}</strong></td>
                <td>
                    <button style="background:#ff9800; padding:4px 8px;" onclick="openEdit('{{ p.id }}', '{{ p.name }}', '{{ p.price }}', `{{ p.description }}`, '{{ p.category_id }}', `{{ p.account_data }}`, '{{ p.stock }}')">កែ</button>
                    <form method="POST" style="display:inline;"><input type="hidden" name="action" value="delete"><input type="hidden" name="id" value="{{ p.id }}"><button type="submit" style="background:#f44336; padding:4px 8px;" onclick="return confirm('លុប?')">លុប</button></form>
                </td>
            </tr>
            {% endfor %}
        </table>
    </div>

    <!-- Edit Category Modal -->
    <div id="editCatModal" class="modal">
        <div class="modal-content" style="width: 320px;">
            <span onclick="document.getElementById('editCatModal').style.display='none'" style="float:right; cursor:pointer; font-size:20px;">&times;</span>
            <h3>✏️ កែប្រែឈ្មោះ Category</h3>
            <form method="POST">
                <input type="hidden" name="action" value="edit_category">
                <input type="hidden" name="category_id" id="ec-id">
                <label>ឈ្មោះថ្មី៖</label><input type="text" name="category_name" id="ec-name" required>
                <button type="submit" style="background:#ff9800; margin-top:10px;">រក្សាទុក</button>
            </form>
        </div>
    </div>

    <!-- Edit Product Modal -->
    <div id="editModal" class="modal">
        <div class="modal-content">
            <span onclick="document.getElementById('editModal').style.display='none'" style="float:right; cursor:pointer; font-size:20px;">&times;</span>
            <h3>✏️ កែប្រែព័ត៌មានទំនិញ</h3>
            <form method="POST" enctype="multipart/form-data">
                <input type="hidden" name="action" value="edit"><input type="hidden" name="id" id="e-id">
                <label>ឈ្មោះ៖</label><input type="text" name="name" id="e-name" required>
                <label>Category៖</label><select name="category_id" id="e-cat" required>{% for cat in categories %}<option value="{{ cat[0] }}">{{ cat[1] }}</option>{% endfor %}</select>
                <label>តម្លៃ ($)：</label><input type="number" step="0.01" name="price" id="e-price" required>
                <label>ពិពណ៌នា៖</label><textarea name="description" id="e-desc"></textarea>
                <label style="color:#d9534f; font-weight:bold;">បញ្ជី Account (១ បន្ទាត់ = ១ គណនី):</label><textarea name="account_data" id="e-acc" rows="5"></textarea>
                <label>រូបភាពថ្មី (បើមាន)៖</label><input type="file" name="image_file" accept="image/*">
                <button type="submit" style="background:#ff9800; margin-top:10px;">រក្សាទុក</button>
            </form>
        </div>
    </div>
    <script>
        function openEditCat(id, name) {
            document.getElementById('ec-id').value = id;
            document.getElementById('ec-name').value = name;
            document.getElementById('editCatModal').style.display = 'block';
        }
        function openEdit(id, name, price, desc, catId, accData, stock) {
            document.getElementById('e-id').value = id;
            document.getElementById('e-name').value = name;
            document.getElementById('e-price').value = price;
            document.getElementById('e-desc').value = desc;
            document.getElementById('e-cat').value = catId;
            document.getElementById('e-acc').value = accData;
            document.getElementById('editModal').style.display = 'block';
        }
    </script></body></html>""", categories=categories, products=products)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)