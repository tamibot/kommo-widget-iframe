---
title: 5. Datos al día
---

# 5. Datos al día: webhooks y botón Sincronizar

## Por qué los dos
Los **webhooks** mantienen todo al momento, pero no son infalibles. El servidor puede estar reiniciando
justo cuando llega un aviso, y Kommo **desactiva el webhook** si recibe muchas respuestas fallidas. El
botón **Sincronizar** es la red de seguridad que el usuario puede pulsar él mismo.

## Webhooks (`POST /webhook`)
1. Se guarda el cuerpo en `kw.webhooks` y se responde de inmediato, porque Kommo corta a los 2 segundos.
2. En segundo plano, por cada lead o contacto del aviso, se **lee el dato real** de Kommo y se guarda.
3. **Borrados y fusiones:** al fusionar dos leads, Kommo borra uno y manda `leads[delete]`. Antes de
   sacarlo de la copia, el servidor confirma con un GET que ya no existe (204). Si fue restaurado, se queda.
4. Si algo falla, el error queda escrito en `kw.webhooks.error`. Nada se pierde en silencio.

Eventos registrados: `add_lead`, `update_lead`, `status_lead`, `delete_lead`, `restore_lead`,
`add_contact` y `update_contact`.

## Botón «Sincronizar» (`POST /v1/embed/sincronizar`)
- Trae los leads y contactos **cambiados en las últimas 24 h**, en páginas de 250 que pasan por el
  limitador.
- Busca los eventos `lead_deleted` del mismo período y saca de la copia lo que Kommo confirma borrado.
- **Un minuto de espera:** un segundo clic devuelve el resultado anterior sin gastar cuota.
- Desde la ficha de un lead no sincroniza toda la cuenta (403).
- No toca el Google Sheet, que se actualiza a su hora con n8n.

En una cuenta con unos 10.000 leads, un clic tarda alrededor de 8 segundos y gasta unas pocas solicitudes.

## Qué no conviene hacer
- **Releer toda la cuenta cada vez que alguien abre el widget.** Funciona, pero con miles de leads
  gasta varios segundos de CPU por apertura y vuelve lenta la vista para todos. Mejor webhooks más
  Sincronizar, y una relectura completa como máximo cada hora.
- **Confiar en el cuerpo del webhook.** Llega de internet. Úsalo solo como aviso y lee el dato de Kommo.
