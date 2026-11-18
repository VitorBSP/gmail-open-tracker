create table if not exists public.caucao_email_tracker_messages (
    token uuid primary key default gen_random_uuid(),
    created_at timestamptz not null default now(),
    recipient text not null,
    subject text not null,
    gmail_message_id text,
    gmail_thread_id text
);

create table if not exists public.caucao_email_tracker_requests (
    id bigint generated always as identity primary key,
    token uuid not null references public.caucao_email_tracker_messages(token)
        on delete cascade,
    requested_at timestamptz not null default now()
);

create index if not exists caucao_tracker_requests_token_idx
    on public.caucao_email_tracker_requests(token, requested_at desc);

alter table public.caucao_email_tracker_messages enable row level security;
alter table public.caucao_email_tracker_requests enable row level security;

revoke all on public.caucao_email_tracker_messages from public, anon, authenticated;
revoke all on public.caucao_email_tracker_requests from public, anon, authenticated;
revoke all on sequence public.caucao_email_tracker_requests_id_seq
    from public, anon, authenticated;

grant select, insert, update, delete
    on public.caucao_email_tracker_messages to service_role;
grant select, insert, update, delete
    on public.caucao_email_tracker_requests to service_role;
grant usage, select
    on sequence public.caucao_email_tracker_requests_id_seq to service_role;
