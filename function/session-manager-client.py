import swagger_client
import base64
import requests
import json
import sys
from swagger_client.models.describe_sessions_request_data import DescribeSessionsRequestData
from swagger_client.models.key_value_pair import KeyValuePair
from swagger_client.models.delete_session_request_data import DeleteSessionRequestData
from swagger_client.models.update_session_permissions_request_data import UpdateSessionPermissionsRequestData
from swagger_client.models.create_session_request_data import CreateSessionRequestData

__CLIENT_ID = '1ec9f1b8-f930-420e-b69f-4af44f3dab68'
__CLIENT_SECRET = 'MTQ5YTliNWMtN2RmNy00MjI3LTliMmMtMzU5NDBkMGY2NDVl'
__PROTOCOL_HOST_PORT = 'https://ec2-3-81-149-42.compute-1.amazonaws.com:8443'

def build_client_credentials():
    client_credentials = '{client_id}:{client_secret}'.format(client_id=__CLIENT_ID, client_secret=__CLIENT_SECRET)
    return base64.b64encode(client_credentials.encode('utf-8')).decode('utf-8')
		
def get_access_token():
    client_credentials = build_client_credentials()
    headers = {
        'Authorization': 'Basic {}'.format(client_credentials),
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    endpoint = __PROTOCOL_HOST_PORT + '/oauth2/token?grant_type=client_credentials'
    print('Calling', endpoint, 'using headers', headers)
    res = requests.post(endpoint, headers=headers, verify=False)
    if res.status_code != 200:
        print('Cannot get access token:', res.text)
        return None
    access_token = json.loads(res.text)['access_token']
    print('Access token is', access_token)
    return access_token

def get_client_configuration():
    configuration = swagger_client.Configuration()
    configuration.host = __PROTOCOL_HOST_PORT
    configuration.verify_ssl = False
    # configuration.ssl_ca_cert = cert_file.pem
    return configuration

def set_request_headers(api_client):
    access_token = get_access_token()
    api_client.set_default_header(header_name='Authorization',
                                  header_value='Bearer {}'.format(access_token))

def get_sessions_api():
    api_instance = swagger_client.SessionsApi(swagger_client.ApiClient(get_client_configuration()))
    set_request_headers(api_instance.api_client)
    return api_instance
		
def describe_sessions(session_ids=None, next_token=None, tags=None, owner=None):
    filters = list()
    if tags:
        for tag in tags:
            filter_key_value_pair = KeyValuePair(key='tag:' + tag['Key'], value=tag['Value'])
            filters.append(filter_key_value_pair)
    if owner:
        filter_key_value_pair = KeyValuePair(key='owner', value=owner)
        filters.append(filter_key_value_pair)

    request = DescribeSessionsRequestData(session_ids=session_ids, filters=filters, next_token=next_token)
    print('Describe Sessions Request:', request)
    api_instance = get_sessions_api()
    api_response = api_instance.describe_sessions(body=request)
    print('Describe Sessions Response', api_response)

def create_sessions(sessions_to_create):
    create_sessions_request = list()
    for name, owner, session_type, init_file_path, max_concurrent_clients,\
            dcv_gl_enabled, permissions_file, requirements in sessions_to_create:
        a_request = CreateSessionRequestData(
            name=name, owner=owner, type=session_type,
            init_file_path=init_file_path, max_concurrent_clients=max_concurrent_clients,
            dcv_gl_enabled=dcv_gl_enabled, permissions_file=permissions_file, requirements=requirements)
        create_sessions_request.append(a_request)

    api_instance = get_sessions_api()
    print('Create Sessions Request:', create_sessions_request)
    api_response = api_instance.create_sessions(body=create_sessions_request)
    print('Create Sessions Response:', api_response)    

def get_session_connection_api():
    api_instance = swagger_client.GetSessionConnectionDataApi(swagger_client.ApiClient(get_client_configuration()))
    set_request_headers(api_instance.api_client)
    return api_instance

def get_session_connection_data(session_id, user):
    api_response = get_session_connection_api().get_session_connection_data(session_id=session_id, user=user)
    print('Get Session Connection Data Response:', api_response)

def delete_sessions(sessions_to_delete, force=False):
    delete_sessions_request = list()
    for session_id, owner in sessions_to_delete:
        a_request = DeleteSessionRequestData(session_id=session_id, owner=owner, force=force)
        delete_sessions_request.append(a_request)

    print('Delete Sessions Request:', delete_sessions_request)
    api_instance = get_sessions_api()
    api_response = api_instance.delete_sessions(body=delete_sessions_request)
    print('Delete Sessions Response', api_response)

def main(arg):
    action = arg[0]
    params = arg[1:]

    # if there is a valid action go ahead, otherwise exit
    if ('create' in action or 'describe' in action or 'connection' in action or 'delete' in action):
        # Windows DCV only accepts CONSOLE sessions
        # Windows DCV does not accept InitFilePath 
        # Windows DCV does not accept DcvGlEnabled (only used with VIRTUAL sessions)
        # 
        # Name, Owner, Type, InitFilePath, MaxConcurrents, DcvGlEnabled, PermissionsFile, tags (format: "tag_key = tag_value")
        if (action == 'create'):
            create_sessions([
                ('session1', 'Administrator', 'CONSOLE', None, None, None, None, None)    
            ])

        # Describe can be used with or without a filter
        # filter is based on tags, sesionid, owner
        if (action == 'describe'):
            print('\n Describing session... \n ')
            describe_sessions()

        # GetSessionConnectionData gets you the connection token and the sessionId
        # use that information to build your connection URL / .dcv file
        if (action == 'connection'):
            print('\n Session connection data... \n ')
            get_session_connection_data('0695d9cc-9100-4ee0-a861-8ff0cbd3afce', 'Administrator')

        # DeleteSession requires sessionId and owner
        if (action == 'delete'):
            print('\n Deleting session... \n')
            delete_sessions([('0695d9cc-9100-4ee0-a861-8ff0cbd3afce', 'Administrator')])
    else:
        print('No valid action found. Exiting.')

if __name__ == "__main__":
    main(sys.argv[1:])
