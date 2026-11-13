# Widget iframe para Kommo

Kit para mostrar **una página propia dentro de Kommo**, en Ajustes o en la ficha de cada lead, con datos
al día y un botón **Sincronizar**. Nació de un widget real en producción. Aquí está lo que funcionó y
lo que aprendimos en el camino, sin datos de ningún cliente.

**Guía completa:** [docs/index.md](docs/index.md). También se publica como página con GitHub Pages.

## Qué puedes hacer con esto

- **Ver en Kommo lo que Kommo no muestra:** tablas, reportes y filtros propios, una ficha de paciente o
  de cliente con todo su historial.
- **Mantener una copia de tus leads y contactos al día,** con webhooks y con un botón «Sincronizar»
  por si un aviso no llegó.
- **Respetar los límites de Kommo** con un contador compartido. La regla es simple: que nunca te bloqueen.
- **Exportar a Google Sheets con n8n,** a la hora que quieras.
- **Abrir la vista solo para el lead de la ficha.** Ese ticket no ve el resto de la cuenta.

## Qué necesitas

| Pieza | Para qué | Detalle |
|---|---|---|
| Cuenta de Kommo con permisos de administrador | Crear la integración y el token | [Paso 1](docs/01-que-necesitas.md) |
| Un servidor con Docker y un dominio | Corre la API, la base y n8n | [Paso 3](docs/03-servidor.md) |
| Este repositorio en GitHub | Código, versiones y la guía publicada | [Paso 3](docs/03-servidor.md) |
| n8n (va incluido) | Exportar a Sheets y automatizar | [Paso 7](docs/07-n8n.md) |

## Estructura

```
server/     API (FastAPI), página del iframe, esquema de la base y prueba de punta a punta
widget/     La «cáscara» que se sube a Kommo (manifest, script, textos, logos) y build.sh
n8n/        Flujo de ejemplo: exportar leads a Google Sheets
ejemplos/   Citas y Cotizaciones (cáscara + explicación) y un dashboard de atención con Kommo Power
docs/       Guía de onboarding (GitHub Pages)
docker-compose.yml · Caddyfile · .env.example
```

## Ejemplos reales

En [`ejemplos/`](ejemplos/) están las cáscaras de dos widgets en producción, con la explicación de qué hace
cada uno y qué se aprendió:
- **[Citas](ejemplos/citas/):** agenda dentro de Kommo, citas en la ficha y recordatorios por WhatsApp.
- **[Cotizaciones](ejemplos/cotizaciones/):** varias cotizaciones o tratamientos por cliente, reportes
  y Excel.
- **[Dashboard de atención](ejemplos/reportes-kommo-power/):** cómo se atiende por chat, actualizado cada
  día con Kommo Power. Trae código completo y prueba.

## Arranque rápido

```bash
cp .env.example .env              # completa dominios y claves (ver docs/08)
docker compose up -d              # API + Postgres + n8n + HTTPS
curl https://widget.tudominio.com/salud
./widget/build.sh https://widget.tudominio.com   # crea widget/widget.zip para Kommo
```

Luego, en Kommo:
1. Sube `widget/widget.zip`.
2. Pega el token.
3. Pulsa **Conectar** y después **Guardar**.

El paso a paso está en [docs/04-widget-kommo.md](docs/04-widget-kommo.md).

## Probar en tu máquina

```bash
createdb widget_kit
cd server && pip install -r requirements.txt
DATABASE_URL=postgresql://localhost/widget_kit python test_app.py
```

La prueba simula Kommo. Cubre conectar la cuenta, los tickets por ficha, Sincronizar, los webhooks con
borrados, la ruta de n8n y el limitador.

## Licencia

MIT. Úsalo, cámbialo y compártelo.
