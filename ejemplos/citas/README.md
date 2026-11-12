# Ejemplo: Citas

Kommo no tiene «cita». Este widget la crea: cada cita es un **elemento de una lista de Kommo** (catálogo)
enlazado al lead, y la agenda es una página del servidor que se ve dentro de Kommo.

## Qué ve el usuario

| Dónde | Qué |
|---|---|
| *Ajustes → Integraciones → Citas* | Agenda por **día** (una columna por profesional), **semana**, **mes** y **lista**. Filtros de sede, profesional y estado. Clic en un hueco = nueva cita a esa hora |
| Ficha del lead (columna derecha) | Próxima cita, sus otras citas, aviso si tiene más de una por atender, botón **Agendar** y cierre en un clic (asistió, no asistió, reprogramar) |
| Al agendar | Avisa si el paciente ya tiene otra cita pendiente o si el profesional ya tiene ese horario. Deja «Agendar de todos modos» |
| Configuración (la primera vez) | Crea la lista «Citas» y sus campos (tipo, sede, profesional, estado) si la cuenta no la tiene |
| Recordatorios | Un aviso por WhatsApp el día anterior y el mismo día, solo en horario permitido |

## Cómo funciona

```
Kommo (navegador)                    Servidor
widget (cáscara) ── clave ──────▶ POST /v1/embed/sesion → ticket de 15 min
  iframe /embed#ticket ─────────▶ leer agenda, buscar paciente  (0 solicitudes a Kommo: lee la copia)
                                  crear cita   → Kommo: elemento de lista + enlace al lead + campo del lead
                                  cambiar cita → Kommo: actualizar elemento + releer + lead
```

- **El navegador nunca llama a Kommo.** Todo lo que se escribe pasa por el limitador del servidor.
- **La zona horaria es la de la cuenta de Kommo** (*Ajustes → Generales*), no la del navegador ni la
  del servidor. Se lee al conectar, en la misma solicitud que valida el token.
- **Dos personas no pueden tomar el mismo hueco:** la creación de citas va bajo un candado en Postgres.
- **Campos en el lead:** «Próxima cita» y «Última cita (estado)». Con ellos, el Digital Pipeline y los
  Salesbots de Kommo pueden reaccionar a las citas sin tocar el servidor.

## Recordatorios de WhatsApp: el reloj es nuestro, el mensaje es de Kommo

1. El cliente crea en Kommo **2 plantillas de WhatsApp** (recordatorio y confirmación), que aprueba
   Meta, y **2 bots de un solo paso** que envían cada plantilla.
2. Una tarea de n8n llama al servidor cada 15 minutos, por la red interna.
3. El servidor decide a quién le toca y escribe el texto en un campo del lead, con la fecha vigente: si
   la cita se reprogramó sale la hora nueva, y si se canceló no sale nada. Después dispara el bot de
   esa cuenta.
4. Kommo no deja leer por API las plantillas que no creó tu integración. Por eso la única prueba real
   es **«Enviar prueba»** a un número propio.

## Lo que necesita la cuenta

- Plan **Advanced o superior**, por las listas personalizadas.
- Un **administrador** que conecte una vez: token → «Conectar» → «Guardar».

## Lecciones de este widget

- **Un lead fusionado deja su cita huérfana.** Antes de escribir en un lead, confirma que sigue
  existiendo. Si no existe, saca la cita de la copia y sigue con las demás, sin cortar el barrido.
- **No barras todo cada minuto.** Lo que cambia ya llega por el widget y por los webhooks. Un barrido
  dos veces al día cubre las citas vencidas sin marcar.
- **Un 403 con JSON es de la cuenta** (plan o permisos) y frena solo esa cuenta. **Un 403 sin JSON es
  bloqueo de IP** y frena todo el servidor.
