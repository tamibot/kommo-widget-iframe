---
title: 9. Límites de Kommo
---

# 9. Límites de Kommo

Kommo permite unas **7 solicitudes por segundo por cuenta**. Además vigila **la IP de tu servidor**:

- **Pasarse en la cuenta** → 429. Los usuarios se quedan sin su herramienta un rato.
- **Pasarse en la IP** → 403 a todo, a veces por días, y en **todas** las cuentas que salen de esa IP.
  No avisa: si tu flujo ignora errores, parece que todo anda bien.

## Cómo lo resuelve el kit
- **Un solo contador, en Postgres** (`kw.turno`). Cada llamada a Kommo, venga de la API, de un script
  o de una tarea, pide turno ahí. Un `sleep` en cada script no sirve, porque el límite lo rompe **la
  suma** de procesos.
- **Dos techos, y manda el más bajo:** el de la cuenta y la fila `*` de toda la IP. Ambos van en
  `techo` = 5/s, por debajo del límite real.
- **Freno de mano.** Ante un 429 se frena la cuenta 60 s. Ante un 403 sin JSON (bloqueo de IP) se frena
  **todo el servidor** una hora. Nadie reintenta en caliente.
- **Falla cerrado.** Si el contador no responde, no se llama a Kommo.
- **Siempre `limit=250`.** Cada página cuesta una solicitud, traiga 10 o 250.

## Reglas para scripts sueltos
1. Nunca `curl` ni `requests` directo a Kommo: usa la clase `Kommo` de `server/kommo.py`.
2. Antes de una corrida grande, **prueba con 5 a 10 registros** y mide solicitudes por segundo reales.
3. Calcula el costo: si cada lead cuesta N solicitudes, tardarás `leads × N ÷ 5` segundos. Acepta ese
   tiempo y no aceleres.
4. **Si ves un 429 o un 403:** detén todo lo que llame a Kommo, no reintentes y espera.
