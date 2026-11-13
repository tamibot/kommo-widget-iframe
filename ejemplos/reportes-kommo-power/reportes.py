"""Dashboard de atención con los datos que Kommo Power deja cada día en Postgres.

Kommo Power (`kommo_chat_export.py --to-postgres`) baja las conversaciones de Kommo y llena
`kommo.chats`, `kommo.leads` y `kommo.contacts`. Este router solo LEE esas tablas: no llama
a Kommo y no gasta cuota. Se monta en el servidor del kit:

    from reportes import router as reportes_router
    app.include_router(reportes_router)
"""
import datetime as dt
import os

import psycopg
from fastapi import APIRouter, Header, HTTPException, Query
from fastapi.responses import HTMLResponse
from pathlib import Path

router = APIRouter()
AQUI = Path(__file__).parent
# Puede ser la misma base del kit o la de Kommo Power, si vive en otro lado.
DSN = os.environ.get("KOMMO_POWER_DSN") or os.environ["DATABASE_URL"]
VIEJO_HORAS = 26          # si la última bajada tiene más que esto, la página lo avisa


def _cuenta(ticket):
    import app as kit                       # el ticket lo valida el servidor del kit
    cuenta, lead = kit._ticket(ticket)
    if lead is not None:
        raise HTTPException(403, "El dashboard es de toda la cuenta, no de la ficha de un lead.")
    return cuenta


@router.get("/reportes", response_class=HTMLResponse)
def pagina():
    return HTMLResponse((AQUI / "reportes.html").read_text(encoding="utf-8"),
                        headers={"Content-Security-Policy": "frame-ancestors https://*.kommo.com https://*.amocrm.com",
                                 "Cache-Control": "no-store"})


@router.get("/v1/embed/reportes")
def reportes(x_ticket: str | None = Header(None), dias: int = Query(30, ge=1, le=365)):
    cuenta = _cuenta(x_ticket)
    hasta = dt.date.today()
    desde = hasta - dt.timedelta(days=dias - 1)
    p = {"c": cuenta, "d": desde, "h": hasta}
    with psycopg.connect(DSN) as con:
        q = lambda sql: con.execute(sql, p).fetchall()
        k = q("""select count(*), coalesce(sum(msg_count),0),
                        count(*) filter (where has_human_response),
                        count(*) filter (where bot_count > 0 and not has_human_response and not no_reply),
                        count(*) filter (where no_reply),
                        percentile_cont(0.5) within group (order by extract(epoch from first_human_at - first_contact_at) / 60)
                          filter (where first_human_at is not null and first_contact_at is not null
                                  and first_human_at >= first_contact_at)
                   from kommo.chats where account=%(c)s and chat_date between %(d)s and %(h)s""")[0]
        diario = q("""select chat_date, count(*), count(*) filter (where has_human_response),
                             count(*) filter (where no_reply)
                        from kommo.chats where account=%(c)s and chat_date between %(d)s and %(h)s
                       group by 1 order by 1""")
        canales = q("""select coalesce(channel,'sin canal'), count(*), count(*) filter (where no_reply)
                         from kommo.chats where account=%(c)s and chat_date between %(d)s and %(h)s
                        group by 1 order by 2 desc""")
        agentes = q("""select a, count(*) from kommo.chats, unnest(human_agents) a
                        where account=%(c)s and chat_date between %(d)s and %(h)s group by 1 order by 2 desc limit 15""")
        anuncios = q("""select coalesce(referral->>'headline', referral->>'source_url', 'Anuncio sin título'),
                               count(*), count(*) filter (where no_reply)
                          from kommo.chats where account=%(c)s and chat_date between %(d)s and %(h)s
                           and referral is not null and referral <> 'null'::jsonb
                         group by 1 order by 2 desc limit 10""")
        embudo = q("""select coalesce(pipeline_name,'—'), coalesce(status_name,'—'), count(*)
                        from kommo.leads where account=%(c)s
                         and lead_created_at::date between %(d)s and %(h)s
                       group by 1, 2 order by 1, 3 desc""")
        sin_respuesta = q("""select ch.lead_id, ct.name, ch.channel, ch.first_contact_at
                               from kommo.chats ch
                               left join kommo.contacts ct on ct.account=ch.account and ct.contact_id=ch.contact_id
                              where ch.account=%(c)s and ch.no_reply and ch.chat_date between %(d)s and %(h)s
                              order by ch.first_contact_at desc nulls last limit 25""")
        ultima = q("select max(scraped_at) from kommo.chats where account=%(c)s")[0][0]
    total = k[0] or 0
    pct = lambda n: round(100 * n / total) if total else 0
    viejo = ultima is None or (dt.datetime.now(dt.timezone.utc) - ultima) > dt.timedelta(hours=VIEJO_HORAS)
    return {
        "cuenta": cuenta, "desde": desde.isoformat(), "hasta": hasta.isoformat(),
        "actualizado": ultima.isoformat() if ultima else None, "datos_viejos": viejo,
        "kpis": {"conversaciones": total, "mensajes": int(k[1]), "con_humano": k[2], "solo_bot": k[3],
                 "sin_respuesta": k[4], "pct_con_humano": pct(k[2]), "pct_sin_respuesta": pct(k[4]),
                 "mediana_primera_respuesta_min": round(k[5]) if k[5] is not None else None},
        "diario": [{"fecha": f.isoformat(), "conversaciones": n, "con_humano": h, "sin_respuesta": s}
                   for f, n, h, s in diario],
        "canales": [{"canal": c, "conversaciones": n, "sin_respuesta": s} for c, n, s in canales],
        "agentes": [{"agente": a, "conversaciones": n} for a, n in agentes],
        "anuncios": [{"anuncio": a, "conversaciones": n, "sin_respuesta": s} for a, n, s in anuncios],
        "embudo": [{"embudo": e, "etapa": s, "leads": n} for e, s, n in embudo],
        "sin_respuesta": [{"lead_id": l, "contacto": c, "canal": ch,
                           "desde": f.isoformat() if f else None,
                           "url": f"https://{cuenta}.kommo.com/leads/detail/{l}"} for l, c, ch, f in sin_respuesta],
    }
