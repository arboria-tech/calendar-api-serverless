from google_auth_oauthlib.flow import Flow
import os
import json

def get_authorization_url(user_id):
    # Usa a URI de redirecionamento a partir da variável de ambiente
    redirect_uri = os.environ.get('REDIRECT_URI', 'https://default-uri.com/callback')
    
    # Cria o flow de autenticação
    flow = Flow.from_client_secrets_file(
        'client_secret.json',  # Certifique-se de ter esse arquivo com as credenciais da API do Google
        scopes=['https://www.googleapis.com/auth/calendar']
    )
    flow.redirect_uri = redirect_uri

    # Gerar a URL de autorização com o user_id no state
    authorization_url, _ = flow.authorization_url(
        access_type='offline',
        state=user_id,
        include_granted_scopes='true'
    )

    return authorization_url

def lambda_handler(event, context):
    # Extrai o body da requisição (formato JSON)
    body = json.loads(event['body'])
    user_id = body['user_id']  # O user_id é extraído do corpo da requisição

    # Gera a URL de autorização com o user_id no state
    authorization_url = get_authorization_url(user_id)

    # Retorna a URL de autorização (302 para redirecionamento)
    return {
        'statusCode': 302,
        'headers': {
            'Location': authorization_url
        }
    }
