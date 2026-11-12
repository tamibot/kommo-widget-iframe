-- Esquema del kit. Idempotente: se puede correr en cada arranque.
create schema if not exists kw;

-- Cuentas de Kommo conectadas. El token va cifrado (Fernet, TOKEN_KEY del entorno).
-- `clave` es lo que guarda el widget en sus ajustes para pedir tickets cortos.
create table if not exists kw.cuentas (
  cuenta      text primary key,              -- subdominio: «miempresa» de miempresa.kommo.com
  token       text not null,
  clave       text not null unique,
  activo      boolean not null default true,
  creada      timestamptz not null default now(),
  ultimo_sync timestamptz
);

-- Tickets del iframe: duran minutos, se guardan solo como hash.
-- lead_id = null abre toda la cuenta; con lead_id, solo la ficha de ese lead.
create table if not exists kw.sesiones (
  ticket_hash text primary key,
  cuenta      text not null references kw.cuentas,
  lead_id     bigint,
  expira      timestamptz not null
);

-- Copia local de lo que el iframe muestra. Se llena con webhooks y con «Sincronizar».
create table if not exists kw.leads (
  cuenta      text not null,
  id          bigint not null,
  nombre      text,
  pipeline_id bigint,
  etapa_id    bigint,
  contacto_id bigint,
  creado      timestamptz,
  actualizado timestamptz,
  campos      jsonb,
  primary key (cuenta, id)
);

create table if not exists kw.contactos (
  cuenta      text not null,
  id          bigint not null,
  nombre      text,
  telefono    text,
  actualizado timestamptz,
  campos      jsonb,
  primary key (cuenta, id)
);

-- Cada aviso de Kommo se guarda ANTES de responder (Kommo corta a los 2 s)
-- y se procesa después. Si algo falla, queda el error escrito.
create table if not exists kw.webhooks (
  id        bigserial primary key,
  recibido  timestamptz not null default now(),
  cuenta    text,
  cuerpo    text not null,
  procesado timestamptz,
  error     text
);
create index if not exists webhooks_pendientes on kw.webhooks (id) where procesado is null;

-- ── Limitador compartido ────────────────────────────────────────────────
-- Kommo limita por cuenta (7 solicitudes/s) y por IP del servidor. La suma de
-- TODOS los procesos es lo que cuenta, así que el turno se pide aquí, en la base,
-- y no con un sleep local. La fila '*' es el techo de toda la IP.
create table if not exists kw.cuota (
  cuenta          text primary key,
  techo           numeric not null default 5,   -- solicitudes por segundo, por debajo del límite real
  proximo         timestamptz,
  bloqueado_hasta timestamptz
);

-- 0 = adelante; >0 = milisegundos a esperar; -1 = freno de mano puesto.
create or replace function kw.turno_fila(p_cuenta text, p_costo int default 1)
returns int language plpgsql as $$
declare
  v     kw.cuota%rowtype;
  ahora timestamptz := clock_timestamp();
begin
  insert into kw.cuota (cuenta) values (p_cuenta) on conflict (cuenta) do nothing;
  select * into v from kw.cuota where cuenta = p_cuenta for update;
  if v.bloqueado_hasta is not null and v.bloqueado_hasta > now() then
    return -1;
  end if;
  if v.proximo is not null and v.proximo > ahora then
    return greatest(1, ceil(extract(epoch from (v.proximo - ahora)) * 1000)::int);
  end if;
  update kw.cuota set proximo = ahora + make_interval(secs => p_costo::float8 / v.techo)
   where cuenta = p_cuenta;
  return 0;
end $$;

-- Manda el techo más bajo: primero el de la IP ('*'), después el de la cuenta.
create or replace function kw.turno(p_cuenta text, p_costo int default 1)
returns int language plpgsql as $$
declare g int;
begin
  g := kw.turno_fila('*', p_costo);
  if g <> 0 then return g; end if;
  return kw.turno_fila(p_cuenta, p_costo);
end $$;

-- Freno de mano ante un 429/403: corta a todos los procesos a la vez.
create or replace function kw.frenar(p_cuenta text, p_segundos int default 60)
returns void language sql as $$
  insert into kw.cuota (cuenta) values (p_cuenta) on conflict (cuenta) do nothing;
  update kw.cuota
     set bloqueado_hasta = greatest(coalesce(bloqueado_hasta, now()), now() + make_interval(secs => p_segundos))
   where cuenta = p_cuenta;
$$;
