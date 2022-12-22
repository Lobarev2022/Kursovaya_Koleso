from flask import Flask, render_template, url_for, request, flash, session, redirect
import psycopg2
import psycopg2.extras
import re
from werkzeug.security import generate_password_hash, check_password_hash
from config import DB_NAME, DB_USER, DB_PASS, DB_HOST, DB_PORT

app = Flask(__name__)
app.secret_key = 'kotiki_klassnie'

try:
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT)
except:
    print('Not your day')


@app.route('/')
def home():
    if 'loggedin' in session:
        return render_template('home.html', username=session['user_name'])
    return redirect(url_for('login'))


@app.route('/login/', methods=['GET', 'POST'])
def login():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        user_login = request.form['username']
        password = request.form['password']

        cursor.execute('SELECT * FROM user_db WHERE user_login = %s', (user_login,))
        account = cursor.fetchone()
        if account:
            password_rs = account['user_password']
            # If account exists in users table in out database
            if check_password_hash(password_rs, password):
                # Create session data, we can access this data in other routes
                session['loggedin'] = True
                session['user_login'] = account['user_login']
                session['user_name'] = account['user_name']
                if user_login.lower() == 'admin':
                    session['isadmin'] = True
                else:
                    session['isadmin'] = False
                cursor.execute('SELECT user_id FROM user_db WHERE user_login = %s', (user_login,))
                user_id = cursor.fetchone()[0]
                session['user_id'] = user_id
                # Redirect to home page
                return redirect(url_for('home'))
            else:
                # Account doesnt exist or username/password incorrect
                flash('Incorrect username/password')
        else:
            # Account doesnt exist or username/password incorrect
            flash('Incorrect username/password')

    elif request.method == 'POST':
        flash('Please fill out the form!')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        fullname = request.form['fullname']
        user_login = request.form['username']
        password = request.form['password']
        phone_number = request.form['phone_number']
        _hashed_password = generate_password_hash(password)

        # Check if account exists using PostgreSQL
        cursor.execute('SELECT * FROM user_db WHERE user_login = %s', (user_login,))
        account = cursor.fetchone()

        # If account exists show error and validation checks
        if account:
            flash('Аккаунт уже создан!')
        elif not re.match(r'[A-Za-z0-9]+', user_login):
            flash('Только цифры и буквы!')
        elif not re.match(r'[0-9]+', phone_number):
            flash('В номере только цифры! (без +)')
        elif not user_login or not password or not fullname or not phone_number:
            flash('Please fill out the form!')
        else:
            if user_login.lower() == 'admin':
                cursor.execute(
                    "INSERT INTO user_db (user_login, user_password, user_name, phone_number, user_role) VALUES (%s,%s,%s, %s, %s)",
                    (user_login, _hashed_password, fullname, phone_number, 'admin'))
                conn.commit()
            else:
                cursor.execute("INSERT INTO user_db (user_login, user_password, user_name, phone_number) VALUES (%s,%s,%s, %s)",
                               (user_login, _hashed_password, fullname, phone_number))
                conn.commit()
            return redirect(url_for('login'))

    elif request.method == 'POST':
        flash('Please fill out the form!')

    return render_template('register.html')


@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
    session.clear()
    return redirect(url_for('login'))


@app.route('/profile')
def profile():
    if 'loggedin' in session:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute('SELECT user_login, user_name FROM user_db WHERE user_id = %s', (session['user_id'], ))
        account = cursor.fetchone()
        cursor.execute('SELECT amount FROM order_food WHERE user_id = %s', (session['user_id'],))
        spend_money = cursor.fetchall()
        count = len(spend_money)
        sum = 0
        for money in spend_money:
            sum += money[0]
        return render_template('profile.html', account=account, sum=sum, count=count)
    return redirect(url_for('login'))


@app.route('/products_categories', methods=['GET', 'POST'])
def products_categories():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if request.method == 'POST':
        if (request.form.get('name', None)):
            category_name = request.form['name']
            category_name = '%' + category_name + '%'
            cursor.execute('SELECT * FROM category WHERE category_name ILIKE %s',
                           (category_name, ))
            categories = cursor.fetchall()
        elif (request.form.get('category', None)):
            category_name = request.form['category']
            cursor.execute(
                "INSERT INTO category (category_name) VALUES (%s) ",
                (category_name, ))
            conn.commit()
        else:
            cursor.execute('SELECT * FROM category')
            categories = cursor.fetchall()
    else:
        cursor.execute('SELECT * FROM category')
        categories = cursor.fetchall()

    return render_template('products_categories.html', categories=categories, admin=session['isadmin'])


