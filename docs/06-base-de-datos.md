---
title: 6. Base de datos
---

# 6. Base de datos

Postgres, esquema `kw`, definido en [`server/schema.sql`](https://github.com/tamibot/kommo-widget-iframe/blob/main/server/schema.sql). Se aplica solo al
arrancar.

| Tabla | Qué guarda | Notas |
|---|---|---|
| `kw.cuentas` | Cada cuenta de Kommo conectada | `token` cifrado con `TOKEN_KEY`; `clave` para pedir tickets |
| `kw.sesiones` | Tickets del iframe | Solo el hash. Vencen a los 15 min; `lead_id` limita a una ficha |
| `kw.leads` | Copia de los leads | `campos` = los campos personalizados tal como los manda Kommo (JSON) |
| `kw.contactos` | Copia de los contactos | Teléfono principal aparte, para buscar |
| `kw.webhooks` | Cada aviso de Kommo | `procesado` y `error` dicen qué pasó con cada uno |
| `kw.cuota` | Estado del limitador | Una fila por cuenta y la fila `*` de toda la IP |

## Consultas útiles

```sql
-- ¿Siguen llegando avisos? (si está vacío en horario laboral, algo se cortó)
select max(recibido), count(*) filter (where recibido > now() - interval '1 hour') from kw.webhooks;

-- Avisos que fallaron hoy
select recibido, left(error, 120) from kw.webhooks where error is not null and recibido::date = current_date;

-- Leads creados por día (hora de Lima)
select (creado at time zone 'America/Lima')::date as dia, count(*) from kw.leads group by 1 order by 1 desc limit 14;

-- Leer un campo personalizado (reemplaza 123456 por el id del campo)
select id, nombre, f->'values'->0->>'value' as valor
  from kw.leads, jsonb_array_elements(campos) f
 where (f->>'field_id')::bigint = 123456;

-- ¿El limitador está frenado?
select cuenta, bloqueado_hasta from kw.cuota where bloqueado_hasta > now();
```

## Campos personalizados nuevos
Si el cliente crea campos en Kommo, **no hace falta cambiar la base**: llegan dentro de `campos`. Solo
agrégalos donde quieras mostrarlos (la página, el Excel o el Sheet) y **ponlos al final de las
columnas** para no mover las tablas dinámicas que ya tenga el cliente.

Un campo de Kommo no cambia de tipo después de creado. Decide con el cliente antes si es lista o
texto libre.
