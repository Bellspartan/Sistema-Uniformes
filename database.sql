
DROP TABLE IF EXISTS productos;
DROP TABLE IF EXISTS ventas;

CREATE TABLE productos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    categoria TEXT NOT NULL,    -- Filipina / Pantalón
    modelo TEXT NOT NULL,       -- MAO / CLASICO V / Jogger / Recto
    genero TEXT NOT NULL,       -- Hombre / Mujer 
    talla TEXT NOT NULL,        -- XS / XXXL
    color TEXT NOT NULL,

    cantidad INTEGER NOT NULL,
    precio REAL NOT NULL,

    UNIQUE(categoria, modelo, genero, talla, color)
);

CREATE UNIQUE INDEX idx_producto_unico
ON productos (categoria,modelo, color, talla, genero);

CREATE TABLE ventas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    producto_id INTEGER,
    cantidad INTEGER,
    total REAL,
    fecha TEXT,
    FOREIGN KEY(producto_id) REFERENCES productos(id)
);
