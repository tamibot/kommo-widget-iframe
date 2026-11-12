"""Servidor del widget: conecta la cuenta, entrega el iframe y mantiene una copia
de Kommo al día con webhooks y con el botón «Sincronizar».

    uvicorn app:app --host 0.0.0.0 --port 8000
"""
import datetime as dt
import hashlib
import hmac
import json
import logging
import os
import re
import secrets
import threading
import time
from pathlib import Path
from urllib.parse import parse_qs

import psycopg
from cryptography.fernet import Fernet
from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse

from kommo import CuotaAgotada, Kommo, TokenRechazado

log = logging.getLogger("widget")
AQUI = Path(__file__).parent
DSN = os.environ["DATABASE_URL"]
URL_PUBLICA = os.environ.get("PUBLIC_URL", "http://localhost:8000").rstrip("/")
CLAVE_INTERNA = os.environ.get("INTERNAL_KEY", "")
TICKET_MIN = 15
SYNC_HORAS, SYNC_ESPERA_S = 24, 60
EVENTOS = ["add_lead", "update_lead", "status_lead", "delete_lead", "restore_lead",
           "add_contact", "update_contact"]

_fernet = Fernet(os.environ["TOKEN_KEY"].encode())
app = FastAPI(title="Widget iframe para Kommo")


def db():
    return psycopg.connect(DSN, autocommit=True)


with db() as _con:
    _con.execute((AQUI / "schema.sql").read_text(encoding="utf-8"))


def cliente(cuenta: str) -> Kommo:
    with db() as con:
        f = con.execute("select token from kw.cuentas where cuenta=%s and activo", (cuenta,)).fetchone()
    if not f:
        raise HTTPException(404, "cuenta no conectada")
    return Kommo(db, cuenta, _fernet.decrypt(f[0].encode()).decode())


def con_kommo(cuenta, fn):
    """Errores de Kommo como respuestas claras para el iframe."""
    try:
        return fn(cliente(cuenta))
    except CuotaAgotada as e:
        raise HTTPException(429, f"Kommo pidió esperar: {e}")
    except TokenRechazado:
        raise HTTPException(401, "El token de Kommo venció. Vuelve a conectar el widget.")


# ── copia local ─────────────────────────────────────────────────────────

def _ts(v):
    return dt.datetime.fromtimestamp(v, dt.timezone.utc) if v else None


def guardar_leads(leads, cuenta):
    with db() as con:
        for l in leads:
            contacto = next(iter(((l.get("_embedded") or {}).get("contacts") or [])), {}).get("id")
            con.execute("""insert into kw.leads (cuenta,id,nombre,pipeline_id,etapa_id,contacto_id,creado,actualizado,campos)
                           values (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                           on conflict (cuenta,id) do update set nombre=excluded.nombre, pipeline_id=excluded.pipeline_id,
                             etapa_id=excluded.etapa_id, contacto_id=excluded.contacto_id,
                             actualizado=excluded.actualizado, campos=excluded.campos""",
                        (cuenta, l["id"], l.get("name"), l.get("pipeline_id"), l.get("status_id"), contacto,
                         _ts(l.get("created_at")), _ts(l.get("updated_at")), json.dumps(l.get("custom_fields_values"))))


def guardar_contactos(contactos, cuenta):
    with db() as con:
        for c in contactos:
            tel = next((v.get("value") for f in c.get("custom_fields_values") or [] if f.get("field_code") == "PHONE"
                        for v in f.get("values") or []), None)
            con.execute("""insert into kw.contactos (cuenta,id,nombre,telefono,actualizado,campos) values (%s,%s,%s,%s,%s,%s)
                           on conflict (cuenta,id) do update set nombre=excluded.nombre, telefono=excluded.telefono,
                             actualizado=excluded.actualizado, campos=excluded.campos""",
                        (cuenta, c["id"], c.get("name"), tel, _ts(c.get("updated_at")),
                         json.dumps(c.get("custom_fields_values"))))


