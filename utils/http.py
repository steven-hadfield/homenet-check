from email.utils import parsedate
import re
import time


def get_response_expiry(headers):
    """Determines the exipiration epoch time for an HTTP response"""
    expiry = None
    """Use Cache-Control: max-age or Expires to locally track of when the file expires"""
    if 'Cache-Control' in headers and 'max-age=' in headers['Cache-Control']:
        age = int(re.search('max-age=(\d*)', headers['Cache-Control']).group(1))
        if age > 0:
            header_date = parsedate(headers['Date']) if 'Date' in headers else None
            response_time = time.mktime(header_date) if header_date else time.time()
            expiry = response_time + age
    if not expiry and 'Expires' in headers:
        parsed_expires = parsedate(headers['Expires'])
        if parsed_expires:
            expiry = time.mktime(parsed_expires)
    return expiry
