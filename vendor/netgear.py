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
        if device.model.startswith('C') or device.model.startswith('N450'):
            return self._cable_modem_latest(device)
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
            file_size = None
            size_match = re.search(r'File\ssize:\s([0-9.]+\s*[A-Za-z]+)', release.get_text())
            if size_match:
                file_size = size_match.group(1)
            versions[version] = {'download': download_link, 'docs': link['href'], 'size': file_size}
        if not versions:
            logger.warning("Failed to find any released versions for %s", device.model)
            return None
        latest = sorted(list(versions.keys()), key=cmp_to_key(cmp_version), reverse=True)[0]
        version = versions[latest]
        return Release(version=latest, download_url=version['download'], docs_url=version['docs'], file_size=version['size'])

    def _normalize_release(self, title):
        match = re.search("Version ([0-9a-z.]+)", title)
        if not match:
            return None
        return match.group(1)

    def _cable_modem_latest(self, device):
        """Cable modems and routers are managed by the providers(?). Model name is expected to include the provider name in brackets"""
        match = re.match(r'^([A-Z]+[0-9vV]+) \[([A-Za-z]+)\]', device.model)
        if not match:
            raise ValueError('Cable model model needs to be in format of "<model id> [<Comcast|Spectrum|Cox|Other>]"')
        model_id = match.group(1)
        provider = match.group(2)
        if provider == 'Other':
            provider = 'All other ISPs'

        # TODO: Determine why kb cert fails
        docs_url = 'https://kb.netgear.com/000036375/What-s-the-latest-firmware-version-of-my-NETGEAR-cable-modem-or-modem-router'
        r = requests.get(docs_url, verify=False)
        logger.debug('Response status for %s: %d', device.model, r.status_code)
        r.raise_for_status()
        soup = BeautifulSoup(r.content, "lxml")

        model_cell = soup.find(string=re.compile('^([^/]+/)?{}'.format(model_id))).find_parent('td')
        row = model_cell.find_parent('tr')
        table = row.find_parent('table')
        provider_cell = table.find(string=re.compile('^{}'.format(provider))).find_parent('td')
        header = provider_cell.find_parent('tr')
        model_version = model_cell
        # Determine the position in the header to get the corresponding cell from the model row
        for cell in header.find_all('td'):
            if cell == provider_cell:
                break
            model_version = model_version.find_next_sibling('td')
        else:
            raise ValueError('Failed to find provider position in table header')
        version = model_version.get_text().strip()
        return Release(version=version, notes='See %s for more information' % docs_url)