def quitar_borrados(k, cuenta, ids):
    """Un lead borrado o fusionado en Kommo se saca de la copia solo si Kommo
    confirma que ya no existe (GET responde 204)."""
    borrados = [i for i in ids if not k.get(f"leads/{i}")]
    if borrados:
        with db() as con:
            con.execute("delete from kw.leads where cuenta=%s and id = any(%s)", (cuenta, borrados))
    return borrados


def traer(k, desde: dt.datetime | None):
    filtro = {"filter[updated_at][from]": int(desde.timestamp())} if desde else {}
    leads = list(k.paginar("leads", **{"with": "contacts"}, **filtro))
    guardar_leads(leads, k.cuenta)
    contactos = list(k.paginar("contacts", **filtro))
    guardar_contactos(contactos, k.cuenta)
    return len(leads), len(contactos)


# ── conectar la cuenta (una vez, desde los ajustes del widget) ──────────

@app.post("/v1/conectar")
def conectar(datos: dict, tareas: BackgroundTasks):
    """Recibe el token de larga duración UNA vez, lo valida, lo guarda cifrado y
    devuelve la `clave` que el widget guarda en sus ajustes. El token no vuelve a Kommo."""
    cuenta = (datos.get("cuenta") or "").strip().lower()
    token = (datos.get("token") or "").strip()
    if not re.fullmatch(r"[a-z0-9-]{2,63}", cuenta) or not token:
        raise HTTPException(400, "faltan cuenta o token")
    with db() as con:
        f = con.execute("select token, clave from kw.cuentas where cuenta=%s", (cuenta,)).fetchone()
    if f and hmac.compare_digest(_fernet.decrypt(f[0].encode()).decode(), token):
        return {"clave": f[1]}
    k = Kommo(db, cuenta, token)
    try:
        k.get("account")
    except (TokenRechazado, CuotaAgotada, Exception):
        raise HTTPException(400, "Kommo no aceptó el token")
    clave = f[1] if f else secrets.token_urlsafe(24)
    with db() as con:
        con.execute("""insert into kw.cuentas (cuenta, token, clave) values (%s,%s,%s)
                       on conflict (cuenta) do update set token=excluded.token, activo=true""",
                    (cuenta, _fernet.encrypt(token.encode()).decode(), clave))
    tareas.add_task(_instalar, cuenta)
    return {"clave": clave}


def _instalar(cuenta):
    k = cliente(cuenta)
    try:
        k.post("webhooks", {"destination": f"{URL_PUBLICA}/webhook", "settings": EVENTOS})
        traer(k, None)                          # carga completa, una vez
        with db() as con:
            con.execute("update kw.cuentas set ultimo_sync=now() where cuenta=%s", (cuenta,))
    except Exception:
        log.exception("%s: falló la instalación", cuenta)


# ── tickets cortos para el iframe ───────────────────────────────────────

def _hash(t):
    return hashlib.sha256(t.encode()).hexdigest()


@app.post("/v1/sesion")
def sesion(datos: dict | None = None, x_widget_clave: str | None = Header(None)):
    """La clave del widget se canjea por un ticket de minutos. El ticket viaja en el
    #hash de la URL del iframe (no queda en logs del servidor) y luego en cabecera."""
    with db() as con:
        f = con.execute("select cuenta from kw.cuentas where clave=%s and activo", (x_widget_clave or "",)).fetchone()
    if not f:
        raise HTTPException(403, "clave inválida")
    lead = (datos or {}).get("lead")
    if lead is not None and not re.fullmatch(r"\d{1,15}", str(lead)):
        raise HTTPException(400, "lead inválido")
    ticket = secrets.token_urlsafe(32)
    with db() as con:
        con.execute("delete from kw.sesiones where expira < now()")
        con.execute("insert into kw.sesiones values (%s,%s,%s, now() + make_interval(mins => %s))",
                    (_hash(ticket), f[0], int(lead) if lead is not None else None, TICKET_MIN))
    return {"ticket": ticket, "expira_en": TICKET_MIN * 60}


