import json
import os
import boto3
import logging
import traceback
from botocore.exceptions import BotoCoreError, ClientError
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from typing import Any, Dict, List, Optional

# Configura o logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Função para buscar as credenciais do S3
def get_google_credentials(user_id: str) -> Credentials:
    s3_client = boto3.client('s3')
    
    try:
        # Pega o arquivo de credenciais do bucket
        logger.info(f"Fetching Google credentials for user {user_id} from S3.")
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
    except (BotoCoreError, ClientError) as s3_error:
        logger.error(f"Failed to fetch credentials for user {user_id} from S3: {str(s3_error)}")
        raise Exception(f"Unable to retrieve credentials for user {user_id}.")
    except KeyError as key_error:
        logger.error(f"Malformed credentials file for user {user_id}: {str(key_error)}")
        raise Exception(f"Credentials file is missing required fields for user {user_id}.")
    except json.JSONDecodeError as json_error:
        logger.error(f"Error parsing JSON for user {user_id}: {str(json_error)}")
        raise Exception(f"Failed to decode JSON credentials for user {user_id}.")
    except Exception as e:
        logger.error(f"Unexpected error fetching credentials for user {user_id}: {str(e)}")
        raise

# Função para buscar eventos no Google Calendar
def get_calendar_events(credentials: Credentials, calendar_id: str, start_time: str, end_time: str) -> List[Dict[str, Any]]:
    try:
        # Constrói o serviço de API do Google Calendar
        logger.info(f"Fetching calendar events from Google Calendar for calendar ID {calendar_id}.")
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
        logger.info(f"Retrieved {len(events)} events from calendar ID {calendar_id}.")
        return events
    except HttpError as google_error:
        logger.error(f"Error fetching events from Google Calendar: {str(google_error)}")
        raise Exception(f"Failed to fetch events from calendar ID {calendar_id}.")
    except Exception as e:
        logger.error(f"Unexpected error fetching calendar events: {str(e)}")
        raise

# Função principal da Lambda
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    try:
        # Extrai o corpo da requisição POST
        body = json.loads(event.get('body', '{}'))

        # Valida os parâmetros esperados
        required_fields = ['user_id', 'calendar_id', 'start_time', 'end_time']
        for field in required_fields:
            if field not in body:
                raise ValueError(f"Missing required field: {field}")

        # Pega os parâmetros do corpo da requisição
        user_id = body['user_id']
        calendar_id = body['calendar_id']
        start_time = body['start_time']
        end_time = body['end_time']

        logger.info(f"Request received to fetch events for user_id={user_id}, calendar_id={calendar_id}, "
                    f"start_time={start_time}, end_time={end_time}")

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
    
    except ValueError as ve:
        logger.warning(f"Validation error: {str(ve)}")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': str(ve)}),
            'headers': {
                'Content-Type': 'application/json'
            }
        }
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}")
        traceback.print_exc()
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
            'headers': {
                'Content-Type': 'application/json'
            }
        }
