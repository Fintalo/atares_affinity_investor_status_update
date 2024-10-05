import azure.functions as func
import logging
import requests
from requests.auth import HTTPBasicAuth
import os

"""
Overview:
Used CRM: Affinity
This code works project based. That means it need the id of a opportunity and the id of the status field within the opportunity list.
(Every projectxCompany should have a opportunity id and every project a status field id)
Whenever there is a status change this code takes the status id and converts it into the corresponding status id in affintiy.
The last step ist to take the STATUS_FIELD id, the STATUS id and the OPPORTUNITY id to change the id in Affintiy

STILL MISSING:
Wir brauchen noch eine Liste wann unser system einen status update vorschlägt mit einer ID für jeden vorgeschlagenen Status update.
Damit muss einer azure function nur eine id von unseren status updates übergeben werden und dann wird in diesem Code einfach diese ID in die entsprechende status id in Affinity "übersetzt"
"""

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="atares_status_update")
def atares_status_update(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')


    """
    Set up
    """

    #receive all data
    try:
        req_body = req.get_json()

        #get variables
        opportunityId = req_body.get('opportunityId')
        statusFieldId = req_body.get('statusFieldId')
        listId = req_body.get('listId')

    except ValueError:
        return func.HttpResponse(
            "Invalid JSON format.",
            status_code=400
        )
    
    

    """
    Functions
    """

    def get_field_value_id_by_field_id(data, target_field_id):
        """
        Sucht nach einem Feld mit einem bestimmten field_id und gibt die zugehörige ID zurück.
        
        :param data: Liste der Felddaten (API-Antwort)
        :param target_field_id: Die gesuchte field_id
        :return: Die ID des Feldes, wenn es gefunden wird, ansonsten None
        """
        for field in data:
            if field.get('field_id') == target_field_id:
                return field.get('id')  # Gibt die ID des Feldes zurück
        return None  # Falls kein Feld mit dem gesuchten field_id gefunden wurde


    
    """
    Ziehe alle Field values der Opportuity
    """
    try:
        # URL und Authentifizierung festlegen
        url_get = "https://api.affinity.co/field-values"
        auth_get = HTTPBasicAuth('', os.getenv("Affinity_Token"))  # Leerzeichen für den Benutzernamen

        
        headers = {
            "Content-Type": 'application/json'
        }
        
        # Query-Parameter für die Anfrage
        query = {
            "opportunity_id": opportunityId,
        }

        # HTTP GET-Anfrage an die API senden
        response = requests.get(url_get, auth=auth_get, headers=headers, params=query)

        # Sicherstellen, dass der Request erfolgreich war
        response.raise_for_status()

        # JSON-Daten aus der Antwort abrufen
        data_response = response.json()


    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")  # HTTP-Fehlerprotokollierung
        return func.HttpResponse(
            f"HTTP error occurred: {http_err}",
            status_code=response.status_code
        )
    except requests.exceptions.RequestException as req_err:
        logging.error(f"Error during request: {req_err}")  # Fehler bei der Anfrage
        return func.HttpResponse(
            "Error during request.",
            status_code=500
        )
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")  # Allgemeine Fehlerprotokollierung
        return func.HttpResponse(
            "An unexpected error occurred.",
            status_code=500
        )
    
    """
    Filtere alle Field Values der Opportunity um genau das eine Statusfeld zu bekommen
    """
    field_value_id = get_field_value_id_by_field_id(data_response,4696869)

    url_put = f'https://api.affinity.co/field-values/{field_value_id}'

    # Authentifizierung mit API-Key (der Benutzername bleibt leer)
    auth_put = HTTPBasicAuth('', os.getenv("Affinity_Token"))

    # Header für den Request
    headers = {
        "Content-Type": "application/json"
    }

    # Daten, die gesendet werden sollen (JSON-Format)
    data = {
        "value": 15023456 #Hier die id aus dem Dropbown einfügen !!!!!
    }

    # Sende den PUT-Request
    response = requests.put(url_put, auth=auth_put, headers=headers, json=data)


    return func.HttpResponse(
                "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
                status_code=200
            )







    # Mit diesem Anstz würden wir erst alle status Felder einer liste bekommen und dann nach unserer Opportunity suchen
    # -> Interessant für die Zukunft, wenn Affintiy API v2 auch PUT calls unterstützt
    """
    #store data in variables
    list_id = req_body.get('listId')
    statusFieldId = req_body.get('statusFieldId')
    
    url = "https://api.affinity.co/v2/lists/" + list_id + "/list-entries"

    query = {
    "cursor": "",
    "limit": "200",
    "fieldIds": statusFieldId,
    "fieldTypes": "enriched"
    }

    headers = {"Authorization": f'Bearer {os.getenv("Affinity_Token")}'}

    response = requests.get(url, headers=headers, params=query)

    data = response.json()
    """
    
    