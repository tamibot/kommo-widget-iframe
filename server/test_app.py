"""Prueba de punta a punta sin salir a internet: Kommo se simula.

    createdb widget_kit
    DATABASE_URL=postgresql://localhost/widget_kit python test_app.py
"""
import os
import time
from unittest.mock import patch

from cryptography.fernet import Fernet

os.environ.setdefault("TOKEN_KEY", Fernet.generate_key().decode())
os.environ.setdefault("INTERNAL_KEY", "clave-interna-de-prueba")
from fastapi.testclient import TestClient  # noqa: E402

import app  # noqa: E402

CUENTA = "demo"


class KommoFalso:
    """Lead 1 existe; lead 2 fue borrado en Kommo (GET responde 204 → None)."""
    def __init__(self, db, cuenta, token, dominio="kommo.com"):
        self.cuenta, self.token, self.pedidos = cuenta, token, []

    def get(self, ruta, **_):
        self.pedidos.append(ruta)
        if self.token != "token-bueno":
            raise app.TokenRechazado("401")
        if ruta == "account":
            return {"subdomain": self.cuenta}
        if ruta == "leads/1":
            return LEAD
        return None

    def post(self, ruta, cuerpo):
        self.pedidos.append(ruta)
        assert ruta == "webhooks" and "delete_lead" in cuerpo["settings"]

    def paginar(self, ruta, **params):
        self.pedidos.append(ruta)
        if ruta == "leads":
            return [LEAD, {**LEAD, "id": 2, "name": "Lead que se borrará"}]
        if ruta == "contacts":
            return [{"id": 10, "name": "Ana Prueba", "updated_at": 1790000000,
                     "custom_fields_values": [{"field_code": "PHONE", "values": [{"value": "999 111 222"}]}]}]
        if ruta == "events":
            assert params["filter[type]"] == "lead_deleted"
            return [{"entity_id": 2}]
        return []


LEAD = {"id": 1, "name": "Lead de prueba", "pipeline_id": 5, "status_id": 50, "created_at": 1790000000,
        "updated_at": 1790000001, "_embedded": {"contacts": [{"id": 10}]}}


def limpiar():
    with app.db() as con:
        for t in ("sesiones", "leads", "contactos", "webhooks", "cuentas"):
            con.execute(f"delete from kw.{t} where true")
        con.execute("delete from kw.cuota where true")


def demo():
    limpiar()
    c = TestClient(app.app)
    with patch.object(app, "Kommo", KommoFalso):
        # Conectar: token malo no pasa; el bueno devuelve una clave y no queda en claro.
        assert c.post("/v1/conectar", json={"cuenta": CUENTA, "token": "malo"}).status_code == 400
        r = c.post("/v1/conectar", json={"cuenta": CUENTA, "token": "token-bueno"})
        assert r.status_code == 200, r.text
        clave = r.json()["clave"]
        with app.db() as con:
            guardado = con.execute("select token from kw.cuentas where cuenta=%s", (CUENTA,)).fetchone()[0]
            assert "token-bueno" not in guardado, "el token se guarda cifrado"
            assert con.execute("select count(*) from kw.leads").fetchone()[0] == 2, "carga inicial"

        # Ticket: sin clave no hay; con clave de ficha solo ve su lead.
        assert c.post("/v1/sesion", json={}).status_code == 403
        t = c.post("/v1/sesion", json={}, headers={"X-Widget-Clave": clave}).json()["ticket"]
        t_lead = c.post("/v1/sesion", json={"lead": 1}, headers={"X-Widget-Clave": clave}).json()["ticket"]
        assert c.get("/v1/embed/leads").status_code == 403
        todos = c.get("/v1/embed/leads", headers={"X-Ticket": t}).json()["leads"]
        assert {l["id"] for l in todos} == {1, 2} and todos[0]["telefono"] == "999 111 222"
        assert [l["id"] for l in c.get("/v1/embed/leads", headers={"X-Ticket": t_lead}).json()["leads"]] == [1]
        assert c.get("/v1/embed/leads?q=ana", headers={"X-Ticket": t}).json()["leads"]

        # Sincronizar: trae, saca el borrado y un segundo clic no vuelve a Kommo.
        assert c.post("/v1/embed/sincronizar", headers={"X-Ticket": t_lead}).status_code == 403
        r1 = c.post("/v1/embed/sincronizar", headers={"X-Ticket": t}).json()
        r2 = c.post("/v1/embed/sincronizar", headers={"X-Ticket": t}).json()
        assert r1["borrados"] == 1 and r2.get("reciente") is True, (r1, r2)
        with app.db() as con:
            assert [f[0] for f in con.execute("select id from kw.leads").fetchall()] == [1]

        # Webhook: se guarda antes de responder y un borrado solo sale si Kommo confirma.
        with app.db() as con:
            con.execute("insert into kw.leads (cuenta,id,nombre) values (%s,3,'Otro')", (CUENTA,))
        cuerpo = f"account%5Bsubdomain%5D={CUENTA}&leads%5Bdelete%5D%5B0%5D%5Bid%5D=3&leads%5Bupdate%5D%5B0%5D%5Bid%5D=1"
        assert c.post("/webhook", content=cuerpo,
                      headers={"Content-Type": "application/x-www-form-urlencoded"}).json() == {"ok": True}
        with app.db() as con:
            w = con.execute("select procesado, error from kw.webhooks").fetchone()
            assert w[0] and w[1] is None, w
            assert [f[0] for f in con.execute("select id from kw.leads order by id").fetchall()] == [1]

        # n8n: sin la clave interna la ruta no existe.
        assert c.get(f"/v1/interno/leads?cuenta={CUENTA}").status_code == 404
        filas = c.get(f"/v1/interno/leads?cuenta={CUENTA}", headers={"X-Interno": os.environ["INTERNAL_KEY"]}).json()
        assert filas[0]["KOMMO ID"] == 1

        # El iframe solo se deja enmarcar por Kommo.
        assert "frame-ancestors https://*.kommo.com" in c.get("/app").headers["Content-Security-Policy"]

    # Limitador compartido: el segundo turno inmediato espera; con freno, se corta.
    with app.db() as con:
        con.execute("update kw.cuota set techo=2, proximo=null, bloqueado_hasta=null")
        assert con.execute("select kw.turno('demo')").fetchone()[0] == 0
        assert con.execute("select kw.turno('demo')").fetchone()[0] > 0
        con.execute("select kw.frenar('demo', 60)")
        time.sleep(0.6)
        assert con.execute("select kw.turno('demo')").fetchone()[0] == -1
    limpiar()
    print("ok · conectar, ticket por ficha, iframe, sincronizar, webhooks con borrado, n8n y limitador")


if __name__ == "__main__":
    demo()
