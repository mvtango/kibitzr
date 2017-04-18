from time import sleep
import requests
import logging
from kibitzr import __version__ as version


logger = logging.getLogger(__name__)


class SessionFetcher(object):
    def __init__(self, conf):
        self.conf = conf
        self.session = requests.Session()
        self.session.headers.update({
            'User-agent': 'Kibitzer/' + version,
        })
        self.url = conf['url']
        self.valid_http = set(conf.get('valid_http', [200]))
        self.last_headers = {'last-modified': False, 'etag': False}

    def fetch(self, *args, **_kwargs):
        retries = 3
        headers = {}
        if self.last_headers["last-modified"]:
            headers["If-Modified-Since"] = self.last_headers["last-modified"]
        elif self.last_headers["etag"]:
            headers["If-None-Match"] = self.last_headers["etag"]
        for retry in range(retries):
            try:
                response = self.session.get(self.url, headers=headers)
            except requests.HTTPError:
                if retry == retries - 1:
                    raise
                else:
                    sleep(5)
                    continue
            except requests.ConnectionError:
                if retry == retries - 1:
                    raise
                else:
                    sleep(15)
                    continue
            if response.status_code == 200:
                for k in self.last_headers.keys():
                    v = response.headers.get(k, False)
                    if v:
                        self.last_headers[k] = v
                        logger.debug(
                           "{self.url} - {k}: {v}".format(**locals())
                        )
            elif response.status_code == 304:
                    logger.debug(
                        "{self.url} - {response.status_code}".format(
                         **locals()
                         )
                    )
            ok = (response.status_code in self.valid_http)
            return ok, response.text
