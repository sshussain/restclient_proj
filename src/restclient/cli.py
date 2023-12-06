import logging

import click
from click import echo
from restclient import client
from restclient import util

__all__ = ['execute']


def prettify_body(content_type: dict, body: str) -> str:
    if (
        'application/xml' in content_type
        or 'application/soap+xml' in content_type
    ):
        return util.prettify_xml(body)
    if 'application/json' in content_type:
        return util.prettify_json(body)
    if 'application/kong+json' in content_type:
        return util.prettify_json(body)
    # if 'text/html' in content_type:
    #     from bs4 import BeautifulSoup
    #     print(BeautifulSoup(body, 'html.parser').prettify(encoding='utf-8'))
    return body


@click.command()
@click.option(
    '-s',
    '--silent',
    default=False,
    is_flag=True,
    help='Do not emit log or error messages',
)
@click.option('-i', '--ini', help='Client configuration in TOML format')
@click.option(
    '-p',
    '--profile',
    help='Profile contains infornation required to access endpoint. For example: URL, authentication',
)
@click.option('-m', '--method', help='HTTP Method. The default is POST')
@click.option('-d', '--datafile', help='Data file')
@click.argument('url', type=str, nargs=1)
def execute(silent, ini, profile, datafile, url, method):
    """restclient is a simple client to test server endpoints.
     An endpoint is defined by HTTP or HTTPS URL

    The HTTP method may be specified by -m option. For now, POST is the default HTTP method.

     The restclient behaviour can be modified by configuration file, and a profile name.

     For now profile is a simple name-to-url map. The profile file name and its location is hardcoded.

     - Profile file: profile.url

     - Path: ${HOME}/etc/restclient

     Example basic:

     -------------

     restclient testmessage.json http://my.company.comp/api


     Example: No profile

     -------------

     restclient -i simple.toml testmessage.json http://my.company.comp/api

     Example: With profile

     -------------

     restclient -i simple.toml -p mycompany testmessage.json

     Here profile.toml will have

     mycompany = "http://my.company.comp/api" entry

     Example: GET

     -------------

     restclient -m GET http://yahoo.com

    """
    logging.info(
        f'CLI params\n===\n  Configuration file: {ini}\n  HTTP Method: {method}\n '
        f' Profile: {profile}\n  Data file: {datafile}\n '
        f' Endpoint: {url}\n==\n'
    )
    if silent:
        logging.disable()

    # Disable validation of URL format
    # if not util.url_check(url):
    #     echo('Malformed URL ' + url)
    #     return
    if datafile:
        if not util.file_check(datafile):
            echo('Data file ' + datafile + ' not found or is not a file')
            return
    if ini:
        if not util.file_check(ini):
            echo('Configuration file ' + ini + ' not found or is not a file')
            return

    status, headers, body = client.client(ini, profile, datafile, url, method)

    content_type = headers['Content-Type']
    logging.info(
        f'Response\n===\n Status code => {status}\n Content-type => {content_type}\n===\n'
    )
    logging.debug(f'Headers =>\n  {headers}')
    pb = prettify_body(content_type, body)
    logging.debug(f'Body\n====\n   {pb}\n====\n')

