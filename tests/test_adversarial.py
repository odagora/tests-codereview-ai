"""Tests adversariales anclados a OWASP A03:2021-Injection.

Cubren la superficie real de busqueda de clientes en payments_svc.db:
- find_customer_by_email: concatena el email en el SQL (hallazgo de Semgrep).
- find_active_customers_by_country: ruta parametrizada, usada como control.
- count_customers_for_status: concatena pero con allowlist previa; se usa
  solo como comparacion adicional, no como endpoint.

Estos payloads estan documentados con objetivo, expectativa segura y razon
de riesgo en samples/security/adversarial-payload.json. Las expectativas
aqui reflejan el comportamiento SEGURO deseado, no lo que el codigo actual
hace: mientras la SQLi de find_customer_by_email siga abierta, los tests de
tautologia marcados como evidencia de riesgo deben FALLAR a proposito.
"""

from __future__ import annotations

import json
import sqlite3
import unittest
from pathlib import Path

from payments_svc.db import (
    count_customers_for_status,
    find_active_customers_by_country,
    find_customer_by_email,
)

PAYLOADS_PATH = (
    Path(__file__).resolve().parents[1]
    / "samples"
    / "security"
    / "adversarial-payload.json"
)


def _load_payloads() -> dict:
    with PAYLOADS_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def _payload_by_id(payload_id: str) -> dict:
    data = _load_payloads()
    for entry in data["payloads"]:
        if entry["id"] == payload_id:
            return entry
    raise KeyError(f"payload no encontrado en adversarial-payload.json: {payload_id}")


def _seed_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.execute(
        "CREATE TABLE customers ("
        "id TEXT PRIMARY KEY, "
        "email TEXT NOT NULL, "
        "status TEXT NOT NULL, "
        "country TEXT NOT NULL"
        ")"
    )
    connection.executemany(
        "INSERT INTO customers (id, email, status, country) VALUES (?, ?, ?, ?)",
        [
            ("cus_1", "alice@example.com", "active", "ES"),
            ("cus_2", "bob@example.com", "blocked", "ES"),
            ("cus_3", "carol@example.com", "active", "MX"),
            ("cus_4", "dave@example.com", "pending", "CO"),
            ("cus_5", "o'brien@example.com", "active", "IE"),
        ],
    )
    return connection


