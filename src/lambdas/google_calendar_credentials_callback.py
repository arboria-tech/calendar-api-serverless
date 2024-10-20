import json
import os
import boto3
import logging
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from typing import Any, Dict

# Configura o logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def exchange_code_for_tokens(code: str) -> Credentials:
    """
    Troca o código de autorização pelo token de acesso e refresh tokens usando OAuth2.

    Args:
        code (str): Código de autorização fornecido pelo Google.

    Returns:
        Credentials: Objeto contendo as credenciais OAuth2.
    """
    try:
        flow = Flow.from_client_secrets_file(
            'client_secret.json',
            scopes=['https://www.googleapis.com/auth/calendar']
        )
        flow.redirect_uri = os.environ.get('REDIRECT_URI', 'https://default-uri.com/callback')
        flow.fetch_token(code=code)
        
        logger.info("Tokens trocados com sucesso.")
        return flow.credentials
    except Exception as e:
        logger.error(f"Erro ao trocar o código por tokens: {str(e)}")
        raise

def associate_tokens_with_user(user_id: str, credentials: Credentials) -> None:
    """
    Salva os tokens do usuário no S3, associando-os ao user_id.

    Args:
        user_id (str): O ID do usuário.
        credentials (Credentials): Credenciais OAuth2 obtidas.
    """
    tokens = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

    try:
        s3_client = boto3.client('s3')
        s3_client.put_object(
            Bucket=os.environ['S3_BUCKET_NAME'],
            Key=f'{user_id}/google-calendar-tokens.json',
            Body=json.dumps(tokens)
        )
        logger.info(f"Tokens salvos no S3 para o user_id: {user_id}.")
    except Exception as e:
        logger.error(f"Erro ao salvar tokens no S3 para o user_id {user_id}: {str(e)}")
        raise

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handler principal da Lambda que troca o código por tokens e salva no S3.

    Args:
        event (Dict[str, Any]): Evento da Lambda contendo parâmetros de consulta.
        context (Any): Contexto de execução da Lambda.

    Returns:
        Dict[str, Any]: Resposta HTTP com conteúdo HTML ou mensagens de erro.
    """
    try:
        # Extrai parâmetros da query string
        query_params = event.get('queryStringParameters', {})
        code = query_params.get('code')
        user_id = query_params.get('state')  # O state contém o user_id

        if not code or not user_id:
            logger.warning("Parâmetros obrigatórios ausentes (code ou state).")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Parâmetros obrigatórios: code e state (user_id)'}),
                'headers': {
                    'Content-Type': 'application/json'
                }
            }

        logger.info(f"Iniciando o processo de troca de tokens para user_id: {user_id}.")

        # Troca o código de autorização por tokens
        credentials = exchange_code_for_tokens(code)

        # Associa tokens ao usuário (salva no S3)
        associate_tokens_with_user(user_id, credentials)

        # Gera a resposta HTML de sucesso
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Google Calendar - Sucesso</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f4f6f9;
                    margin: 0;
                    padding: 0;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    color: #333;
                }}
                .container {{
                    text-align: center;
                    background-color: white;
                    padding: 50px;
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                    border-radius: 10px;
                }}
                h1 {{
                    color: #4CAF50;
                }}
                p {{
                    font-size: 18px;
                    margin-bottom: 20px;
                }}
                a {{
                    text-decoration: none;
                    color: white;
                    background-color: #4CAF50;
                    padding: 10px 20px;
                    border-radius: 5px;
                    font-size: 16px;
                }}
                a:hover {{
                    background-color: #45a049;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Conectado com sucesso ao Google Calendar!</h1>
                <p>Parabéns, sua conta foi associada corretamente! Agora podemos marcar eventos!</p>
            </div>
        </body>
        </html>
        """

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'text/html'
            },
            'body': html_content
        }

    except Exception as e:
        logger.error(f"Erro no processamento da requisição: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Erro interno do servidor'}),
            'headers': {
                'Content-Type': 'application/json'
            }
        }
