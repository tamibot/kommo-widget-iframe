# Ejemplos reales: Citas, Cotizaciones y dashboard de atención

Tres ejemplos que siguen el mismo patrón del kit: el widget es solo una **cáscara** que abre una página
del servidor en un iframe. Citas y Cotizaciones funcionan hoy en cuentas de Kommo.

| Ejemplo | Qué resuelve | Carpeta |
|---|---|---|
| **Citas** | Kommo no tiene «cita». Agenda por día, semana y mes; las citas de cada lead en su ficha; avisos de choque; recordatorios de WhatsApp | [`citas/`](citas/) |
| **Cotizaciones** | Varias cotizaciones o tratamientos por cliente, cada uno con su propio seguimiento, reportes y Excel | [`cotizaciones/`](cotizaciones/) |
| **Dashboard de atención** | Conversaciones por día, sin respuesta, por canal, agente y anuncio, con los datos que Kommo Power baja cada día | [`reportes-kommo-power/`](reportes-kommo-power/) |

## Qué hay en cada carpeta

El dashboard de atención trae su código completo (servidor, página y prueba), listo para sumar al kit.
De Citas y Cotizaciones va solo la **cáscara del widget**: `manifest.json`, `script.js`, textos (`i18n/`) e imágenes. Es lo que se
sube a Kommo en un ZIP. El servidor de estos dos productos no se publica: tiene configuración de
clientes. El servidor del kit (`server/`) muestra el mismo patrón completo, listo para adaptar.

## Diferencias con la cáscara del kit

Los ejemplos usan otros nombres de rutas. Para usarlos con el servidor del kit, cambia estas líneas en
su `script.js` o agrega rutas con estos nombres en `server/app.py`:

| Paso | Kit (`widget/`) | Citas y Cotizaciones |
|---|---|---|
| Conectar con el token | `POST /v1/conectar` | `POST /v1/clave` (manda también `widget: 'citas'` o `'cotizaciones'`) |
| Pedir el ticket | `POST /v1/sesion` · cabecera `X-Widget-Clave` | `POST /v1/embed/sesion` · cabecera `X-Kommo-Clave` |
| Página del iframe | `/app#ticket` | Citas: `/embed#ticket` · Cotizaciones: `/cotizaciones#ticket` |
| Renovar el ticket | `postMessage {kw:'renovar'}` | `postMessage {k10k:'renovar'}` |

El dominio del servidor está como `https://widget.tudominio.com` en `script.js` y `manifest.json`.
Cámbialo por el tuyo antes de armar el ZIP:

```bash
cd ejemplos/citas/widget && zip -r ../citas.zip manifest.json script.js i18n images
```

## Lo que muestran estos ejemplos, además del kit

- **La clave también se guarda en `localStorage`** como respaldo: algunas versiones de Kommo tardan en
  devolver los ajustes recién guardados.
- **Un aviso claro cuando falta conectar.** El usuario que no es administrador ve qué hacer, no un error.
- **`onSave` se niega a guardar un token.** Si alguien lo pega y no pulsa «Conectar», Kommo no lo guarda.
- **Cada callback va envuelto en `try`.** Un error del widget no puede romper la pantalla de Kommo.
- **El área de trabajo se busca con varios selectores** (en Cotizaciones), porque Kommo cambia sus ids
  entre versiones.
