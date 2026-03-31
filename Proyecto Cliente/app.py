from flask import Flask, render_template, request, redirect
import sqlite3
import os
from datetime import datetime
from collections import defaultdict
from flask import url_for

app = Flask(__name__)

# Conexión DB
def get_db():
    conn = sqlite3.connect("/tmp/inventario.db")
    conn.row_factory = sqlite3.Row
    return conn

# Crear DB automaticamente
def init_db():
    conn = get_db()
    with open("database.sql", "r") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()

STOCK_MINIMO = 5
# Ruta principal
@app.route("/")
def index():
    conn = get_db()
    productos = conn.execute("SELECT * FROM productos").fetchall()

    catalogo = defaultdict(lambda: defaultdict(list))

    for p in productos:
        clave = f"{p['color']} {p['genero']}"
        modelo = f"{p['categoria']} {p['modelo']}"

        catalogo[clave][modelo].append(p)
    
    ganancia_total = conn.execute("""
            SELECT SUM(total) as total FROM ventas
        """).fetchone()["total"]

    ganancia_total = ganancia_total if ganancia_total else 0


    # MÉTRICAS
    total_productos = len(productos)
    total_stock = sum([p["cantidad"] for p in productos])
    stock_bajo = len([p for p in productos if p["cantidad"] <= STOCK_MINIMO])
    stock_bueno = len([p for p in productos if p["cantidad"] > STOCK_MINIMO])

    conn.close()

    return render_template(
        "index.html",
        productos=productos,
        minimo=STOCK_MINIMO,
        total_productos=total_productos,
        total_stock=total_stock,
        stock_bajo=stock_bajo,
        stock_bueno=stock_bueno,
        catalogo=catalogo,
        ganancia_total=ganancia_total
    )

@app.route("/dashboard")
def dashboard():
    conn = get_db()
    
    # Ventas por día
    ventas_dia = conn.execute("""
        SELECT fecha, SUM(cantidad) as total
        FROM ventas
        GROUP BY fecha
        ORDER BY fecha
        """).fetchall()
    
    fechas = [v["fecha"] for v in ventas_dia]
    totales = [v["total"] for v in ventas_dia]

    # Ganancias por día
    ganancia_dia = conn.execute("""
        SELECT fecha, SUM(total) as total
        FROM ventas
        GROUP BY fecha
        ORDER BY fecha
    """).fetchall()

    fechas_ganancia = [g["fecha"] for g in ganancia_dia]
    totales_ganancia = [g["total"] for g in ganancia_dia]

    # Top productos
    top_productos = conn.execute("""
        SELECT
            p.categoria,
            p.modelo,
            p.color,
            SUM(v.cantidad) as total
        FROM ventas v
        JOIN productos p ON v.producto_id = p.id
        GROUP BY p.id
        ORDER BY total DESC
        LIMIT 5
    """).fetchall() 

    labels_top = [
        f"{p['categoria']} {p['modelo']} {p['color']}"
        for p in top_productos
    ]
    valores_top = [p["total"] for p in top_productos]

    conn.close()

    return render_template(
        "dashboard.html",
        fechas=fechas,
        totales=totales,
        fechas_ganancia=fechas_ganancia,
        totales_ganancia=totales_ganancia,
        labels_top=labels_top,
        valores_top=valores_top
    )

# Agregar producto
@app.route("/agregar", methods=["POST"])
def agregar():
    categoria = request.form["categoria"].strip().lower()
    modelo = request.form["modelo"].strip().lower()
    genero = request.form["genero"].strip().lower()
    talla = request.form["talla"].strip().lower()
    color = request.form["color"].strip().lower()
    cantidad = int(request.form["cantidad"])
    precio = float(request.form["precio"])

    conn = get_db()
    
    # Buscar si ya existe el producto
    producto = conn.execute("""
        SELECT id, cantidad FROM productos
        WHERE categoria = ? AND modelo = ? AND genero = ? AND talla = ? AND color = ?
    """, (categoria, modelo, genero, talla, color)).fetchone()

    if producto:
        # Si existe -> sumar stock
        nueva_cantidad = producto["cantidad"] + cantidad

        conn.execute("""
            UPDATE productos
            SET cantidad = ?
            WHERE id = ?
        """, (nueva_cantidad, producto["id"]))

    else:
        # Si no existe -> crear nuevo
        conn.execute("""
            INSERT INTO productos (categoria, modelo, genero, talla, color, cantidad, precio)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (categoria, modelo, genero, talla, color, cantidad, precio))
        
        print("AGREGANDO PRODUCTO:", categoria, modelo, genero, talla, cantidad, precio)
    conn.commit()
    conn.close()
    
    return redirect(url_for("index"))

# Venta (descontar stock)
@app.route("/vender/<int:id>", methods=["POST"])
def vender(id):
    conn = get_db()

    producto = conn.execute("""
        SELECT cantidad, precio FROM productos WHERE id =  ?
    """, (id,)).fetchone()
    
    if producto["cantidad"] > 0:

        # Descontar stock
        conn.execute("""
            UPDATE productos
            SET cantidad = cantidad - 1 
            WHERE id = ?
        """, (id,))

        total_venta = producto["precio"]

        # Registrar venta con dinero
        conn.execute("""
            INSERT INTO ventas (producto_id, cantidad, total, fecha)
            VALUES (?, ?, ?, ?)
        """, (id, 1, total_venta, datetime.now().strftime("%Y-%m-%d")))

        conn.commit()

    conn.close()
    return redirect("/")

# Eliminar producto
@app.route("/eliminar/<int:id>", methods=["POST"])
def eliminar(id):
    conn = get_db()
    conn.execute("DELETE FROM productos WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect("/")

if __name__ == "__main__":
    if not os.path.exists("inventario.db"):
        init_db()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)