def _ticket(ticket):
    with db() as con:
        f = con.execute("select cuenta, lead_id from kw.sesiones where ticket_hash=%s and expira > now()",
                        (_hash(ticket or ""),)).fetchone()
    if not f:
        raise HTTPException(403, "sesión vencida")
    return f


# ── el iframe ───────────────────────────────────────────────────────────

@app.get("/app", response_class=HTMLResponse)
def pagina():
    # Solo Kommo puede enmarcar la página.
    return HTMLResponse((AQUI / "app.html").read_text(encoding="utf-8"),
                        headers={"Content-Security-Policy": "frame-ancestors https://*.kommo.com https://*.amocrm.com",
                                 "Cache-Control": "no-store"})


@app.get("/v1/embed/leads")
def leads(x_ticket: str | None = Header(None), q: str = ""):
    cuenta, lead = _ticket(x_ticket)
    with db() as con:
        filas = con.execute("""select l.id, l.nombre, l.etapa_id, c.nombre, c.telefono, l.creado, l.actualizado
                                 from kw.leads l left join kw.contactos c on c.cuenta=l.cuenta and c.id=l.contacto_id
                                where l.cuenta=%s and (%s::bigint is null or l.id=%s)
                                  and (%s = '' or l.nombre ilike %s or c.nombre ilike %s or c.telefono ilike %s)
                                order by l.creado desc nulls last limit 500""",
                            (cuenta, lead, lead, q, f"%{q}%", f"%{q}%", f"%{q}%")).fetchall()
        sync = con.execute("select ultimo_sync from kw.cuentas where cuenta=%s", (cuenta,)).fetchone()[0]
    return {"ultimo_sync": sync.isoformat() if sync else None,
            "leads": [{"id": a, "nombre": b, "etapa_id": c, "contacto": d, "telefono": e,
                       "creado": f.isoformat() if f else None, "actualizado": g.isoformat() if g else None}
                      for a, b, c, d, e, f, g in filas]}


# ── botón «Sincronizar» ─────────────────────────────────────────────────
# ponytail: candado en memoria, vale con un solo proceso uvicorn; con varios, pg_advisory_lock.
_candado = threading.Lock()
_ultima: dict[str, tuple[float, dict]] = {}


@app.post("/v1/embed/sincronizar")
def sincronizar(x_ticket: str | None = Header(None)):
    """Por si un webhook no llegó: trae lo cambiado en las últimas 24 h y saca lo
    borrado. Unas pocas solicitudes por clic, y varios clics seguidos no gastan cuota."""
    cuenta, lead = _ticket(x_ticket)
    if lead is not None:
        raise HTTPException(403, "La ficha de un lead no sincroniza toda la cuenta.")
    if not _candado.acquire(blocking=False):
        raise HTTPException(409, "Ya se está sincronizando. Espera unos segundos.")
    try:
        previo = _ultima.get(cuenta)
        if previo and time.monotonic() - previo[0] < SYNC_ESPERA_S:
            return {**previo[1], "reciente": True}
        desde = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=SYNC_HORAS)

        def correr(k):
            n_leads, n_contactos = traer(k, desde)
            eventos = k.paginar("events", limite=100, **{"filter[type]": "lead_deleted",
                                                         "filter[created_at][from]": int(desde.timestamp())})
            ids = sorted({int(e["entity_id"]) for e in eventos})
            with db() as con:
                en_copia = [f[0] for f in con.execute("select id from kw.leads where cuenta=%s and id=any(%s)",
                                                      (cuenta, ids)).fetchall()]
            return {"ok": True, "leads": n_leads, "contactos": n_contactos,
                    "borrados": len(quitar_borrados(k, cuenta, en_copia))}

        r = con_kommo(cuenta, correr)
        with db() as con:
            con.execute("update kw.cuentas set ultimo_sync=now() where cuenta=%s", (cuenta,))
        _ultima[cuenta] = (time.monotonic(), r)
        return r
    finally:
        _candado.release()


