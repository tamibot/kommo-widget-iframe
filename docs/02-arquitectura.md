---
title: 2. Cómo funciona
---

# 2. Cómo funciona

```
 Kommo (navegador del usuario)                Tu servidor (Docker)
 ┌────────────────────────────┐   ticket   ┌───────────────────────────────┐
 │ Widget = cáscara script.js │──────────▶ │ API FastAPI  /app  /v1/...    │
 │  └─ iframe  /app#ticket    │◀────────── │   │                           │
 └────────────────────────────┘   página   │   ├─ Postgres  (copia + cuota)│
                                           │   └─ n8n ──▶ Google Sheets    │
 Kommo (servidores) ── webhooks ─────────▶ │ /webhook                      │
                     ◀── API v4 (con turno)│ cliente kommo.py + limitador  │
                                           └───────────────────────────────┘
```

## Las tres llaves, de más a menos poderosa

1. **Token de larga duración de Kommo.** Se pega una vez en los ajustes del widget. El servidor lo
   valida, lo guarda **cifrado** y nunca lo devuelve. Kommo no lo guarda.
2. **Clave del widget.** El servidor la entrega al conectar, y queda en los ajustes del widget en
   Kommo. Solo sirve para pedir tickets.
3. **Ticket.** Dura 15 minutos y lo pide la cáscara cada vez que abre el iframe. Si se abre desde la
   ficha de un lead, el ticket **solo ve ese lead**.

El ticket viaja en el `#` de la URL del iframe, que el navegador no manda al servidor ni guarda en sus
logs. Después va en la cabecera `X-Ticket`. Cuando vence, el iframe le pide uno nuevo a la cáscara por
`postMessage`, sin recargar la página.

## De dónde salen los datos

- **Webhooks:** Kommo avisa cada alta, cambio, borrado o restauración. El servidor guarda el aviso,
  responde enseguida y después **lee el dato real de Kommo**. El cuerpo del aviso no es confiable.
- **Botón Sincronizar:** trae lo cambiado en las últimas 24 h, por si algún aviso se perdió.
- **Carga inicial:** al conectar la cuenta, una sola vez.

## Dónde aparece en Kommo

| Ubicación (`manifest.json`) | Qué muestra |
|---|---|
| `advanced_settings` | Pantalla completa en *Ajustes → Integraciones → tu widget* |
| `lcard-1` | Columna derecha de la ficha del lead, solo ese lead |
| `settings` | Ventana de ajustes con el botón **Conectar** |
