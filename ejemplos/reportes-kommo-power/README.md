# Ejemplo: dashboard de atención con Kommo Power

Un dashboard dentro de Kommo que muestra **cómo se está atendiendo por chat**. Se actualiza solo cada
día con los datos que baja Kommo Power. Kommo no trae este reporte: su API pública no entrega los
mensajes de los chats.

## Qué muestra

| Bloque | Qué dice | De dónde sale (`kommo.chats`) |
|---|---|---|
| Conversaciones | Cuántas hubo en el período (7, 30 o 90 días) | una fila por conversación |
| Atendidas por una persona | Cuántas tuvieron al menos una respuesta humana, y el % | `has_human_response` |
| Solo bot | Respondió el bot y ninguna persona | `bot_count > 0` sin humano ni `no_reply` |
| Sin respuesta | El cliente escribió y nadie contestó. Se marca en rojo desde el 10 % | `no_reply` |
| Mediana hasta la primera respuesta | Minutos desde el primer mensaje del cliente hasta la primera respuesta de una persona | `first_human_at − first_contact_at` |
| Conversaciones por día | Barras por día, con detalle al pasar el mouse | `chat_date` |
| Por canal | WhatsApp, Instagram, Facebook o TikTok, con sus «sin respuesta» | `channel` |
| Por agente | Conversaciones que atendió cada persona | `human_agents` |
| Anuncios que trajeron chats | Chats que llegaron desde un anuncio (Click to WhatsApp) | `referral` |
| Leads nuevos por etapa | En qué etapa quedaron los leads creados en el período | `kommo.leads` |
| Sin respuesta (lista) | Los 25 más recientes, con botón para abrir el lead en Kommo | `no_reply` |

Arriba se lee **cuándo fue la última bajada**. Si pasaron más de 26 horas, aparece un aviso: es el
canario que dice que la tarea diaria de Kommo Power dejó de correr.

## Cómo llegan los datos cada día

```
cada noche (cron o timer)                       Postgres                       Kommo (iframe)
kommo_chat_export.py --to-postgres  ───▶  kommo.chats / leads / contacts  ◀─── /v1/embed/reportes ◀── /reportes
   (Kommo Power, API privada de Kommo)          (solo lectura desde aquí)
```

1. **Kommo Power** (`kommo_chat_export.py --account <subdominio> --pipeline <id> --to-postgres`) baja las
   conversaciones y llena las tablas del esquema `kommo`, creadas con su `db/001_schema.sql`.
2. Prográmalo **una vez al día**, de madrugada. Respeta su ritmo (unas 5 solicitudes por segundo) y no lo
   corras en paralelo con otro proceso contra la misma cuenta.
3. Este dashboard **solo lee**: no llama a Kommo ni gasta cuota.

> Kommo Power entra por la **API privada** de Kommo, con la sesión de un usuario, porque la pública no
> trae los chats. Úsalo con una cuenta que el cliente autorice y respeta sus límites.

## Instalación sobre el kit

1. Copia `reportes.py` y `reportes.html` a `server/`.
2. En `server/app.py`, al final:
   ```python
   from reportes import router as reportes_router
   app.include_router(reportes_router)
   ```
3. Si las tablas de Kommo Power viven en otra base, define `KOMMO_POWER_DSN` en el `.env`. Si no, usa
   `DATABASE_URL`.
4. Para que el widget abra el dashboard, cambia en `widget/script.js` la ruta del iframe: `'/app'` por
   `'/reportes'`. Si quieres las dos vistas, sube un segundo widget.
5. El subdominio de la cuenta conectada en el kit debe ser el mismo que Kommo Power guarda en `account`.

## Probar sin Kommo ni Kommo Power

```bash
DATABASE_URL=postgresql://localhost/widget_kit python ejemplos/reportes-kommo-power/test_reportes.py
DATABASE_URL=postgresql://localhost/widget_kit python ejemplos/reportes-kommo-power/test_reportes.py --vista 4500
```

La primera corre la prueba. La segunda deja la página abierta con 60 días de datos inventados e imprime
la URL. `tablas_kommo_power_prueba.sql` crea solo las columnas que usa el dashboard, con los mismos
nombres que el esquema real.

## Seguridad
- Solo abre con un ticket de cuenta completa. Desde la ficha de un lead responde 403.
- La página solo se deja enmarcar por Kommo.
- Los nombres de los contactos salen de la base, no del navegador. Para compartir el dashboard fuera
  del equipo del cliente, quita la lista «Sin respuesta».

## Ideas para seguir
- **Tiempo de respuesta en horario hábil** y semáforo por agente. Kommo Power ya lo calcula en
  `kommo_kpis.py`.
- **Exportar a Excel** cada tabla.
- **Un generador de reportes:** que el usuario elija las columnas y los filtros, y el servidor arme la
  consulta.
