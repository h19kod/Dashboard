import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Order

# 1. إعداد المسارات المطلقة لضمان عمل قاعدة البيانات في أي مكان
base_dir = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(base_dir, 'templates')

app = Flask(__name__, template_folder=template_dir)

# 2. إعدادات الحماية وقاعدة البيانات
app.config['SECRET_KEY'] = 'professional-secure-key-2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(base_dir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 3. ربط SQLAlchemy بالتطبيق
db.init_app(app)

# 4. إعداد نظام إدارة الجلسات (Login Manager)
login_manager = LoginManager()
login_manager.login_view = 'login'  # توجيه المستخدم لصفحة الدخول إذا لم يسجل
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 5. تهيئة قاعدة البيانات عند التشغيل (Database Initialization)
with app.app_context():
    db.create_all()
    # إنشاء مستخدم أدمن افتراضي إذا لم يكن موجوداً
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', email='admin@pro.com')
        admin.set_password('123456')  # تشفير الباسوورد
        db.session.add(admin)
        db.session.commit()
        print("✅ تم إنشاء قاعدة البيانات وحساب المدير الافتراضي!")

# --- المسارات البرمجية (Routes) ---

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and user.check_password(request.form.get('password')):
            login_user(user)
            flash('أهلاً بك مجدداً!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('بيانات الدخول غير صحيحة ❌', 'danger')
            
    return render_template('login.html')

@app.route("/")
@app.route("/dashboard")
@login_required
def dashboard():
    # منطق البحث بالاسم
    search_query = request.args.get('search', '')
    
    u_count = User.query.count()
    o_count = Order.query.count()
    
    if search_query:
        orders = Order.query.filter(Order.product_name.contains(search_query)).all()
    else:
        orders = Order.query.order_by(Order.date_posted.desc()).all()
        
    return render_template('dashboard.html', u_count=u_count, o_count=o_count, orders=orders, search_query=search_query)

@app.route("/add_order", methods=['GET', 'POST'])
@login_required
def add_order():
    if request.method == 'POST':
        name = request.form.get('product_name')
        price = request.form.get('amount')
        if name and price:
            new_order = Order(product_name=name, amount=float(price))
            db.session.add(new_order)
            db.session.commit()
            flash('تمت إضافة الطلب بنجاح ✅', 'success')
            return redirect(url_for('dashboard'))
    return render_template('add_order.html')

@app.route("/delete_order/<int:order_id>")
@login_required
def delete_order(order_id):
    order = Order.query.get_or_404(order_id)
    db.session.delete(order)
    db.session.commit()
    flash('تم حذف السجل بنجاح 🗑️', 'danger')
    return redirect(url_for('dashboard'))

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)