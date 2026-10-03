create extension if not exists pgcrypto;

create table if not exists public.profiles (
 id uuid primary key references auth.users(id) on delete cascade,
 email text,
 plan text not null default 'free' check(plan in ('free','pro')),
 pro_expires_at timestamptz,
 created_at timestamptz not null default now()
);
create table if not exists public.mailboxes (
 id uuid primary key default gen_random_uuid(),
 address text unique not null,
 owner_id uuid references auth.users(id) on delete set null,
 visitor_id text,
 plan text not null default 'free' check(plan in ('free','pro')),
 created_at timestamptz not null default now(),
 expires_at timestamptz not null,
 active boolean not null default true
);
create unique index if not exists one_active_mailbox_per_user on public.mailboxes(owner_id) where active=true and owner_id is not null;
create unique index if not exists one_active_mailbox_per_visitor on public.mailboxes(visitor_id) where active=true and visitor_id is not null;
create table if not exists public.messages (
 id uuid primary key default gen_random_uuid(),
 mailbox_id uuid not null references public.mailboxes(id) on delete cascade,
 sender text, recipient text, subject text, body_text text, body_html text,
 received_at timestamptz not null default now()
);
create table if not exists public.payments (
 id uuid primary key default gen_random_uuid(),
 provider text not null, external_id text unique not null,
 user_id uuid references auth.users(id) on delete set null,
 email text, amount numeric, currency text, status text, payload jsonb,
 created_at timestamptz not null default now()
);
create index if not exists messages_mailbox_received_idx on public.messages(mailbox_id,received_at desc);
alter table public.profiles enable row level security;
alter table public.mailboxes enable row level security;
alter table public.messages enable row level security;
alter table public.payments enable row level security;
