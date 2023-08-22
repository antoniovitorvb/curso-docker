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


### Múltiplas instâncias/workers "Escalar é preciso"

- `Dockerfile` criado na pasta `worker/`
- Em [docker-compose.yml](docker-compose.yml), serviço `worker` foi alterado para:
```yml
services:
  worker:
    build: worker # vai procurar em worker/Dockerfile
    volumes:
      # Workers
      - ./worker:/worker
    working_dir: /worker
    command: worker.py
    networks:
      - fila
    depends_on:
      - queue
```
- Para definir quantos worker serão criados na inicialização execute:
```sh
docker-compose up -d --scale worker=3
```


### Boas práticas: variáveis de ambiente

- Em [app/sender.py](app/sender.py), ao invés de usar valores fixos para acesso ao BD, foi criado variáveis como:
```py
db_host = os.getenv(key='DB_HOST', default='db')
db_user = os.getenv(key='DB_USER', default='postgres')
db_name = os.getenv(key='DB_NAME', default='sender')
```
---
`Obs.:` em `db_name`, o parâmetro `default='sender'` foi propositadamente colocado diferente do valor real (`DB_NAME=email_sender`) para testar se o a variável iria buscar o valor correto em [docker-compose.yml](docker-compose.yml)
```yml
services:
  app:
    environment:
      - DB_NAME=email_sender
```
---
- No terminal, subi novamente o projeto;
```sh
docker-compose up -d --scale worker=3
```
---
`Obs.:` Em caso de
  ```
  404 Not Found
  nginx/1.13.12
  ```
  1. Abra [app/sender.py](app/sender.py):
  
      Crie uma variável global para senha e altere o `dsn`:
  ```py
  db_pw = os.getenv(key='DB_PASSWORD', default='postgres')
  ```  
  ```py
  # De:
  dsn = f"dbname={db_name} user={db_user} host={db_host}"
  # Para:
  dsn = f"host={db_host} dbname={db_name} user={db_user} password={db_pw}"
  ```
  2. Reinicie a aplicação
---
- Envie um e-mail e consulte se foi guardado no banco de dados corretamente
```sh
docker-compose exec db psql -U postgres -d email_sender -c 'SELECT * FROM emails'
```


### Override

- Criei o arquivo [docker-compose.override.yml](docker-compose.override.yml);
- Em [docker-compose.yml](docker-compose.yml) alterei `DB_NAME` para um nome errado;
```yml
version: '3'
services:
  app:
    environment:
      - DB_NAME=abc_sender
```
O objetivo dessas alterações foi testar se o `override` corrigiria um `DB_NAME` errado.

O [docker-compose.override.yml](docker-compose.override.yml) é flexibilizar alterações que não precisam alterar um build ou uma imagem. Neste caso, mesmo com o `environment` errado em [docker-compose.yml](docker-compose.yml) o programa funcionou corretamente.