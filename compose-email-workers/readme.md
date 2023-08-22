# Projeto Envio de E-mails com Workers

### Iniciando a composição com o banco de dados
Inicialize o Docker;

abrindo o terminal na pasta `/compose-email-workers/` execute:
```sh
docker-compose up
docker-compose ps
```
Verifique se `compose-email-workers_db_1` está executando com `State Up`.

Se tudo estiver certo, liste os bancos de dados existentes dentro da instância `db` e depois encerre-a:
```sh
docker-compose exec db psql -U postgres -c '\l'
docker-compose down
```
se alguma mensagem de erro aparecer como
```
CryptographyDeprecationWarning: Blowfish has been deprecated "class": algorithms.Blowfish
```
Execute os seguintes comandos e tente novamente:
```sh
pip install --upgrade paramiko
docker-compose restart db
```

### Usando volumes e scripts de banco de dados

Após adicionados os volumes em [docker-compose.yml](docker-compose.yml) execute:
```sh
docker-compose ps
```
Se estiver vazio execute e verifique se `State = Up`
```sh
docker-compose up -d
docker-compose ps
```
```sh
docker-compose exec db psql -U postgres -f /scripts/check.sql
```
Isso vai executar o arquivo `check.sql` para verificar se o database `email_sender` foi criado corretamente


### Começando a camada de front-end

Após criada a pasta `web/` e adicionado o serviço `frontend` em [docker-compose.yml](docker-compose.yml) reinicie o container
```sh
docker-compose down
docker-compose up -d
docker-compose ps
```
Agora abra o navegador em [localhost:80](localhost:80)


### Aplicativo para enfileirar as mensagens

Após criar a pasta `app/`, criado os arquivos `app.sh` e `sender.py`, adicionado as configorações em [docker-compose.yml](docker-compose.yml):
```sh
docker-compose down
docker-compose up -d
docker-compose ps
```
Se não funcionar adicione `bash`:
```yml
service:
  app:
    command: bash ./app.sh
```


### Configurando Proxy reverso

- Criei a pasta `nginx/`;
- Criei o arquivo `nginx/default.conf` para redirecionar a porta `8080` para `/api`;
- No [docker-compose.yml](docker-compose.yml) adicionei um volume ao serviço de `frontend`:
```yml
  frontend:
    image: nginx:1.13
    volumes:
      # Site
      - ./web:/usr/share/nginx/html/
      # Configurando um proxy reverso
      - ./nginx/default.conf:/etc/nginx/conf.d/default.conf
```
- No arquivo [web/index.html](web/index.html) alterei:
```html
<!-- De: -->
<form action="http://localhost:8080" method="POST">
<!-- Para: -->
<form action="http://localhost/api" method="POST">
```
- Reiniciei novamente o `docker-compose`


### Redes, dependência e banco de dados

- Adicionei o parâmetro `networks` em [docker-compose.yml](docker-compose.yml) para os serviços `db`, `frontend` e `app` e suas dependências (`depends_on:`);
- Em [app/app.sh](app/app.sh) adicionei a biblioteca `psycopg2==2.7.3.2` para acessar o banco de dados Postgres;
---
#### `Obs.:` Em caso de erros como:

  ```
  Error: 500 Internal Server


OperationalError('FATAL: password authentication failed for user "postgres"\n',)
  ```
  1. destive o sistema com o parâmetro `-v` para remover os volumes antigos
  ```sh
  docker-compose down -v
  ```
  2. Em [docker-compose.yml](docker-compose.yml) adicione:
  ```yml
  db:
    environment:
        POSTGRES_PASSWORD: postgres
  ```
  1. Em [app/sender.py](app/sender.py) altere o `DSN`
  ```py
  # De:
  DSN = 'dbname=email_sender user=postgres host=db'
  # Para:
  DSN = 'host=db dbname=email_sender user=postgres password=postgres'
  ```
---
- Para verificar se funcionou, vá em [localhost](localhost) e envie um e-mail;
- Se a mensagem foi enfileirada, execute no terminal o comando com a query abaixo:
```sh
docker-compose exec db psql -U postgres -d email_sender -c 'SELECT * FROM emails'
```


### Filas e Workers

- Nova pasta `worker`
- Nova rede chamada `fila`;
- 2 novos serviços: `queue` e `worker`
    ```yml
    services:
      queue:
        image: redis:3.2
        networks:
          - fila
    
      worker:
        image: python:3.6
        volumes:
          # Workers
          - ./worker:/worker
        working_dir: /worker
        command: bash ./app.sh
        networks:
          - fila
        depends_on:
          - queue
    ```
- Biblioteca `redis==2.10.5` adicionada a [app/app.sh](app/app.sh);
- Refatoração em [app/sender.py](app/sender.py):
  - Novas bibliotecas importadas;
  - Criada a classe `Sender` para a fila
- Na pasta `worker/` criei os arquivos `app.sh` para instalar as dependências e `worker.py` para consumir as mensagens da fila `sender` e simular envio dessa mensagem por email.