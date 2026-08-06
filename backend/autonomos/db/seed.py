"""First-run seed data (3.1) and the alias tables behind 9.3 / 9.7.

The alias lists are *data*, not code (R6): coverage improves by editing rows,
and every alias points at a category or method that already exists.
"""

from __future__ import annotations

import sqlite3

from ..clock import now_iso

SEED_CATEGORIES = [
    "Comida",
    "Transporte",
    "Mercado",
    "Servicios",
    "Salud",
    "Ocio",
    "Hogar",
    "Ropa",
    "Educación",
    "Otros",
]

SEED_PAYMENT_METHODS = [
    "Efectivo",
    "Tarjeta de crédito",
    "Tarjeta débito",
    "Transferencia",
    "Nequi",
    "Daviplata",
]

# Spanish lexicon: transcript phrase -> category name.
SEED_CATEGORY_ALIASES: dict[str, list[str]] = {
    "Transporte": [
        "uber", "taxi", "bus", "buseta", "gasolina", "combustible", "transmilenio",
        "didi", "indriver", "cabify", "peaje", "parqueadero", "metro", "pasaje",
        "pasajes", "transporte", "moto", "sitp", "acpm", "tanqueada", "tanquear",
    ],
    "Comida": [
        "almuerzo", "almorzar", "comida", "cafe", "café", "restaurante", "desayuno",
        "cena", "domicilio", "rappi", "pizza", "hamburguesa", "empanada", "helado",
        "panaderia", "panadería", "tinto", "onces", "sandwich", "sánduche", "corrientazo",
        "menu del dia", "comer", "almorce", "almorcé", "cene", "cené",
    ],
    "Mercado": [
        "mercado", "supermercado", "exito", "éxito", "d1", "ara", "jumbo", "carulla",
        "olimpica", "olímpica", "plaza de mercado", "frutas", "verduras", "tienda",
        "makro", "surtimax", "granero",
    ],
    "Servicios": [
        "servicios", "luz", "agua", "gas", "internet", "telefono", "teléfono",
        "celular", "recibo", "factura", "energia", "energía", "netflix", "spotify",
        "suscripcion", "suscripción", "plan de datos", "recarga", "acueducto",
    ],
    "Salud": [
        "salud", "farmacia", "drogueria", "droguería", "medico", "médico", "medicina",
        "medicamento", "eps", "odontologo", "odontólogo", "examen", "consulta",
        "cruz verde", "laboratorio",
    ],
    "Ocio": [
        "ocio", "cine", "bar", "cerveza", "fiesta", "concierto", "salida", "juego",
        "videojuego", "trago", "tragos", "rumba", "paseo", "parque", "teatro",
        "netflix y cine", "billar",
    ],
    "Hogar": [
        "hogar", "casa", "arriendo", "muebles", "ferreteria", "ferretería", "aseo",
        "decoracion", "decoración", "reparacion", "reparación", "cocina", "administracion",
        "administración", "colchon", "colchón",
    ],
    "Ropa": [
        "ropa", "camisa", "camiseta", "pantalon", "pantalón", "zapatos", "tenis",
        "chaqueta", "vestido", "medias", "ropa interior", "gorra", "buzo",
    ],
    "Educación": [
        "educacion", "educación", "curso", "libro", "libros", "universidad",
        "matricula", "matrícula", "clase", "semestre", "taller", "diplomado",
        "cuaderno", "papeleria", "papelería",
    ],
    "Otros": ["otros", "varios", "otra cosa"],
}

# Everyday Spanish for how the spend was paid (9.7).
SEED_PAYMENT_METHOD_ALIASES: dict[str, list[str]] = {
    "Efectivo": [
        "efectivo", "en efectivo", "plata", "en plata", "cash", "billetes",
        "de contado", "contado", "monedas", "en billetes",
    ],
    "Tarjeta de crédito": [
        "tarjeta de credito", "tarjeta de crédito", "con la tarjeta de credito",
        "con la tarjeta de crédito", "credito", "crédito", "a credito", "a crédito",
        "con credito", "con crédito", "tarjeta credito", "tarjeta crédito",
        "visa", "mastercard", "amex", "tc",
    ],
    "Tarjeta débito": [
        "tarjeta debito", "tarjeta débito", "tarjeta de debito", "tarjeta de débito",
        "con la tarjeta debito", "con la tarjeta débito", "debito", "débito",
        "con debito", "con débito",
    ],
    "Transferencia": [
        "transferencia", "transferi", "transferí", "por transferencia", "pse",
        "consignacion", "consignación", "consigne", "consigné", "bancolombia",
        "davivienda", "banco",
    ],
    "Nequi": ["nequi", "por nequi", "con nequi", "en nequi"],
    "Daviplata": ["daviplata", "por daviplata", "con daviplata", "en daviplata"],
}


def seed_if_empty(conn: sqlite3.Connection) -> None:
    """Populate starter lists and aliases when the tables are empty (3.1)."""
    ts = now_iso()
    have_categories = conn.execute("SELECT COUNT(*) c FROM categories").fetchone()["c"]
    if not have_categories:
        for order, name in enumerate(SEED_CATEGORIES):
            conn.execute(
                "INSERT INTO categories(name, sort_order, created_at) VALUES(?,?,?)",
                (name, order, ts),
            )
    have_methods = conn.execute("SELECT COUNT(*) c FROM payment_methods").fetchone()["c"]
    if not have_methods:
        for order, name in enumerate(SEED_PAYMENT_METHODS):
            conn.execute(
                "INSERT INTO payment_methods(name, sort_order, created_at) VALUES(?,?,?)",
                (name, order, ts),
            )

    _seed_aliases(conn, "categories", "category_aliases", SEED_CATEGORY_ALIASES)
    _seed_aliases(
        conn, "payment_methods", "payment_method_aliases", SEED_PAYMENT_METHOD_ALIASES
    )


def _seed_aliases(
    conn: sqlite3.Connection,
    target_table: str,
    alias_table: str,
    aliases: dict[str, list[str]],
) -> None:
    if conn.execute(f"SELECT COUNT(*) c FROM {alias_table}").fetchone()["c"]:
        return
    for target_name, words in aliases.items():
        row = conn.execute(
            f"SELECT id FROM {target_table} WHERE name = ?", (target_name,)
        ).fetchone()
        if row is None:
            continue
        for word in words:
            conn.execute(
                f"INSERT OR IGNORE INTO {alias_table}(target_id, alias) VALUES(?,?)",
                (row["id"], word),
            )
