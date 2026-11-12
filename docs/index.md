---
title: Guía de onboarding
---

# Widget iframe para Kommo · Guía de onboarding

Esta guía te lleva de cero a un widget funcionando dentro de Kommo. Síguela en orden la primera vez.

| # | Paso | Lo que te llevas |
|---|---|---|
| 1 | [Qué necesitas](01-que-necesitas.md) | Lista de cuentas, accesos y piezas |
| 2 | [Cómo funciona](02-arquitectura.md) | El dibujo completo: Kommo, widget, servidor, base y n8n |
| 3 | [Servidor y GitHub](03-servidor.md) | API, base de datos y n8n corriendo con HTTPS |
| 4 | [El widget en Kommo](04-widget-kommo.md) | El widget instalado y conectado |
| 5 | [Datos al día: webhooks y Sincronizar](05-sincronizar.md) | Por qué hacen falta los dos |
| 6 | [Base de datos](06-base-de-datos.md) | Qué guarda cada tabla y consultas útiles |
| 7 | [n8n y Google Sheets](07-n8n.md) | Exportación diaria a un Sheet |
| 8 | [API keys y seguridad](08-api-keys-y-seguridad.md) | Cada clave, dónde vive y cómo rotarla |
| 9 | [Límites de Kommo](09-limites-de-kommo.md) | Cómo no quedar bloqueado |
| 10 | [Lecciones aprendidas](10-lecciones.md) | Lo que se rompió en producción y cómo se evitó |

## En una frase

El widget de Kommo es solo una **cáscara**: pide un ticket corto a tu servidor y muestra tu página en un
iframe. Los datos, la lógica y las claves viven en tu servidor, nunca en Kommo ni en el navegador.
