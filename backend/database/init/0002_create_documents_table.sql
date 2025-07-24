create table public.documents
(
    uuid              uuid      default gen_random_uuid() not null primary key,
    conversation_uuid uuid                                not null,
    title             varchar(255)                        null,
    type              varchar(255)                        not null,
    filepath          text                                not null,
    created_at        timestamp default now(),

    FOREIGN KEY (conversation_uuid) REFERENCES public.conversations (uuid) ON DELETE CASCADE,
    UNIQUE (conversation_uuid, title),
    UNIQUE (conversation_uuid, filepath)
);
