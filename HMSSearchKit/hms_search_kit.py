# Created by Sezer BOZKIR<admin@sezerbozkir.com at 2/24/2021
import requests
from http import HTTPStatus
from datetime import datetime, timedelta
from functools import wraps


class AccessTokenError(Exception):
    """API Call cannot complete properly."""


class HMSSearchKit:
    """
    How to find Client ID and Client Secret:
    https://developer.huawei.com/consumer/en/doc/development/HMSCore-Guides-V5/open-platform-oauth-0000001053629189-V5
    Supported languages:
    https://developer.huawei.com/consumer/en/doc/development/HMSCore-References-V5/language-code-0000001057569148-V5
    Supported Regions:
    https://developer.huawei.com/consumer/en/doc/development/HMSCore-References-V5/search-region-code-0000001057330966-V5
    result_count min:1 max:100 default:10
    result_page min:1 max:100 default:1
    Paramter details:
    https://developer.huawei.com/consumer/en/doc/development/HMSCore-References-V5/web-search-0000001056849539-V5#EN-US_TOPIC_0000001056849539__section3593201613611
    Error code details:
    https://developer.huawei.com/consumer/en/doc/development/HMSCore-References-V5/error-code-0000001055689455-V5
    """

    token_url = "https://oauth-login.cloud.huawei.com/oauth2/v3/token"
    query_url: str = "https://search-dre.cloud.huawei.com/apis/search/v1.0.0/{query_type}/search"
    token_parameters = {
        'grant_type': 'client_credentials',
        'client_id': '',
        'client_secret': ''
    }
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': 'Bearer ',
        'X-Kit-AppID': '102445919'
    }
    access_token = None
    access_token_expire = None

    def __init__(self, client_id: str, client_secret: str):
        self.token_parameters['client_id'] = client_id
        self.token_parameters['client_secret'] = client_secret

    def get_token(self):
        if self.access_token and datetime.now() <= self.access_token_expire:
            return self.access_token
        resp = requests.post(self.token_url, data=self.token_parameters)
        if resp.status_code != HTTPStatus.OK:
            raise AccessTokenError("ERROR: Access token cannot created:" + resp.reason)
        else:
            resp_content = resp.json()
        self.access_token = resp_content["access_token"]
        self.access_token_expire = datetime.now() + timedelta(seconds=resp_content['expires_in'])
        self.headers['Authorization'] += self.access_token

    def _token_valid_check(f):
        @wraps(f)
        def wrapped(inst, *args, **kwargs):
            if not inst.access_token or datetime.now() <= inst.access_token_expire:
                inst.get_token()
            return f(inst, *args, **kwargs)

        return wrapped

    def _prepare_params(self, string_query, language, regions, result_count, result_page):
        params = {
            "q": string_query
        }
        if language:
            params['language'] = language
        if regions:
            params['sregion'] = regions
        if result_count:
            params['ps'] = result_count
        if result_page:
            params['pn'] = result_page
        return params

    @_token_valid_check
    def search(self, string_query, result_count, page_count, regions, language):
        print(self.access_token)

    @_token_valid_check
    def _base_search(self, query_type, string_query, language, regions, result_count, result_page):
        params = self._prepare_params(string_query, language, regions, result_count, result_page)
        url = self.query_url.format(query_type=query_type)
        resp = requests.get(url, headers=self.headers, params=params)
        if resp.status_code == HTTPStatus.OK:
            result = {
                'search_type': query_type,
                'search_string': string_query,
                'count': len(resp.json()['data']),
                'search_results': resp.json()['data']
            }
            return result
        return {resp.status_code: resp.reason}

    def web_search(self, string_query: str, language=None, regions=None, result_count=None, result_page=None):
        return self._base_search("web", string_query, language, regions, result_count, result_page)

    def image_search(self, string_query: str, language=None, regions=None, result_count=None, result_page=None):
        return self._base_search("image", string_query, language, regions, result_count, result_page)

    def video_search(self, string_query: str, language=None, regions=None, result_count=None, result_page=None):
        return self._base_search("video", string_query, language, regions, result_count, result_page)

    def news_search(self, string_query: str, language=None, regions=None, result_count=None, result_page=None):
        return self._base_search("news", string_query, language, regions, result_count, result_page)

    def full_search(self, string_query: str, language=None, regions=None, result_count=None, result_page=None):
        web_search_result = self.web_search(string_query, language, regions, result_count, result_page)
        image_search_result = self.image_search(string_query, language, regions, result_count, result_page)
        video_search_result = self.video_search(string_query, language, regions, result_count, result_page)
        news_search_result = self.news_search(string_query, language, regions, result_count, result_page)
        collected_results = {
            'search_type': "all",
            'search_string': string_query,
            'count': web_search_result['count'] +
                     image_search_result['count'] +
                     video_search_result['count'] +
                     news_search_result['count'],
            'search_results': web_search_result['search_results'] +
                              image_search_result['search_results'] +
                              video_search_result['search_results'] +
                              news_search_result['search_results']
        }
        return collected_results


if __name__ == '__main__':
    client = HMSSearchKit("YOUR_CLIENT_ID", "YOUR_CLIENT_SECRET")
    client.web_search("sezer bozkır", language="tr", regions='tr', result_count=5, result_page=2)
    client.image_search("sezer bozkır")
    client.video_search("sezer bozkır")
    client.news_search("sezer bozkır")
    client.full_search("sezer bozkir")
