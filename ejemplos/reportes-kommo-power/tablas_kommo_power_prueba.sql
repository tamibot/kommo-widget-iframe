-- SOLO PARA PROBAR sin Kommo Power. En producción estas tablas las crea Kommo Power con su
-- db/001_schema.sql y las llena `kommo_chat_export.py --to-postgres`. Columnas = las que usa
-- reportes.py, con los mismos nombres y tipos que el esquema de Kommo Power.
create schema if not exists kommo;

create table if not exists kommo.contacts (
  account text not null, contact_id bigint not null, name text,
  updated_at timestamptz not null default now(), primary key (account, contact_id));

create table if not exists kommo.leads (
  account text not null, lead_id bigint not null, contact_id bigint,
  pipeline_id bigint, pipeline_name text, status_id bigint, status_name text,
  lead_created_at timestamptz, updated_at timestamptz not null default now(),
  primary key (account, lead_id));

create table if not exists kommo.chats (
  account text not null, lead_id bigint not null, talk_id bigint not null, contact_id bigint,
  channel text, chat_date date,
  msg_count int not null default 0, in_count int not null default 0, out_count int not null default 0,
  bot_count int not null default 0, human_count int not null default 0, media_count int not null default 0,
  has_human_response boolean not null default false, no_reply boolean not null default false,
  human_takeover_at_msg int, bot_names text[] not null default '{}', human_agents text[] not null default '{}',
  first_contact_at timestamptz, first_bot_at timestamptz, first_human_at timestamptz,
  referral jsonb, messages jsonb not null default '[]', scraped_at timestamptz not null default now(),
  primary key (account, lead_id, talk_id));
