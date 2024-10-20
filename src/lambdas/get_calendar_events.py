import json
import os
import boto3
import traceback
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# Função para buscar as credenciais do S3
def get_google_credentials(user_id):
    s3_client = boto3.client('s3')
    
    try:
        # Pega o arquivo de credenciais do bucket
        s3_response = s3_client.get_object(
            Bucket=os.environ['S3_BUCKET_NAME'],
            Key=f'{user_id}/google-calendar-tokens.json'
        )
        
        # Carrega as credenciais a partir do arquivo JSON
        tokens = json.loads(s3_response['Body'].read())
        credentials = Credentials(
            token=tokens['token'],
            refresh_token=tokens['refresh_token'],
            token_uri=tokens['token_uri'],
            client_id=tokens['client_id'],
            client_secret=tokens['client_secret'],
            scopes=tokens['scopes']
        )
        
        return credentials
    except Exception as e:
        print(f"Error fetching credentials for user {user_id}: {e}")
        raise

# Função para buscar eventos no Google Calendar
def get_calendar_events(credentials, calendar_id, start_time, end_time):
    try:
        # Constrói o serviço de API do Google Calendar
        service = build('calendar', 'v3', credentials=credentials)

        # Busca eventos no calendário especificado no intervalo fornecido
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=start_time,
            timeMax=end_time,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        return events
    except Exception as e:
        print(f"Error fetching events: {e}")
        traceback.print_exc()
        raise

def lambda_handler(event, context):
    try:
        # Extrai o corpo da requisição POST
        body = json.loads(event['body'])

        # Pega os parâmetros do corpo da requisição
        user_id = body['user_id']
        calendar_id = body['calendar_id']
        start_time = body['start_time']
        end_time = body['end_time']

        print(f"Fetching events for user_id={user_id}, calendar_id={calendar_id}, start_time={start_time}, end_time={end_time}")

        # Busca as credenciais do Google associadas ao user_id no S3
        credentials = get_google_credentials(user_id)

        # Busca os eventos no Google Calendar
        events = get_calendar_events(credentials, calendar_id, start_time, end_time)

        # Retorna os eventos em formato JSON
        return {
            'statusCode': 200,
            'body': json.dumps(events),
            'headers': {
                'Content-Type': 'application/json'
            }
        }
    
    except Exception as e:
        print(f"Error in lambda_handler: {e}")
        traceback.print_exc()
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
            'headers': {
                'Content-Type': 'application/json'
            }
        }
