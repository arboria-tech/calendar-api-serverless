import json
import os
import boto3
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

def exchange_code_for_tokens(code):
    flow = Flow.from_client_secrets_file(
        'client_secret.json',
        scopes=['https://www.googleapis.com/auth/calendar']
    )
    flow.redirect_uri = os.environ.get('REDIRECT_URI', 'https://default-uri.com/callback')
    flow.fetch_token(code=code)
    return flow.credentials

def associate_tokens_with_user(user_id, credentials):
    tokens = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
    
    # Salva tokens no S3 associado ao user_id
    s3_client = boto3.client('s3')
    s3_client.put_object(
        Bucket=os.environ['S3_BUCKET_NAME'],
        Key=f'{user_id}/google-calendar-tokens.json',
        Body=json.dumps(tokens)
    )

def lambda_handler(event, context):
    # Pega o código de autorização e o state (que é o user_id)
    code = event['queryStringParameters']['code']
    user_id = event['queryStringParameters']['state']  # O state contém o user_id

    # Troca o código de autorização por tokens
    credentials = exchange_code_for_tokens(code)

    # Associa tokens ao usuário (salvando no S3)
    associate_tokens_with_user(user_id, credentials)

    # Retorna uma página HTML informando que a conexão foi feita com sucesso
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
            <p>Parabéns, sua conta foi associada corretamente! Agora podemos marcar eventos!</strong>.</p>
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
