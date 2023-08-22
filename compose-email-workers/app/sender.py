from bottle import Bottle, request
import psycopg2
import redis
import json
import os

class Sender(Bottle):
    def __init__(self):
        super().__init__(self)
        self.route('/', method='POST', callback=self.send)
        redis_host = os.getenv(key='REDIS_HOST', default='queue')
        self.fila = redis.StrictRedis(host=redis_host, port=6379, db=0)

        # DSN = Data Source Name
        # DSN = 'host=db dbname=email_sender user=postgres password=postgres'
        
        db_host = os.getenv(key='DB_HOST', default='db')
        db_user = os.getenv(key='DB_USER', default='postgres')
        db_name = os.getenv(key='DB_NAME', default='sender')
        db_pw = os.getenv(key='DB_PASSWORD', default='postgres')

        # dsn = f"dbname={db_name} user={db_user} host={db_host}"
        dsn = f"host={db_host} dbname={db_name} user={db_user} password={db_pw}"
        self.conn = psycopg2.connect(dsn)

    def register_message(self, assunto, mensagem):
        SQL = 'INSERT INTO emails (assunto, mensagem) VALUES (%s, %s)'
        cur = self.conn.cursor()
        cur.execute(SQL, (assunto, mensagem))
        self.conn.commit()
        cur.close()
        # self.conn.close()
        msg = {'assunto': assunto, 'mensagem': mensagem}
        self.fila.rpush('sender', json.dumps(msg)) # pega a fila 'sender' e converte para o formato JSON

        print('Mensagem registrada com sucesso !')
    
    

    # @route('/', method='POST')
    def send(self):
        assunto = request.forms.get('assunto')
        mensagem = request.forms.get('mensagem')

        self.register_message(assunto, mensagem)
        return f"Mensagem enfileirada ! Assunto: {assunto} | Mensagem: {mensagem}"

if __name__ == '__main__':
    sender = Sender() # cria a fila
    sender.run(host='0.0.0.0', port=8080, debug=True)