@app.route('/products_in_category/<int:id>', methods=['GET', 'POST'])
def products_in_category(id):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if request.method == 'POST':
        if (request.form.get('name', None)):
            product_name = request.form['name']
            cursor.execute('SELECT product_id FROM product WHERE product_name = %s',
                           (product_name, ))
            product_id = cursor.fetchone()
            if product_id is not None:
                product_id = product_id[0]
                return redirect(url_for('product_card', id=product_id))
        else:
            all_data = list()
            all_data.append(request.form.get('manufacturer', None))
            all_data.append(request.form.get('country', None))
            all_data.append(request.form.get('price', None))
            all_data.append(request.form.get('product_name', None))
            sum = 0
            for data in all_data:
                if data:
                    sum += 1
            if sum == 0:
                pass
            elif sum == 4:
                price = request.form['price']
                if not re.match(r'[0-9]+', price):
                    flash('Цена целое число', category='error')
                else:
                    manufacturer = request.form['manufacturer']
                    country = request.form['country']
                    product_name = request.form['product_name']
                    cursor.execute(
                        "INSERT INTO product (category_id, manufacturer, country, price, product_name) VALUES (%s, %s, "
                        "%s, %s, %s)",
                        (id, manufacturer, country, price, product_name))
                    conn.commit()
            else:
                flash('Введите все данные продукта', category='error')

    cursor.execute('SELECT product_id, product_name FROM product WHERE category_id = %s', (id, ))
    products = cursor.fetchall()
    return render_template('products_in_category.html', products=products, admin=session['isadmin'])


@app.route('/product_card/<int:id>', methods=['GET', 'POST'])
def product_card(id):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if request.method == 'POST':
        if (request.form.get('new_name', None)):
            new_name = request.form['new_name']
            cursor.execute(
                "UPDATE product SET product_name = %s WHERE product_id = %s ",
                (new_name, id))
            conn.commit()

    cursor.execute('SELECT product_name, manufacturer, country, price FROM product WHERE product_id = %s', (id, ))
    product_info = cursor.fetchone()
    cursor.execute('SELECT product_rate FROM product_rating WHERE product_id = %s', (id, ))
    product_rate = cursor.fetchall()
    if not product_rate:
        product_rate = 'Никем не оценен'
    else:
        value = 0
        for rate in product_rate:
            value += rate[0]
        value /= len(product_rate)
        product_rate = value
    return render_template('product_card.html', product_info=product_info, id=id, product_rate=product_rate
                           ,admin=session['isadmin'])


@app.route('/add_to_cart/<int:id>')
def add_to_cart(id):
    if 'loggedin' in session:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute(
            "SELECT user_id FROM product_cart WHERE product_id = %s ",
            (id, ))
        user_id = cursor.fetchone()
        if user_id is None or user_id[0] != session['user_id']:
            cursor.execute(
                "INSERT INTO product_cart (user_id, product_id) VALUES (%s, %s) ",
                (session['user_id'], id))
            conn.commit()
            return redirect(url_for('cart'))
        else:
            flash('В корзине уже есть такой товар :)', category='error')
            return redirect(url_for('product_card', id=id))

    return redirect(url_for('login'))


@app.route('/cart', methods=['GET', 'POST'])
def cart():
    if 'loggedin' in session:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute('SELECT product_id FROM product_cart WHERE user_id = %s', (session['user_id'],))
        product_id = cursor.fetchall()

        if request.method == 'POST':
            if (request.form.get('order', None)):
                if session['total_amount'] != 0:
                    cursor.execute('INSERT INTO order_food (amount, order_date, user_id) VALUES (%s, LOCALTIMESTAMP, %s)'
                                   'RETURNING order_id',
                                   (session['total_amount'], session['user_id']))
                    order_id = cursor.fetchone()[0]
                    conn.commit()
                    for id in product_id:
                        id = id[0]
                        cursor.execute('INSERT INTO product_in_order (product_id, order_id) VALUES (%s, %s)',
                                       (id, order_id))
                        cursor.execute(
                            "DELETE FROM product_cart WHERE product_id = %s",
                            (id,))
                        conn.commit()
                    return redirect(url_for('orders'))
                else:
                    flash('В корзине пусто', category='error')

        products = list()
        total_amount = 0
        for id in product_id:
            cursor.execute('SELECT product_name, price FROM product WHERE product_id = %s', (id[0],))
            product_id = cursor.fetchone()
            product_id.append(id[0])
            total_amount += product_id[1]
            products.append(product_id)

        session['total_amount'] = total_amount
        return render_template('cart.html', products=products, total_amount=total_amount)
    return redirect(url_for('login'))


