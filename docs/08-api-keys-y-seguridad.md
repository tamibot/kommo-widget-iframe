---
title: 8. API keys y seguridad
---

# 8. API keys y seguridad

| Clave | Dónde vive | Para qué | Si se filtra |
|---|---|---|---|
| Token de larga duración de Kommo | Cifrado en `kw.cuentas` | Leer y escribir en la cuenta | Revocarlo en la integración, generar otro y volver a **Conectar** |
| `TOKEN_KEY` | `.env` | Cifra los tokens guardados | Generar otra y reconectar cada cuenta: los tokens viejos ya no se leen |
| `POSTGRES_PASSWORD` | `.env` | Acceso a la base | Cambiarla en Postgres y en `.env` |
| `INTERNAL_KEY` | `.env` y credencial de n8n | n8n lee `/v1/interno/*` | Cambiarla en los dos lados |
| `N8N_ENCRYPTION_KEY` | `.env` | n8n cifra sus credenciales | **No cambiarla** sin exportar antes las credenciales: n8n deja de arrancar |
| Credencial de Google (OAuth) | Dentro de n8n | Escribir en Sheets | Revocarla en la cuenta de Google |
| Clave del widget | Ajustes del widget en Kommo | Pedir tickets | Volver a **Conectar** genera la misma; para cambiarla, borra la cuenta en `kw.cuentas` y reconecta |

## Reglas
- **Nada de claves en git.** El `.env` está en `.gitignore`. Antes de cada `git push`, revisa que no
  se cuele un token en un archivo de prueba.
- **Si una clave pasa por un chat, un correo o una captura de pantalla, rótala.** Quedó guardada en un
  lugar que no controlas.
- **En el servidor**, si tu proveedor tiene un gestor de secretos (AWS SSM Parameter Store, por
  ejemplo), úsalo para generar el `.env` en vez de dejarlo a mano.
- **Los datos de cada cliente van en la cuenta del cliente**, o al menos en una base separada por
  cliente, nunca mezclados con los tuyos.

## Lo que ya cuida el kit
- El token **se pega una vez y no se guarda en Kommo**. El servidor lo cifra.
- Los **tickets duran 15 minutos**, se guardan como hash y viajan en el `#` de la URL, no en la query.
- Un ticket abierto desde la ficha **solo ve ese lead**.
- La página solo se deja enmarcar por Kommo (`Content-Security-Policy: frame-ancestors`).
- `/v1/interno/*` no existe desde internet, y sin `INTERNAL_KEY` responde 404.

## Límite conocido
Cualquier usuario de la cuenta puede leer la **clave del widget** en los ajustes, porque Kommo guarda así
los ajustes. Con ella se pide un ticket de cuenta completa. Para cerrarlo del todo hay que validar los
tokens firmados de un solo uso de Kommo (`$authorizedAjax`) con el *secret key* de la integración.
