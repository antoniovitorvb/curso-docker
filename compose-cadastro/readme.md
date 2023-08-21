# Projeto Cadastro Simples

Inicialize o Docker;

abrindo o terminal na pasta `/compose-cadastro/` execute:

```sh
docker-compose up
```

Ele vai ler os arquivos e executar todos os containers, todos os serviços que foram configurados

Para testar, abra o navegador em [localhost](localhost) para ver o [FrontEnd](frontend/index.html) e [localhost:3000](localhost:3000) para ver o [BackEnd](backend/app.js).

`Observação:` se o comando não funcionar, acesse a pasta `/backend` e instale as dependências manualmente:
```sh
cd backend/
sudo npm i
```