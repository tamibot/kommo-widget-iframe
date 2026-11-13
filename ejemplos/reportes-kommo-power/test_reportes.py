"""Prueba del dashboard con datos inventados, sin Kommo ni Kommo Power.

    DATABASE_URL=postgresql://localhost/widget_kit python ejemplos/reportes-kommo-power/test_reportes.py
    ... test_reportes.py --vista 4500     # deja la página corriendo con datos de ejemplo
"""
import datetime as dt
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

from cryptography.fernet import Fernet

AQUI = Path(__file__).parent
sys.path[:0] = [str(AQUI), str(AQUI.parents[1] / "server")]
os.chdir(AQUI.parents[1] / "server")
os.environ.setdefault("TOKEN_KEY", Fernet.generate_key().decode())
from fastapi.testclient import TestClient  # noqa: E402

import app as kit  # noqa: E402
import reportes  # noqa: E402
import test_app  # noqa: E402

kit.app.include_router(reportes.router)
C = "demo"


def sembrar():
    """Tablas mínimas de Kommo Power (las reales las crea su db/001_schema.sql) y 60 días de chats."""
    with kit.db() as con:
        con.execute((AQUI / "tablas_kommo_power_prueba.sql").read_text(encoding="utf-8"))
        for t in ("chats", "leads", "contacts"):
            con.execute(f"delete from kommo.{t} where account=%s", (C,))
        hoy = dt.date.today()
        lead = 1000
        for d in range(60):
            dia = hoy - dt.timedelta(days=d)
            for j in range(3 + d % 5):
                lead += 1
                humano = j % 3 != 0
                sin_resp = j % 7 == 6
                inicio = dt.datetime.combine(dia, dt.time(9 + j % 8, 0), dt.timezone.utc)
                con.execute("""insert into kommo.chats (account, lead_id, talk_id, contact_id, channel, chat_date, msg_count,
                                 in_count, out_count, bot_count, human_count, has_human_response, no_reply, human_agents,
                                 first_contact_at, first_human_at, referral, scraped_at)
                               values (%s,%s,1,%s,%s,%s,8,4,%s,%s,%s,%s,%s,%s,%s,%s,%s, now())""",
                            (C, lead, lead, ("waba", "instagram_business", "facebook")[j % 3], dia,
                             0 if sin_resp else 4, 0 if sin_resp else 2, 2 if humano and not sin_resp else 0, humano and not sin_resp, sin_resp,
                             ["Ana", "Luis"][j % 2:j % 2 + 1] if humano and not sin_resp else [],
                             inicio, inicio + dt.timedelta(minutes=5 + j * 3) if humano and not sin_resp else None,
                             json.dumps({"headline": "Promo noviembre"}) if j % 4 == 0 else None))
                con.execute("insert into kommo.contacts (account, contact_id, name) values (%s,%s,%s)",
                            (C, lead, f"Contacto {lead}"))
                con.execute("""insert into kommo.leads (account, lead_id, contact_id, pipeline_name, status_name, lead_created_at)
                               values (%s,%s,%s,'Ventas',%s,%s)""",
                            (C, lead, lead, ("Nuevo", "En conversación", "Cita agendada")[j % 3], inicio))


def ticket(c, lead=None):
    with patch.object(kit, "Kommo", test_app.KommoFalso):
        clave = c.post("/v1/conectar", json={"cuenta": C, "token": "token-bueno"}).json()["clave"]
        return c.post("/v1/sesion", json={"lead": lead} if lead else {}, headers={"X-Widget-Clave": clave}).json()["ticket"]


def demo():
    test_app.limpiar()
    sembrar()
    c = TestClient(kit.app)
    t = ticket(c)
    assert c.get("/v1/embed/reportes").status_code == 403, "sin ticket no hay datos"
    assert c.get("/v1/embed/reportes", headers={"X-Ticket": ticket(c, 1001)}).status_code == 403, "la ficha no ve el dashboard"
    r = c.get("/v1/embed/reportes?dias=30", headers={"X-Ticket": t}).json()
    k = r["kpis"]
    assert len(r["diario"]) == 30 and k["conversaciones"] == sum(d["conversaciones"] for d in r["diario"]), r["diario"][:2]
    assert k["con_humano"] + k["solo_bot"] + k["sin_respuesta"] <= k["conversaciones"]
    assert k["mediana_primera_respuesta_min"] is not None and r["datos_viejos"] is False
    assert {x["canal"] for x in r["canales"]} == {"waba", "instagram_business", "facebook"}
    assert r["agentes"][0]["agente"] in ("Ana", "Luis") and r["anuncios"][0]["anuncio"] == "Promo noviembre"
    assert r["sin_respuesta"] and r["sin_respuesta"][0]["url"].startswith("https://demo.kommo.com/leads/detail/")
    assert len(c.get("/v1/embed/reportes?dias=7", headers={"X-Ticket": t}).json()["diario"]) == 7
    assert "frame-ancestors https://*.kommo.com" in c.get("/reportes").headers["Content-Security-Policy"]
    # Si Kommo Power deja de bajar datos, la página lo avisa (canario).
    with kit.db() as con:
        con.execute("update kommo.chats set scraped_at = now() - interval '3 days' where account=%s", (C,))
    assert c.get("/v1/embed/reportes", headers={"X-Ticket": t}).json()["datos_viejos"] is True
    print("ok · KPIs, por día, canales, agentes, anuncios, embudo, sin respuesta, permisos y aviso de datos viejos")
    return t


if __name__ == "__main__":
    t = demo()
    if "--vista" in sys.argv:
        import uvicorn
        with kit.db() as con:
            con.execute("update kommo.chats set scraped_at = now() where account=%s", (C,))
        puerto = int(sys.argv[sys.argv.index("--vista") + 1])
        print(f"http://localhost:{puerto}/reportes#{t}", flush=True)
        uvicorn.run(kit.app, host="127.0.0.1", port=puerto, log_level="warning")