class TestFindCustomerByEmailSqlInjection(unittest.TestCase):
    """Payloads de inyeccion SQL contra la ruta vulnerable (concatenacion)."""

    def setUp(self) -> None:
        self.connection = _seed_connection()

    def tearDown(self) -> None:
        self.connection.close()

    def test_tautologia_sql_no_debe_devolver_cliente(self) -> None:
        """Caso obligatorio: payload de tautologia `' OR '1'='1`.

        Expectativa segura: find_customer_by_email("' OR '1'='1") NO es un
        email valido, por lo que debe devolver None. Hoy la funcion
        concatena el valor en el SQL y la tautologia hace que el WHERE
        coincida con toda la tabla, devolviendo el primer cliente (cus_1)
        sin que el atacante conociera su email real.

        Este test debe FALLAR mientras la SQLi este abierta: es la
        evidencia del riesgo, no un error de la suite. No se debe "arreglar"
        aceptando que devuelva un cliente.
        """
        entry = _payload_by_id("sqli-tautologia-comilla-simple")
        payload = entry["payload"]

        result = find_customer_by_email(self.connection, payload)

        self.assertIsNone(
            result,
            "find_customer_by_email devolvio un cliente con un payload que "
            f"no es un email valido ({payload!r}): {result!r}. Esto confirma "
            "la SQL injection detectada por Semgrep en find_customer_by_email "
            "(src/payments_svc/db.py). No conviertas este fallo en la "
            "expectativa aceptada: corrige la funcion para usar parametros.",
        )

    def test_tautologia_con_comentario_no_debe_devolver_cliente(self) -> None:
        entry = _payload_by_id("sqli-tautologia-comentario")
        result = find_customer_by_email(self.connection, entry["payload"])
        self.assertIsNone(result, f"payload {entry['id']} filtro un cliente: {result!r}")

    def test_prefijo_email_real_con_comentario_no_debe_devolver_cliente(self) -> None:
        """La entrada no es un email valido; no debe "colarse" como Alice."""
        entry = _payload_by_id("sqli-prefijo-email-real-truncado")
        result = find_customer_by_email(self.connection, entry["payload"])
        self.assertIsNone(
            result,
            "una entrada que no es un email valido no debe resolverse al "
            f"cliente real: {result!r} (payload {entry['id']})",
        )

    def test_condicion_sobre_status_no_debe_filtrar_por_atributo(self) -> None:
        entry = _payload_by_id("sqli-condicion-sobre-otra-columna")
        result = find_customer_by_email(self.connection, entry["payload"])
        self.assertIsNone(result, f"payload {entry['id']} filtro un cliente: {result!r}")

    def test_union_select_no_debe_elegir_fila_arbitraria(self) -> None:
        entry = _payload_by_id("sqli-union-select-otra-fila")
        result = find_customer_by_email(self.connection, entry["payload"])
        self.assertIsNone(result, f"payload {entry['id']} filtro un cliente: {result!r}")

    def test_union_select_no_debe_exponer_metadatos_del_esquema(self) -> None:
        entry = _payload_by_id("sqli-union-metadatos-esquema")
        result = find_customer_by_email(self.connection, entry["payload"])
        self.assertIsNone(
            result,
            f"payload {entry['id']} filtro metadatos del esquema: {result!r}",
        )

    def test_sentencias_apiladas_no_deben_alterar_la_tabla(self) -> None:
        """`'; DROP TABLE customers; --` no debe borrar datos.

        sqlite3 con execute() no permite multiples statements (lanza
        ProgrammingError), asi que este test no prueba que la inyeccion sea
        imposible en general; prueba que, con el driver actual, la tabla
        sigue intacta tras el intento.
        """
        entry = _payload_by_id("sqli-sentencias-apiladas")

        try:
            find_customer_by_email(self.connection, entry["payload"])
        except Exception:
            pass

        count = self.connection.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
        self.assertEqual(
            count,
            5,
            "la tabla customers perdio filas tras el payload de sentencias apiladas",
        )


class TestFindCustomerByEmailEntradasMalformadas(unittest.TestCase):
    """Entradas malformadas y de frontera contra find_customer_by_email."""

    def setUp(self) -> None:
        self.connection = _seed_connection()

    def tearDown(self) -> None:
        self.connection.close()

    def test_email_vacio_no_devuelve_cliente(self) -> None:
        entry = _payload_by_id("borde-email-vacio")
        self.assertIsNone(find_customer_by_email(self.connection, entry["payload"]))

    def test_email_solo_espacios_no_devuelve_cliente(self) -> None:
        entry = _payload_by_id("borde-email-solo-espacios")
        self.assertIsNone(find_customer_by_email(self.connection, entry["payload"]))

    def test_caracteres_de_control_no_devuelven_cliente(self) -> None:
        entry = _payload_by_id("borde-caracteres-control")
        self.assertIsNone(find_customer_by_email(self.connection, entry["payload"]))

    def test_apostrofe_en_email_legitimo_no_rompe_con_excepcion_cruda(self) -> None:
        """`o'brien@example.com` es un formato de email plausible.

        No es un ataque, pero con concatenacion de strings tambien rompe la
        consulta. Documentamos el comportamiento observado (excepcion de
        sintaxis SQL) como evidencia de que el problema no es solo de
        seguridad sino tambien de correctud funcional; no lo aceptamos como
        comportamiento deseado.
        """
        entry = _payload_by_id("sqli-apostrofe-nombre-legitimo")

        with self.assertRaises(
            sqlite3.OperationalError,
            msg=(
                "se esperaba que la concatenacion actual rompa con un email "
                "legitimo que contiene un apostrofe; si esto ya no lanza "
                "OperationalError, revisa si la funcion fue corregida para "
                "usar parametros y actualiza este test en consecuencia"
            ),
        ):
            find_customer_by_email(self.connection, entry["payload"])

    def test_byte_nul_no_debe_propagar_excepcion_cruda_del_driver(self) -> None:
        """NUL embebido: documenta el comportamiento observado hoy.

        No es un resultado deseable (deberia validarse antes de llegar al
        driver), pero se deja como evidencia explicita en vez de ocultarlo.
        """
        entry = _payload_by_id("borde-nul-byte")

        with self.assertRaises(sqlite3.ProgrammingError):
            find_customer_by_email(self.connection, entry["payload"])


