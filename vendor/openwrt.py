import csv
from email.utils import formatdate
import gzip
import logging
import os.path
import re
import time

from bs4 import BeautifulSoup
import requests

from utils.http import get_response_expiry
from . import Release, Vendor, registry

logger = logging.getLogger('vendor.openwrt')

@registry.register
class OpenWRT(Vendor):
    _cache = None
    _cache_tag = None
    def __init__(self, config):
        self._cache = os.path.join(config.cache_dir, 'openwrt-db.csv.gz')
        self._cache_tag = os.path.join(config.cache_dir, 'openwrt-db.etag')
        self._cache_expiry = os.path.join(config.cache_dir, 'openwrt-db.expires')

    def id():
        return 'openwrt'

    def name(self):
        return 'OpenWRT'

    def get_latest(self, device):
        """Check the OpenWRT database for the taget version of the specified device"""
        cache = self._get_cache()
        if cache is None:
            raise ValueError("Failed to retrieve OpenWRT database")

        with gzip.open(self._cache, 'rt', errors='surrogateescape') as csv_file:
            reader = csv.DictReader(csv_file, delimiter='\t')
            for row in reader:
                if device.model == self._format_model(row):
                    version = row['supportedcurrentrel']
                    docs_url = 'https://openwrt.org/releases/{}/notes-{}'.format('.'.join(version.split('.')[:2]), version)
                    download_link = row['firmwareopenwrtupgradeurl']

                    # Load additional release metadata from file index page
                    basepath_index = download_link.rindex('/') + 1
                    index = download_link[:basepath_index]
                    filename = download_link[basepath_index:]
                    hashsum = None
                    hashtype = None
                    file_size = None
                    build_date = None
                    try:
                        r = requests.get(index)
                        r.raise_for_status()
                        soup = BeautifulSoup(r.content, "lxml")

                        files = soup.table
                        header = files.tr
                        # Expected header: model, hash, file size, build date
                        hashtype = header.find('th').find_next_sibling('th').string
                        cell = files.find('a', href=filename).find_parent('td')
                        hashsum_cell = cell.find_next_sibling('td')
                        hashsum = hashsum_cell.string
                        size_cell = hashsum_cell.find_next_sibling('td')
                        file_size = size_cell.string
                        date_cell = size_cell.find_next_sibling('td')
                        build_date = date_cell.string

                    except requests.exceptions.HTTPError as e:
                        logger.warning('Failed to download target release metadata', e)

                    return Release(version=version, download_url=download_link, docs_url=docs_url, hash_type = hashtype, hash_sum=hashsum, file_size=file_size, release_date=build_date)
        loggger.warning("Failed to find any released versions for %s", device.model)
        return None


    def supported_devices(self):
        """Check OpenWRT database for supported devices"""

        cache = self._get_cache()
        if cache is None:
            return None

        devices = []
        with gzip.open(self._cache, 'rt', errors='surrogateescape') as csv_file:
            reader = csv.DictReader(csv_file, delimiter='\t')
            for row in reader:
                # Filter unsupported models in spreadsheet; there may be other values to filter
                if row['supportedcurrentrel'] != '' and row['supportedcurrentrel'] != '-':
                    devices.append(self._format_model(row))
        return devices

    def _format_model(self, row):
        model = '{} {}'.format(row['brand'], row['model'])
        if row['version'] != 'NULL':
            model += ' {}'.format(row['version'])
        return model

    def _get_cache(self):
        last_modified = None
        tag = None
        if os.path.exists(self._cache):
            if os.path.exists(self._cache_expiry):
                with open(self._cache_expiry, 'r') as expiry_file:
                    expiry = expiry_file.read(100)
                if float(expiry) > time.time():
                    logger.debug('Skipping web request due to valid cache')
                    return self._cache

            last_modified = os.path.getmtime(self._cache)

        if os.path.exists(self._cache_tag):
            with open(self._cache_tag, 'r') as etag_file:
                tag = etag_file.read(100)
        try:
            self._download_db(last_modified, tag)
        except requests.exceptions.HTTPError as e:
            logger.warning('Failed to download latest devices list', e)

        if not os.path.exists(self._cache):
            return None
        return self._cache

    def _download_db(self, last_modified=None, tag=None):
        """Download the latest database file if newer than cached file"""
        headers = {}
        # Use multiple headers/local files to try to use cache as much as sensible
        if last_modified:
            headers['If-Modified-Since'] = formatdate(timeval = last_modified, localtime = False, usegmt = True)
        if tag:
            headers['If-None-Match'] = tag
        logger.debug('Checking for latest OpenWRT database with headers: %s', headers)
        r = requests.get('https://openwrt.org/_media/toh_dump_tab_separated_csv.csv.gz', stream=True, headers=headers)
        logger.debug('Response status: %d, Headers: %s', r.status_code, r.headers)
        r.raise_for_status()
        if r.ok:
            with open(self._cache, 'wb') as fd:
                for chunk in r.iter_content(chunk_size=128):
                    fd.write(chunk)
            if 'ETag' in r.headers:
                with open(self._cache_tag, 'w') as etag_file:
                    etag_file.write(r.headers['ETag'])
            expiry = get_response_expiry(r.headers)
            if expiry:
                with open(self._cache_expiry, 'w') as expiry_file:
                    expiry_file.write(str(expiry))

