from bottle import route, run, request
import psycopg2

DSN = 'host=db dbname=email_sender user=postgres password=admin'
SQL = 'INSERT INTO emails (assunto, mensagem) VALUES (%s, %s)'

def register_message(assunto, mensagem):
    conn = psycopg2.connect(DSN)
    cur = conn.cursor()
    cur.execute(SQL, (assunto, mensagem))
    conn.commit()
    cur.close()
    conn.close()

    print('Mensagem registrada com sucesso!')

@route('/', method='POST')
def send():
    assunto = request.forms.get('assunto')
    mensagem = request.forms.get('mensagem')

    register_message(assunto, mensagem)
    return f"Mensagem enfileirada ! Assunto: {assunto}\nMensagem: {mensagem}"

if __name__ == '__main__':
    run(host='0.0.0.0', port=8080, debug=True)