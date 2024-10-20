import json
import os
import boto3
import logging
import traceback
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from typing import List, Dict, Any

# Configuração de logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Função para buscar as credenciais do S3
def get_google_credentials(user_id: str) -> Credentials:
    s3_client = boto3.client('s3')

    try:
        logger.info(f"Buscando credenciais no S3 para o usuário {user_id}")
        s3_response = s3_client.get_object(
            Bucket=os.environ['S3_BUCKET_NAME'],
            Key=f'{user_id}/google-calendar-tokens.json'
        )

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
        logger.error(f"Erro ao buscar credenciais para o usuário {user_id}: {str(e)}")
        raise RuntimeError(f"Falha ao buscar credenciais no S3 para o usuário {user_id}") from e

# Função para criar um evento no Google Calendar
def create_calendar_event(
    credentials: Credentials, 
    calendar_id: str, 
    start_time: str, 
    end_time: str, 
    attendees: List[str], 
    summary: str, 
    description: str
) -> Dict[str, Any]:
    try:
        logger.info(f"Criando evento no Google Calendar para o calendar_id {calendar_id}")
        service = build('calendar', 'v3', credentials=credentials)

        event_body = {
            'summary': summary,
            'location': '',
            'description': description,
            'start': {
                'dateTime': start_time,
                'timeZone': 'America/Sao_Paulo',  
            },
            'end': {
                'dateTime': end_time,
                'timeZone': 'America/Sao_Paulo',  
            },
            'attendees': [{'email': attendee} for attendee in attendees],
            'reminders': {
                'useDefault': True,
            },
        }

        event_result = service.events().insert(calendarId=calendar_id, body=event_body).execute()
        logger.info(f"Evento criado com sucesso: {event_result.get('id')}")
        return event_result
    except Exception as e:
        logger.error(f"Erro ao criar o evento no Google Calendar: {str(e)}")
        traceback.print_exc()
        raise RuntimeError("Falha ao criar evento no Google Calendar") from e

# Função Lambda Handler
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    try:
        body = json.loads(event.get('body', '{}'))

        user_id = body['user_id']
        calendar_id = body['calendar_id']
        start_time = body['start_time']
        end_time = body.get('end_time', (datetime.fromisoformat(start_time) + timedelta(hours=1)).isoformat())
        attendees = body['attendees']
        summary = body['summary']
        description = body.get('description', '')

        logger.info(f"Requisição recebida para criar evento: user_id={user_id}, calendar_id={calendar_id}")
        logger.info(f"start_time={start_time}, end_time={end_time}, attendees={attendees}, summary={summary}, description={description}")

        credentials = get_google_credentials(user_id)
        event_result = create_calendar_event(credentials, calendar_id, start_time, end_time, attendees, summary, description)

        return {
            'statusCode': 200,
            'body': json.dumps(event_result),
            'headers': {
                'Content-Type': 'application/json'
            }
        }

    except KeyError as ke:
        logger.error(f"Erro de chave ausente no corpo da requisição: {str(ke)}")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Parâmetro obrigatório ausente no corpo da requisição'}),
            'headers': {
                'Content-Type': 'application/json'
            }
        }

    except Exception as e:
        logger.error(f"Erro inesperado: {str(e)}")
        traceback.print_exc()
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Erro interno do servidor'}),
            'headers': {
                'Content-Type': 'application/json'
            }
        }
