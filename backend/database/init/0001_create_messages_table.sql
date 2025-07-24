create table public.messages
(
    uuid               uuid      default gen_random_uuid() not null primary key,
    conversation_uuid  uuid                                not null,
    message            json                                not null,
    intermediate_steps json,
    created_at         timestamp default now(),

    FOREIGN KEY (conversation_uuid) REFERENCES public.conversations (uuid) ON DELETE CASCADE
);
