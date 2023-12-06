import logging
import pathlib

import requests
import tomli
from oauthlib.oauth2 import LegacyApplicationClient
from requests import Response
from requests.auth import HTTPBasicAuth
from requests_oauthlib import OAuth2Session

__all__ = ['client']


def _read_from_file(filename: str):
    data = ''
    with open(filename, 'r') as f:
        data = f.read()
    return data


def _read_config(config_file: str) -> dict:
    """Read client configuration

    :param config_file: Configuration file in TOML format
    :return: Dictionary created from parsed TOML file
    """
    with open(config_file, 'rb') as f:
        return tomli.load(f)


def _read_profile(profile):
    """
    Read endpoint URL for the given profile. The profile.toml is located at ~/etc/rc/profile.toml
    """
    p = _read_config('~/etc/rc/profile.toml')
    u = p[profile]
    return u


def _fetch_token(
    username, password, url, client_id, client_secret, grant_type
):
    """Fetch Bearer token from IDP
    :param username: Username avaiable in IDP
    :param password: Password bound to the username in IDP
    :param url: IDP access token URL
    :param client_id:
    :param client_secret:
    :param grant_type: Configured OAUTH2 token grant permission
    ...
    :return: Bearer token as string
    """
    oauth = OAuth2Session(client=LegacyApplicationClient(client_id=client_id))
    token = oauth.fetch_token(
        token_url=url,
        username=username,
        password=password,
        client_id=client_id,
        client_secret=client_secret,
        verify=False,
    )
    # return token.get('access_token', default=None)
    return token.get('access_token')


def _post_with_basic_auth(
    endpoint: str, data: str, headers, username: str, password: str
) -> Response:
    """

    :param endpoint:
    :param data:
    :param headers:
    :param username:
    :param password:
    :return: class:`requests.Response`
    """
    auth = HTTPBasicAuth(username, password)
    return requests.post(endpoint, data, headers, auth=auth)


def _post_with_oauth2(
    endpoint,
    data,
    headers,
    username,
    password,
    grant_type,
    access_token_url,
    client_id,
    client_secret,
) -> Response:
    """

    :param endpoint:
    :param data:
    :param headers:
    :param username:
    :param password:
    :param grant_type:
    :param access_token_url:
    :param client_id:
    :param client_secret:
    :return: class:`requests.Response`
    """
    tstr = _fetch_token(
        username,
        password,
        access_token_url,
        client_id,
        client_secret,
        grant_type,
    )
    headers['Authorization'] = 'Bearer ' + tstr
    return requests.post(endpoint, data, headers=headers)


def _do_simple_post(endpoint, data, headers) -> Response:
    return requests.post(endpoint, data, headers)


def _do_post(configuration, endpoint, data, headers) -> Response:
    """

    :param configuration:
    :param endpoint:
    :param data:
    :param headers:
    :return: class:`requests.Response`
    """
    logging.info(f'_do_post() {configuration}, endpoint {endpoint}')
    # Check is configuration is empty
    if not configuration:
        return _do_simple_post(endpoint, data, headers)

    if configuration['auth_type'] == 'NONE':
        return requests.post(endpoint, data=data, headers=headers)

    if configuration['auth_type'] == 'BASIC':
        username = configuration['username']
        password = configuration['password']
        return _post_with_basic_auth(
            endpoint, data, headers, username, password
        )

    if configuration['auth_type'] == 'OAUTH2':
        username = configuration['username']
        password = configuration['password']
        grant_type = configuration['grant_type']
        access_token_url = configuration['access_token_url']
        client_id = configuration['client_id']
        client_secret = configuration['client_secret']
        return _post_with_oauth2(
            endpoint,
            data,
            headers,
            username,
            password,
            grant_type,
            access_token_url,
            client_id,
            client_secret,
        )


def _get_with_basic_auth(endpoint, headers, username, password) -> Response:
    """

    :param endpoint:
    :param headers:
    :param username:
    :param password:
    :return:
    """
    auth = HTTPBasicAuth(username, password)
    return requests.get(endpoint, headers, auth=auth)


def _get_with_oauth2(
    endpoint,
    headers,
    username,
    password,
    grant_type,
    access_token_url,
    client_id,
    client_secret,
) -> Response:
    """

    :param endpoint:
    :param headers:
    :param username:
    :param password:
    :param grant_type:
    :param access_token_url:
    :param client_id:
    :param client_secret:
    :return:
    """
    tstr = _fetch_token(
        username,
        password,
        access_token_url,
        client_id,
        client_secret,
        grant_type,
    )
    headers['Authorization'] = 'Bearer ' + tstr
    return requests.get(endpoint, headers=headers)


def _do_get(configuration, endpoint, headers) -> Response:
    """

    :param configuration:
    :param endpoint:
    :param headers:
    :return:
    """
    if not configuration:
        return requests.get(endpoint, headers=headers)

    if configuration['auth_type'] == 'NONE':
        return requests.get(endpoint, headers=headers)

    if configuration['auth_type'] == 'BASIC':
        username = configuration['username']
        password = configuration['password']
        return _get_with_basic_auth(endpoint, headers, username, password)

    if configuration['auth_type'] == 'OAUTH2':
        username = configuration['username']
        password = configuration['password']
        grant_type = configuration['grant_type']
        access_token_url = configuration['access_token_url']
        client_id = configuration['client_id']
        client_secret = configuration['client_secret']
        return _get_with_oauth2(
            endpoint,
            headers,
            username,
            password,
            grant_type,
            access_token_url,
            client_id,
            client_secret,
        )


def client(
    inifile: str, profile: str, datafile: str, endpoint: str, method: str
) -> tuple:
    r"""Performs HTTP POST request to given endpoint.

    :param method: HTTP Method
    :param profile: search profile in ~/etc/rc/profile.toml
    :param inifile: TOML file containing authentication information
    :param datafile: file contoins HTTP request body contents
    :param endpoint: destination URI
    ...
    :return Response status code, headers, and body contents
    :rtype: tuple
    ...
    """
    import requests

    requests.packages.urllib3.disable_warnings(
        requests.packages.urllib3.exceptions.InsecureRequestWarning
    )

    # Read profile to get endpoint url
    #  if the given profile is not present, use given url
    # exit if given url is also not present
    eurl = endpoint
    if profile:
        eurl = _read_profile(profile)
    if not eurl:
        logging.error(f'Could not find the endpoint {eurl}')
        raise ValueError(
            'Could not  locate endpoint in a profile file, or is not specified on command line.'
        )

    configuration = {}
    if inifile:
        configuration = _read_config(inifile)

    if method and method.upper() == 'GET':
        r: Response = _do_get(configuration, eurl, headers={'Accept': '*/*'})
        return r.status_code, r.headers, r.text

    suffix = pathlib.Path(datafile).suffix
    suffix = suffix.replace('.', '')
    content_type = 'unknown'
    if suffix in 'xml':
        content_type = 'application/xml'
    elif suffix == 'json':
        content_type = 'application/json'
    elif suffix in 'kongjson':
        content_type = 'application/kong+json'
    else:
        content_type = 'text/plain'
    data = _read_from_file(datafile)

    r: Response = _do_post(
        configuration, eurl, data, headers={'Content-Type': content_type}
    )
    return r.status_code, r.headers, r.text

