import sys
import requests
import atexit
import random

from bs4 import BeautifulSoup
import lxml


class TwitchHelper:
    OK_CODE = 200

    def __init__(self, client_id: str, client_secret: str):
        self._client_id = client_id
        self._client_secret = client_secret
        self._get_token()
        atexit.register(self._revoke_token)

    def _get_token(self):
        get_token_url = \
            f'https://id.twitch.tv/oauth2/token' \
            f'?client_id={self._client_id}' \
            f'&client_secret={self._client_secret}' \
            f'&grant_type=client_credentials'

        response = requests.post(get_token_url)
        if response.status_code == self.OK_CODE:
            # print("GOT TOKEN:", response.json()['access_token'], file=sys.stderr)
            self._token = response.json()['access_token']

    def _token_lifetime(self):
        validate_token_url = 'https://id.twitch.tv/oauth2/validate'
        headers = {
            'Authorization': ' '.join(['OAuth', self._token])
        }

        response = requests.get(validate_token_url, headers=headers)
        if response.status_code == self.OK_CODE:
            return response.json()['expires_in']
        return 0

    def _revoke_token(self):
        revoke_token_url = \
            f'https://id.twitch.tv/oauth2/revoke' \
            f'?client_id={self._client_id}' \
            f'&token={self._token}'

        # print("REVOKE TOKEN:", self._token, file=sys.stderr)
        requests.post(revoke_token_url)

    def get_client_id(self):
        return self._client_id

    def get_client_secret(self):
        return self._client_secret

    def get_token(self):
        return self._token

    def update_token(self, min_duration=60):
        if self._token_lifetime() < min_duration:
            self._revoke_token()
            self._get_token()


class TwitchRequests:
    OK_CODE = 200
    OK_LANGUAGE_CODES = ['en', 'ru']

    def __init__(self, client_id: str, client_secret: str):
        self._twitch_client = TwitchHelper(
            client_id=client_id,
            client_secret=client_secret,
        )
        self._streams = []

    @staticmethod
    def from_id_and_secret_path(id_file_path: str, secret_file_path: str):
        with open(id_file_path) as f1:
            client_id = f1.read()
        with open(secret_file_path) as f2:
            client_secret = f2.read()
        return TwitchRequests(client_id=client_id, client_secret=client_secret)

    def search_for_section(self, query: str, result_size=20):
        self._twitch_client.update_token()

        search_url = \
            f'https://api.twitch.tv/helix/search/categories' \
            f'?query={query}' \
            f'&first={result_size}'
        headers = {
            'Authorization': ' '.join(['Bearer', self._twitch_client.get_token()]),
            'Client-Id': self._twitch_client.get_client_id(),
        }

        response = requests.get(search_url, headers=headers)
        if response.status_code == self.OK_CODE:
            return response.json()['data']
        return []

    def get_streams_info(self, category_name: str, max_viewers=20, max_amount=1000, per_page=100):
        self._twitch_client.update_token()

        categories_info = self.search_for_section(category_name)
        game_id = 0
        for game in categories_info:
            if game['name'] == category_name:
                game_id = game['id']
                break

        streams = []

        cursor = None
        streams_search_url = \
            f'https://api.twitch.tv/helix/streams' \
            f'?first={per_page}' \
            f'&game_id={game_id}'

        for l in self.OK_LANGUAGE_CODES:
            streams_search_url += f'&language={l}'

        if cursor is not None:
            streams_search_url += f'&after={cursor}'

        headers = {
            'Authorization': ' '.join(['Bearer', self._twitch_client.get_token()]),
            'Client-Id': self._twitch_client.get_client_id(),
        }

        response = requests.get(streams_search_url, headers=headers)
        while len(streams) < max_amount and response.status_code == 200 and len(response.json()['data']) != 0:
            cursor = response.json()['pagination']['cursor']
            for stream in response.json()['data']:
                if stream['viewer_count'] <= max_viewers:
                    streams.append(stream)

            streams_search_url = \
                f'https://api.twitch.tv/helix/streams' \
                f'?first={per_page}' \
                f'&game_id={game_id}'

            for l in self.OK_LANGUAGE_CODES:
                streams_search_url += f'&language={l}'

            if cursor is not None:
                streams_search_url += f'&after={cursor}'

            response = requests.get(streams_search_url, headers=headers)

        self._streams = streams

    def get_sample(self, amount=10):
        if len(self._streams) < amount:
            return self._streams
        return random.sample(self._streams, amount)


class CopypastaFinder:
    copypastas = []
    credits = []

    def __init__(self, max_page=1):
        for page_num in range(1, max_page + 1):
            url = f'https://www.twitchquotes.com/copypastas/labels/classic?page={page_num}'
            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'lxml')
            for copypasta in soup.find_all('div', '-copypasta'):
                text = copypasta.text.strip()
                text.replace("\r\n", "<br>")
                text.replace("\n", "<br>")
                self.copypastas.append(text)
            for url_part in soup.find_all('a', '-date'):
                self.credits.append('https://www.twitchquotes.com' + url_part['href'])

    def random_copypasta(self):
        index = random.randint(0, len(self.copypastas) - 1)
        return [self.copypastas[index], self.credits[index]]


class DadJoke:
    OK_CODE = 200
    ERROR_MESSAGE = 'No joke :('

    def __init__(self):
        self._user_agent = 'My API hw https://github.com/NightRS'

    def get_random_joke(self):
        url = 'https://icanhazdadjoke.com/'
        headers = {
            'User-Agent': self._user_agent,
            'Accept': 'application/json',
        }

        response = requests.get(url, headers=headers)
        if response.status_code == self.OK_CODE:
            return [response.json()['joke'], 'https://icanhazdadjoke.com/j/' + response.json()['id']]
        return [self.ERROR_MESSAGE, '']