@app.route('/delete_from_cart/<int:id>', methods=['GET', 'POST'])
def delete_from_cart(id):
    if 'loggedin' in session:
        if request.method == 'POST':
            if (request.form.get('yes', None)):
                cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                cursor.execute(
                    "DELETE FROM product_cart WHERE product_id = %s",
                    (id,))
                conn.commit()
            return redirect(url_for('cart'))
        return render_template('delete_from_cart.html')
    return redirect(url_for('login'))


#здесь информация о заказе и возможность удаления заказа
@app.route('/delete_order/<int:id>/<string:status>', methods=['GET', 'POST'])
def delete_order(id, status):
    if 'loggedin' in session:
        if request.method == 'POST':
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            if (request.form.get('yes', None)):
                cursor.execute(
                    "DELETE FROM product_in_order WHERE order_id = %s",
                    (id,))
                conn.commit()
                cursor.execute(
                    "DELETE FROM order_food WHERE order_id = %s",
                    (id,))
                conn.commit()
            elif (request.form.get('products', None)):
                cursor.execute('SELECT product_id FROM product_in_order WHERE order_id = %s',
                               (id,))
                products_id = cursor.fetchall()
                products_info = list()
                for product_id in products_id:
                    product_id = product_id[0]
                    cursor.execute('SELECT manufacturer, country, price, product_name, product_id FROM product WHERE product_id = %s',
                                   (product_id,))
                    products_info.append(cursor.fetchone())
                return render_template('products_info.html', products_info=products_info, status=status)

            return redirect(url_for('orders'))
        return render_template('delete_order.html', status=status)
    return redirect(url_for('login'))

@app.route('/rate_item/<int:id>', methods=['GET', 'POST'])
def rate(id):
    if 'loggedin' in session:
        if request.method == 'POST':
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            rating = request.form['rating']
            if rating == 'Оценить продукт':
                 flash('Выберите рейтинг!', category='error')
            else:
                cursor.execute("SELECT EXISTS (SELECT * FROM product_rating WHERE product_id = %s AND user_id = %s)",
                                (id, session['user_id']))
                alreadyrated = cursor.fetchone()  #true/false
                if alreadyrated[0]:
                    flash('Вы уже оценили этот продукт!', category='error')
                else:
                    cursor.execute(
                         "INSERT INTO product_rating (product_id, user_id, product_rate) VALUES (%s, %s, %s) ",
                         (id,  session['user_id'], rating))
                    conn.commit()
                    return redirect(url_for('orders'))

        return render_template('rate_product.html', id=id)
    return redirect(url_for('login'))


@app.route('/orders', methods=['GET', 'POST'])
def orders():
    if 'loggedin' in session:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        # через минуту после заказа статус меняется на доставлено и можно сделать оценку товара
        #
        #
        cursor.execute("SELECT order_id FROM  order_food WHERE LOCALTIMESTAMP - INTERVAL '1 MINUTES' > order_date AND"
                       " user_id = %s", (session['user_id'],))
        delivered_id = cursor.fetchall()
        if delivered_id is not None:
            for id in delivered_id:
                id = id[0]
                cursor.execute(
                    "UPDATE order_food SET status = %s WHERE order_id = %s ",
                    ('Delivered', id))
                conn.commit()
        #
        #
        cursor.execute('SELECT status, amount, order_date, order_id FROM order_food WHERE user_id = %s'
                       , (session['user_id'], ))
        orders = cursor.fetchall()
        return render_template('orders.html', orders=orders)
    return redirect(url_for('login'))


if __name__ == "__main__":
    app.run(debug=True)