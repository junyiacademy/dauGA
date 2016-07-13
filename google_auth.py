from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from httplib2 import Http


class google_auth:
    credential_path = "./credential.json"
    types = {
        'analytics_v4': {
            'api_name': 'analyticsreporting',
            'scope': 'https://www.googleapis.com/auth/analytics',
            'version': 'v4'
        },
        'bigquery_v2': {
            'api_name': 'bigquery',
            'scope': 'https://www.googleapis.com/auth/bigquery',
            'version': 'v2'
        },
        'storage_v1': {
            'api_name': 'storage',
            'scope': 'https://www.googleapis.com/auth/cloud-platform',
            'version': 'v1'
        }
    }

    def __init__(self, path):
        self.credential_path = path

    def get_auth(self, name):
        if name in self.types:
            credentials = ServiceAccountCredentials.from_json_keyfile_name(self.credential_path, self.types[name]['scope'])
            http_auth = credentials.authorize(Http())
            auth_object = build(self.types[name]['api_name'], self.types[name]['version'], http=http_auth)
            return auth_object
        else:
            raise LookupError('There is no such type!')
