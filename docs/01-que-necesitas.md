---
title: 1. Qué necesitas
---

# 1. Qué necesitas

## Kommo
- **Usuario administrador.** Solo un administrador crea integraciones y sube widgets.
- **Una integración privada** en *Ajustes → Integraciones → Crear integración*. De ahí sale el
  **token de larga duración**: con él, tu servidor lee y escribe en la cuenta.
- **Plan:** el widget y la API funcionan en todos. Las *listas* (catálogos) y algunos campos piden
  Advanced o superior. Si la API responde 403 con JSON, casi siempre es eso o falta de permisos.

## Servidor
- **Un VPS con Docker:** AWS EC2, Lightsail, DigitalOcean o similar. Para una cuenta con unos 10.000
  leads bastan 2 GB de RAM y 2 vCPU.
- **Un dominio** con dos subdominios apuntando a la IP del servidor: uno para la API (`widget.`) y otro
  para n8n (`n8n.`). Caddy saca los certificados HTTPS solo.
- **Puertos 80 y 443 abiertos.** El resto, cerrado. Entra por SSH con llave o por la consola del
  proveedor (en AWS, SSM).

## GitHub
- **Un repositorio** con este código. Así cada cambio queda con historial y puedes volver atrás.
- **GitHub Pages** (opcional) para publicar esta guía: *Settings → Pages → Deploy from branch →
  `main` / `docs`*.

## n8n (incluido en `docker-compose.yml`)
- Para tareas programadas: exportar a Google Sheets, avisos y reportes.
- **Una credencial de Google** dentro de n8n (OAuth) si vas a escribir en Sheets.

## Antes de empezar, ten a mano
- [ ] El subdominio de Kommo (`miempresa` de `miempresa.kommo.com`).
- [ ] El token de larga duración de la integración privada.
- [ ] Los dos dominios apuntando al servidor.
- [ ] Las claves del `.env`, que se explican en el [paso 8](08-api-keys-y-seguridad.md).
