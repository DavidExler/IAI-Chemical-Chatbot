create table public.conversations
(
    uuid       uuid           not null default gen_random_uuid() primary key,
    user_uuid  uuid           not null,
    title      varchar(40)    not null default 'New Conversation',
    chain      varchar(255)   not null default 'rag',
    prompt     varchar(255)   not null default 'Default',
    tools      varchar(255)[] not null default '{}',
    documents  uuid[]         not null default '{}',
    created_at timestamp      not null default now()
);