# ── webhooks de Kommo ───────────────────────────────────────────────────

@app.post("/webhook")
async def webhook(req: Request, tareas: BackgroundTasks):
    """Guardar y responder: Kommo corta a los 2 s y desactiva el webhook tras
    muchas respuestas fallidas. El trabajo va después."""
    cuerpo = (await req.body()).decode("utf-8", "replace")
    cuenta = (parse_qs(cuerpo).get("account[subdomain]") or [None])[0]
    with db() as con:
        con.execute("insert into kw.webhooks (cuenta, cuerpo) values (%s,%s)", (cuenta, cuerpo))
    tareas.add_task(procesar_pendientes)
    return {"ok": True}


def procesar_pendientes():
    with db() as con:
        filas = con.execute("select id, cuenta, cuerpo from kw.webhooks where procesado is null order by id limit 200").fetchall()
    for wid, cuenta, cuerpo in filas:
        error = None
        try:
            aplicar(cuenta, parse_qs(cuerpo))
        except Exception as e:                  # el error queda escrito, no se pierde
            error = str(e)[:500]
            log.exception("webhook %s", wid)
        with db() as con:
            con.execute("update kw.webhooks set procesado=now(), error=%s where id=%s", (error, wid))


def aplicar(cuenta, q):
    """El cuerpo del webhook es solo un aviso: los datos se leen de Kommo."""
    with db() as con:
        if not con.execute("select 1 from kw.cuentas where cuenta=%s and activo", (cuenta,)).fetchone():
            raise ValueError(f"cuenta no conectada: {cuenta}")
    ids = lambda patron: {int(v[0]) for c, v in q.items() if re.fullmatch(patron, c)}
    borrados = ids(r"leads\[delete\]\[\d+\]\[id\]")
    cambiados = ids(r"leads\[(?:add|update|status|restore)\]\[\d+\]\[id\]") - borrados
    contactos = ids(r"contacts\[(?:add|update)\]\[\d+\]\[id\]")
    k = cliente(cuenta)
    if borrados:
        quitar_borrados(k, cuenta, sorted(borrados))
    for lid in cambiados:
        l = k.get(f"leads/{lid}", **{"with": "contacts"})
        if l:
            guardar_leads([l], cuenta)
    for cid in contactos:
        c = k.get(f"contacts/{cid}")
        if c:
            guardar_contactos([c], cuenta)


# ── para n8n (Sheet, reportes) ──────────────────────────────────────────

@app.get("/v1/interno/leads")
def para_n8n(cuenta: str, x_interno: str | None = Header(None)):
    """Filas planas para que n8n las escriba en un Sheet. Solo con INTERNAL_KEY."""
    if not CLAVE_INTERNA or not hmac.compare_digest(x_interno or "", CLAVE_INTERNA):
        raise HTTPException(404, "Not Found")
    with db() as con:
        filas = con.execute("""select l.id, l.nombre, l.pipeline_id, l.etapa_id, c.nombre, c.telefono, l.creado
                                 from kw.leads l left join kw.contactos c on c.cuenta=l.cuenta and c.id=l.contacto_id
                                where l.cuenta=%s order by l.id""", (cuenta,)).fetchall()
    return [{"KOMMO ID": a, "LEAD": b, "EMBUDO": c, "ETAPA": d, "CONTACTO": e, "TELEFONO": f,
             "CREADO": g.isoformat() if g else None} for a, b, c, d, e, f, g in filas]


@app.get("/salud")
def salud():
    with db() as con:
        con.execute("select 1")
    return {"ok": True}
