from functools import cmp_to_key
import logging
import re
import urllib.parse

from bs4 import BeautifulSoup
from cmp_version import cmp_version
import requests

from . import Release, Vendor, registry

logger = logging.getLogger('vendor.netgear')

@registry.register
class Netgear(Vendor):
    def id():
        return 'netgear'

    def name(self):
        return 'Netgear'

    def get_latest(self, device):
        r = requests.get('https://www.netgear.com/support/product/%s' % urllib.parse.quote(device.model))
        logger.debug('Response status for %s: %d', device.model, r.status_code)
        r.raise_for_status()

        soup = BeautifulSoup(r.content, "lxml")
        # Find downloads with release notes
        latest_releases = soup.find(id='topicsdownload').find(class_='latest-version').find_all("a", string=re.compile('^Release Notes'))
        versions = {}
        for link in latest_releases:
            release = link.parent.parent
            title = release.find(re.compile("^h")).string
            version = self._normalize_release(title)
            if not version:
                logger.debug("Skipping non-release %s", title)
                continue
            download_link = release.find("a", class_="btn")['href']
            versions[version] = {'download': download_link, 'docs': link['href']}
        if not versions:
            logger.warning("Failed to find any released versions for %s", device.model)
            return None
        latest = sorted(list(versions.keys()), key=cmp_to_key(cmp_version), reverse=True)[0]
        return Release(version=latest, download_url=versions[latest]['download'], docs_url=versions[latest]['docs'])

    def _normalize_release(self, title):
        match = re.search("Version ([0-9a-z.]+)", title)
        if not match:
            return None
        return match.group(1)

