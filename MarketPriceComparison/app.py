# app.py

from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_mysqldb import MySQL
from MySQLdb.cursors import DictCursor

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Berkay2002!'
app.config['MYSQL_DB'] = 'Project2'

mysql = MySQL(app)

@app.route("/products")
def products():
    # Bağlantı ve sorgu işlemleri
    cur = mysql.connection.cursor(DictCursor)
    cur.execute("""
        SELECT id, name, brand, size, description, category, image_url
        FROM products
        ORDER BY RAND()
        LIMIT 12;
    """)
    products = cur.fetchall()
    cur.close()
    # products.html şablonunu render et
    return render_template("products.html", data=products)


@app.route("/products_by_category")
def products_by_category():
    category = request.args.get('category')

    # Bağlantı ve sorgu işlemleri
    cur = mysql.connection.cursor(DictCursor)
    cur.execute("""
        SELECT id, name, brand, size, description, category, image_url
        FROM products
        WHERE category = %s
    """, (category,))
    products = cur.fetchall()
    cur.close()

    # products_by_category.html şablonunu render et
    return render_template("products_by_category.html", data=products)

@app.route("/product_detail/<int:product_id>")
def product_detail(product_id):
    # Bağlantı ve sorgu işlemleri
    cur = mysql.connection.cursor(DictCursor)
    cur.execute("""
        SELECT id, name, brand, size, description, category, image_url
        FROM products
        WHERE id = %s
    """, (product_id,))
    product = cur.fetchone()
    cur.close()

    # Eğer ürün bulunamazsa, 404 hatası döndür
    if not product:
        return "Product not found", 404

    # Ürün detay sayfasına yönlendir
    return redirect(url_for("product_detail_page", product_id=product_id))


@app.route("/product_detail_page/<int:product_id>")
def product_detail_page(product_id):
    # Bağlantı ve sorgu işlemleri
    cur = mysql.connection.cursor(DictCursor)
    cur.execute("""
        SELECT id, name, brand, size, description, category, image_url
        FROM products
        WHERE id = %s
    """, (product_id,))
    product = cur.fetchone()


    # Eğer ürün bulunamazsa, 404 hatası döndür
    if not product:
        return "Product not found", 404

    cur.execute("""
            SELECT markets.market_name, prices.price
            FROM prices
            JOIN markets ON prices.market_id = markets.market_id
            WHERE prices.id = %s;
        """, (product_id,))
    prices = cur.fetchall()
    cur.close()

    # product_detail.html şablonunu render et
    return render_template("product_detail.html", product=product, prices=prices)

@app.route("/add_to_favorites", methods=["POST"])
def add_to_favorites():
    # AJAX isteğiyle gelen veriyi alma
    data = request.get_json()
    product_id = data.get("product_id")

    # Favorilere eklenen ürünün daha önce eklenip eklenmediğini kontrol et
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM favorites WHERE product_id = %s", (product_id,))
    existing_favorite = cur.fetchone()

    # Eğer ürün zaten favorilere eklenmişse, tekrar eklememek için kontrol et
    if existing_favorite:
        return jsonify({"message": "The product already on the favorites."}), 400

    # Ürün favorilere eklenmemişse, eklemeyi gerçekleştir
    cur.execute("INSERT INTO favorites (product_id) VALUES (%s)", (product_id,))
    mysql.connection.commit()
    cur.close()

    return jsonify({"message": "The product added to favorites."}), 200

@app.route("/remove_from_favorites", methods=["POST"])
def remove_from_favorites():
    # AJAX isteğiyle gelen veriyi alma
    data = request.get_json()
    product_id = data.get("product_id")

    # Favorilerden kaldırma işlemini gerçekleştir
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM favorites WHERE product_id = %s", (product_id,))
    mysql.connection.commit()
    cur.close()

    return jsonify({"message": "The product removed from favorites."}), 200


@app.route("/favorites")
def favorites():
    # Bağlantı ve sorgu işlemleri
    cur = mysql.connection.cursor(DictCursor)
    cur.execute("""
        SELECT p.id, p.name, p.brand, p.size, p.description, p.category, p.image_url
        FROM products p
        JOIN favorites f ON p.id = f.product_id
    """)
    favorite_products = cur.fetchall()
    cur.close()

    # favorites.html şablonunu render et, favori ürünleri veri olarak gönder
    return render_template("favorites.html", favorite_products=favorite_products)

@app.route("/search")
def search():
    query = request.args.get('query')

    # Bağlantı ve sorgu işlemleri
    cur = mysql.connection.cursor(DictCursor)
    cur.execute("""
        SELECT id, name, brand, size, description, category, image_url
        FROM products
        WHERE name LIKE %s
    """, ('%' + query + '%',))
    search_results = cur.fetchall()
    cur.close()

    # search_results.html şablonunu render et, arama sonuçlarını veri olarak gönder
    return render_template("search_results.html", search_results=search_results)


@app.route("/add_to_cart", methods=["POST"])
def add_to_cart():
    # AJAX isteğiyle gelen veriyi alma
    data = request.get_json()
    product_id = data.get("product_id")

    # Sepete eklenen ürünü shopping_cart tablosuna ekleyelim
    cur = mysql.connection.cursor()

    # Ürün zaten kartta mı kontrol et
    cur.execute("SELECT * FROM shopping_cart WHERE product_id = %s", (product_id,))
    existing_product = cur.fetchone()

    if existing_product:
        cur.close()
        return jsonify({"message": "The product already on the cart."}), 400
    else:
        cur.execute("INSERT INTO shopping_cart (product_id) VALUES (%s)", (product_id,))
        mysql.connection.commit()
        cur.close()
        return jsonify({"message": "The product added to the cart"}), 200

@app.route("/remove_from_cart", methods=["POST"])
def remove_from_cart():
    # AJAX isteğiyle gelen veriyi alma
    data = request.get_json()
    product_id = data.get("product_id")

    # Ürünü karttan kaldırmak için
    cur = mysql.connection.cursor()

    # Ürün kartta mı kontrol et
    cur.execute("SELECT * FROM shopping_cart WHERE product_id = %s", (product_id,))
    existing_product = cur.fetchone()

    if existing_product:
        # Ürünü karttan kaldır
        cur.execute("DELETE FROM shopping_cart WHERE product_id = %s", (product_id,))
        mysql.connection.commit()
        cur.close()
        return jsonify({"message": "Your product has been removed."}), 200
    else:
        cur.close()
        return jsonify({"message": "The product is not already on the cart."}), 400



@app.route("/shopping_cart")
def shopping_cart():
    cur = mysql.connection.cursor(DictCursor)
    cur.execute("""
        SELECT p.id, p.name, p.brand, p.size, p.description, p.category, p.image_url,
               pr1.price as price1, pr2.price as price2, pr3.price as price3
        FROM shopping_cart sc
        JOIN products p ON sc.product_id = p.id
        JOIN prices pr1 ON p.id = pr1.id AND pr1.market_id = 1
        JOIN prices pr2 ON p.id = pr2.id AND pr2.market_id = 2
        JOIN prices pr3 ON p.id = pr3.id AND pr3.market_id = 3
    """)
    cart_items = cur.fetchall()
    cur.close()

    return render_template("shopping_cart.html", cart_items=cart_items)



if __name__ == "__main__":
    app.run(debug=True, port=5001)
