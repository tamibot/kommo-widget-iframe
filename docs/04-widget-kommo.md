---
title: 4. El widget en Kommo
---

# 4. El widget en Kommo

## 4.1 Arma el ZIP
```bash
./widget/build.sh https://widget.tudominio.com
```
El script pone tu dominio dentro de `script.js` y deja `widget/widget.zip`. Cambia los textos en
`widget/i18n/es.json` y los logos en `widget/images/`, con los mismos nombres y tamaños.

## 4.2 Créalo en Kommo
1. *Ajustes → Integraciones → Crear integración* (integración privada).
2. Ponle nombre y descripción, y activa los permisos de acceso a todos los datos.
3. En **Widget**, sube `widget.zip`.
4. En la pestaña **Llaves y alcances**, genera el **token de larga duración**. Cópialo: Kommo lo muestra
   una sola vez.

## 4.3 Instálalo y conéctalo
1. Abre la integración y pulsa **Instalar**.
2. Pega el token en **«Token de larga duración»**.
3. Pulsa **Conectar**. El servidor valida el token, registra los webhooks, arranca la carga inicial y
   llena **«Clave del widget»**.
4. Pulsa **Guardar**. Si el campo del token todavía tiene algo, el widget no te deja guardar: el
   token no debe quedar en Kommo.

## 4.4 Dónde verlo
- **Pantalla completa:** *Ajustes → Integraciones → tu widget*.
- **Ficha del lead:** columna derecha, con los datos de ese lead.

## 4.5 Si algo no se ve

| Síntoma | Causa probable | Qué hacer |
|---|---|---|
| «Un administrador debe conectar el widget» | Falta la clave en ajustes | Repetir 4.3 |
| El iframe sale en blanco | `PUBLIC_URL` o el dominio del ZIP no coinciden | Revisar `.env` y volver a armar el ZIP |
| «Kommo no aceptó el token» | Token vencido, mal copiado o sin permisos | Generar otro en la integración |
| «Kommo pidió esperar» | Se tocó el límite de solicitudes | Esperar; ver el [paso 9](09-limites-de-kommo.md) |
| Datos viejos | Webhook desactivado o caído | Pulsar **Sincronizar** y revisar `kw.webhooks` |

## 4.6 Cambiar la página
La vista es `server/app.html`: HTML y JavaScript sin dependencias. Agrega columnas, filtros o pestañas
ahí, y los datos en `server/app.py`. Cada ruta nueva para el iframe debe validar el ticket con
`_ticket()`.
