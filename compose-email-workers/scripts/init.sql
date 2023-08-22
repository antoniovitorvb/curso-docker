-- DROP DATABASE email_sender;
CREATE DATABASE email_sender;

\c email_sender

CREATE TABLE emails (
    id serial not null,
    data timestamp not null default CURRENT_TIMESTAMP,
    assunto varchar(100) not null,
    mensagem varchar(250) not null
);