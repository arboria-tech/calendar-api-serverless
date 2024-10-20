import json
import os
import boto3
import traceback
from datetime import datetime, timedelta
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

# Função para criar um evento no Google Calendar
def create_calendar_event(credentials, calendar_id, start_time, end_time, attendees, summary, description):
    try:
        # Constrói o serviço de API do Google Calendar
        service = build('calendar', 'v3', credentials=credentials)

        # Cria o corpo do evento
        event = {
            'summary': summary,
            'location': '',
            'description': description,
            'start': {
                'dateTime': start_time,
                'timeZone': 'America/Sao_Paulo',  # Defina o fuso horário adequado
            },
            'end': {
                'dateTime': end_time,
                'timeZone': 'America/Sao_Paulo',  # Defina o fuso horário adequado
            },
            'attendees': [{'email': attendee} for attendee in attendees],
            'reminders': {
                'useDefault': True,
            },
        }

        # Insere o evento no calendário
        event_result = service.events().insert(calendarId=calendar_id, body=event).execute()
        return event_result
    except Exception as e:
        print(f"Error creating event: {e}")
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
        # Caso não tenha end time, considera 1 hora de duração
        end_time = body.get('end_time', (datetime.fromisoformat(start_time) + timedelta(hours=1)).isoformat())
        attendees = body['attendees']
        summary = body['summary']
        description = body.get('description', '')

        print(f"Creating event for user_id={user_id}, calendar_id={calendar_id}, start_time={start_time}, end_time={end_time}")

        # Busca as credenciais do Google associadas ao user_id no S3
        credentials = get_google_credentials(user_id)

        # Cria o evento no Google Calendar
        event_result = create_calendar_event(credentials, calendar_id, start_time, end_time, attendees, summary, description)

        # Retorna o evento criado em formato JSON
        return {
            'statusCode': 200,
            'body': json.dumps(event_result),
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