class TestFindCustomerByEmailValoresDeFrontera(unittest.TestCase):
    """Strings largos para explorar ausencia de limites de tamano."""

    def setUp(self) -> None:
        self.connection = _seed_connection()

    def tearDown(self) -> None:
        self.connection.close()

    def test_string_largo_1000_no_devuelve_cliente(self) -> None:
        entry = _payload_by_id("borde-string-largo-1000")
        payload = "a" * entry["payload_len"]
        self.assertIsNone(find_customer_by_email(self.connection, payload))

    def test_string_largo_100000_no_devuelve_cliente(self) -> None:
        entry = _payload_by_id("borde-string-largo-100000")
        payload = "a" * entry["payload_len"]
        self.assertIsNone(find_customer_by_email(self.connection, payload))


class TestRutaParametrizadaComoControl(unittest.TestCase):
    """find_active_customers_by_country como control de comparacion segura.

    Caso obligatorio: un equivalente del payload de tautologia contra la
    ruta parametrizada, para contrastar el comportamiento seguro.
    """

    def setUp(self) -> None:
        self.connection = _seed_connection()

    def tearDown(self) -> None:
        self.connection.close()

    def test_tautologia_sql_contra_ruta_parametrizada_no_filtra_nada(self) -> None:
        entry = _payload_by_id("control-ruta-parametrizada-tautologia")

        result = find_active_customers_by_country(self.connection, entry["payload"])

        self.assertEqual(
            result,
            [],
            "la ruta parametrizada (placeholders '?') trata el payload como "
            "un valor literal de 'country'; no deberia devolver clientes",
        )

    def test_comilla_simple_contra_ruta_parametrizada_no_rompe(self) -> None:
        entry = _payload_by_id("control-ruta-parametrizada-comilla-simple")

        # A diferencia de find_customer_by_email, esto no debe lanzar
        # ninguna excepcion de sintaxis SQL.
        result = find_active_customers_by_country(self.connection, entry["payload"])

        self.assertEqual(result, [])


class TestCountCustomersForStatusConAllowlist(unittest.TestCase):
    """count_customers_for_status concatena, pero con allowlist previa.

    Se usa solo como punto de comparacion adicional (no es un endpoint de
    busqueda de clientes): la allowlist de status rechaza cualquier payload
    de inyeccion antes de construir el SQL.
    """

    def setUp(self) -> None:
        self.connection = _seed_connection()

    def tearDown(self) -> None:
        self.connection.close()

    def test_payload_de_inyeccion_es_rechazado_por_la_allowlist(self) -> None:
        with self.assertRaises(ValueError):
            count_customers_for_status(self.connection, "' OR '1'='1")

    def test_status_permitido_cuenta_correctamente(self) -> None:
        self.assertEqual(count_customers_for_status(self.connection, "active"), 3)


class TestSemillasXssYFuzzing(unittest.TestCase):
    """Semillas de XSS/fuzzing: no hay sumidero HTML en este repo.

    Se documentan como semillas reutilizables si en el futuro el valor de
    email se refleja en una respuesta HTTP o en logs HTML; hoy solo se
    valida que no generen un resultado de dominio incorrecto.
    """

    def setUp(self) -> None:
        self.connection = _seed_connection()

    def tearDown(self) -> None:
        self.connection.close()

    def test_seed_script_tag_no_devuelve_cliente(self) -> None:
        entry = _payload_by_id("xss-seed-script-tag")
        self.assertIsNone(find_customer_by_email(self.connection, entry["payload"]))

    def test_seed_metacaracteres_mixtos_no_propaga_excepcion_no_controlada(self) -> None:
        entry = _payload_by_id("fuzzing-seed-comillas-mixtas")
        try:
            result = find_customer_by_email(self.connection, entry["payload"])
        except sqlite3.OperationalError:
            # Documentado: con concatenacion, metacaracteres SQL rompen la
            # sintaxis. Se acepta como comportamiento observado, no deseado.
            return
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
