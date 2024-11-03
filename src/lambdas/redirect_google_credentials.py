import os
import json
import logging
from google_auth_oauthlib.flow import Flow
from typing import Any, Dict, Union

# Configura o logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Função para gerar a URL de autorização
def get_authorization_url(user_id: str) -> str:
    """
    Gera a URL de autorização para o Google OAuth2 usando o ID do usuário.
    
    Args:
        user_id (str): O ID do usuário que será incluído no parâmetro 'state'.

    Returns:
        str: A URL de autorização para o fluxo OAuth2.
    """
    redirect_uri = os.environ.get('REDIRECT_URI', 'https://default-uri.com/callback')
    
    try:
        flow = Flow.from_client_secrets_file(
            'client_secret.json',
            scopes=['https://www.googleapis.com/auth/calendar']
        )
        flow.redirect_uri = redirect_uri

        authorization_url, _ = flow.authorization_url(
            access_type='offline',
            state=user_id,
            include_granted_scopes='true'
        )
        
        logger.info(f"Authorization URL generated successfully for user_id={user_id}")
        return authorization_url
    except Exception as e:
        logger.error(f"Error generating authorization URL for user_id={user_id}: {str(e)}")
        raise e

# Função principal do Lambda
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Union[int, Dict[str, str]]]:
    """
    Handler principal da função Lambda que processa a requisição e gera a URL de autorização do Google OAuth2.

    Args:
        event (Dict[str, Any]): O evento da Lambda, contendo o corpo da requisição.
        context (Any): O contexto da Lambda.

    Returns:
        Dict[str, Union[int, Dict[str, str]]]: Resposta HTTP com código de status e cabeçalhos.
    """
    try:
        # Extração do body e validação
        body = json.loads(event.get('body', '{}'))
        user_id = body.get('user_id')

        if not user_id:
            logger.warning("user_id not provided in the request body.")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'user_id is required'}),
                'headers': {
                    'Content-Type': 'application/json'
                }
            }

        logger.info(f"Processing request for user_id={user_id}")

        # Gera a URL de autorização
        authorization_url = get_authorization_url(user_id)

        # Retorna a URL de autorização no corpo da resposta
        return {
            'statusCode': 200,
            'body': json.dumps({'authorization_url': authorization_url}),
            'headers': {
                'Content-Type': 'application/json'
            }
        }

    except json.JSONDecodeError:
        logger.error("Failed to decode JSON from the request body.")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid JSON format'}),
            'headers': {
                'Content-Type': 'application/json'
            }
        }
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal Server Error'}),
            'headers': {
                'Content-Type': 'application/json'
            }
        }
