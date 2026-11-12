---
title: 3. Servidor y GitHub
---

# 3. Servidor y GitHub

## 3.1 Copia el repositorio
```bash
git clone https://github.com/TU_USUARIO/kommo-widget-iframe.git
cd kommo-widget-iframe
```
Trabaja en tu propio fork o repositorio, y sube cada cambio con `git push`.

> **No lo pongas dentro de una carpeta sincronizada** (iCloud, Dropbox, OneDrive). Esos servicios dejan
> archivos «a medio bajar» y git se cuelga o corrompe sus referencias. Usa una carpeta local normal.

## 3.2 Configura el `.env`
```bash
cp .env.example .env
nano .env
```
Cada valor se explica en el [paso 8](08-api-keys-y-seguridad.md). El `.env` **no se sube a GitHub**:
ya está en `.gitignore`.

## 3.3 Levanta todo
```bash
docker compose up -d
docker compose ps                         # api, db, n8n y caddy en «running»
curl https://widget.tudominio.com/salud   # {"ok":true}
```
El esquema de la base se crea solo al arrancar la API.

## 3.4 Actualizar sin romper nada
```bash
git pull
docker compose up -d --build api
curl https://widget.tudominio.com/salud
```
- **Hazlo fuera del horario del cliente.** Al reiniciar se pierden unos segundos de webhooks, y Kommo
  desactiva el webhook si falla muchas veces seguidas.
- **No reinicies mientras corre una exportación de n8n.** Mira antes en n8n que no haya ejecuciones
  en curso.
- **Antes de construir**, etiqueta la imagen anterior para poder volver:
  `docker tag NOMBRE:latest NOMBRE:antes-$(date +%Y%m%d%H%M)`.

## 3.5 Respaldos
```bash
docker compose exec db pg_dump -U widget widget | gzip > respaldo-$(date +%F).sql.gz
```
Prográmalo con un timer de systemd o un cron, guarda las copias **fuera del servidor** y pruébalas una
vez al mes restaurándolas en otra base. Un respaldo que nunca se restauró no está probado.

## 3.6 Que avise si algo se cae
La ausencia de errores no prueba que esté funcionando. Lo mínimo:
- Un monitor externo (UptimeRobot o similar) contra `/salud`.
- Una alerta si `kw.webhooks` no recibe nada en horario laboral:
  `select max(recibido) from kw.webhooks;`

## 3.7 Publicar la guía con GitHub Pages
*Settings → Pages → Source: Deploy from a branch → `main` y carpeta `/docs` → Save.* En un minuto
queda en `https://TU_USUARIO.github.io/kommo-widget-iframe/`.
