from typing import NotRequired, Optional
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import Optional as WTFOptional, Length, EqualTo
from werkzeug.security import generate_password_hash, check_password_hash
from forms import LoginForm, RegistrationForm


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    
class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_name = db.Column(db.String(150), nullable=False)
    product_price = db.Column(db.Float, nullable=False)
    
    


class UpdateProfileForm(FlaskForm):
    username = StringField('نام کاربری', validators=[WTFOptional(), Length(min=2, max=20)])
    password = PasswordField('رمز عبور جدید', validators=[WTFOptional(), Length(min=6)])
    confirm_password = PasswordField('تایید رمز عبور', validators=[WTFOptional(), EqualTo('password')])
    submit = SubmitField('بروزرسانی')

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = UpdateProfileForm()
    if form.validate_on_submit():

        current_user.username = form.username.data
        

        if form.password.data:
            current_user.password = generate_password_hash(form.password.data)
        
        try:
            db.session.commit()
            flash('پروفایل شما با موفقیت بروزرسانی شد.', 'success')
            return redirect(url_for('dashboard'))
        except:
            db.session.rollback()
            flash('خطا در بروزرسانی پروفایل.', 'danger')
    

    form.username.data = current_user.username
    return render_template('profile.html', form=form)

@app.route('/delete_account', methods=['GET', 'POST'])
@login_required
def delete_account():
    if request.method == 'POST':
        try:
            Cart.query.filter_by(user_id=current_user.id).delete()
            
            
            db.session.delete(current_user)
            db.session.commit()
            
            flash('حساب کاربری شما با موفقیت حذف شد.', 'success')
            return redirect(url_for('index'))
        except:
            db.session.rollback()
            flash('خطا در حذف حساب کاربری.', 'danger')
    
    return render_template('delete_account.html')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.password == form.password.data:
            login_user(user)
            return redirect(url_for('dashboard'))
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, password=form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/dashboard')
@login_required  
def dashboard():

    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', cart_items=cart_items)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/add_to_cart', methods=['POST'])
@login_required
def add_to_cart():
    product_name = request.form.get('product_name')
    product_price = request.form.get('product_price')
    
    if product_name and product_price:
        try:
            product_price = float(product_price.replace(',', '').replace('تومان', '').strip())
            new_cart_item = Cart(
                user_id=current_user.id, 
                product_name=product_name, 
                product_price=product_price
            )
            db.session.add(new_cart_item)
            db.session.commit()
            flash('محصول به سبد خرید اضافه شد.', 'success')
        except ValueError:
            flash('خطا در اضافه کردن محصول.', 'danger')
    
    return redirect(url_for('index'))


@app.route('/remove_from_cart/<int:item_id>', methods=['POST'])
@login_required
def remove_from_cart(item_id):
    cart_item = Cart.query.get_or_404(item_id)
    

    if cart_item.user_id != current_user.id:
        flash('شما اجازه حذف این محصول را ندارید.', 'danger')
        return redirect(url_for('dashboard'))
    
    db.session.delete(cart_item)
    db.session.commit()
    flash('محصول از سبد خرید حذف شد.', 'success')
    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)