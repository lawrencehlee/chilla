import requests

class TwitchStreams:
    def __init__(self, client_id, client_secret, game_id):
        self.client_id = client_id
        self.client_secret = client_secret
        self.game_id = game_id
        self.access_token = ""

    def get_access_token(self):
        url = f'https://id.twitch.tv/oauth2/token?client_id={self.client_id}&client_secret={self.client_secret}&grant_type=client_credentials'
        response = requests.post(url)

        if response.status_code == 200:
            response_json = response.json()
            self.access_token = response_json['access_token']
            return response_json['access_token']
        else:
            response_json = response.json()
            return None

    def validate_access_token(self):
        headers = {
            'Content-type': 'application/json',
            'Authorization': f'Bearer {self.access_token}',
            'Client-Id': f'{self.client_id}',
        }

        url = f'https://id.twitch.tv/oauth2/validate'
        response = requests.get(url, headers=headers)
        return response.status_code == 200

    def get_streams(self):
        if not self.validate_access_token():
            try:
                self.access_token = self.get_access_token()
            except Exception as error:
                print(error)
        print(self.access_token)
        headers = {
            'Content-type': 'application/json',
            'Authorization': f'Bearer {self.access_token}',
            'Client-Id': f'{self.client_id}',
        }
        url = f'https://api.twitch.tv/helix/streams?first=5&game_id={self.game_id}'
        response = requests.get(url, headers=headers)
        return response.json()
        
