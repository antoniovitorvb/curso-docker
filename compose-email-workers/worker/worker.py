import redis
import json
from time import sleep
from random import randint
import os



if __name__ == '__main__':
    redis_host = os.getenv(key='REDIS_HOST', default='queue')
    r = redis.Redis(host=redis_host, port=6379, db=0)
    print('Aguardando mensagens...')

    while True:
        mensagem = json.loads(r.blpop('sender')[1])
        # Simulando envio de e-mail...
        print('Enviando a mensagem', mensagem['assunto'])
        sleep(randint(5, 15))
        print('Mensagem', mensagem['assunto'], 'enviada!')