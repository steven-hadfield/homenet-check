"""
"""

import abc
from os.path import dirname
import pkgutil
import sys

__all__ = ['registry', 'Vendor', 'VendorRegistry']

class Vendor(metaclass=abc.ABCMeta):

    def __init__(self, config):
        pass

    @staticmethod
    @abc.abstractproperty
    def id():
        """Vendor IDentifier used to when stored in database"""

    @abc.abstractproperty
    def name(self):
        """Display name for the vendor"""

    @abc.abstractmethod
    def get_latest(self, device):
        """Get the latest available version for the given device"""

    def supported_devices():
        """Return a list of enumerated devices, if suppported. If enumeration is not supported, should return None"""
        return None

    def retrieve_device_version(self, device):
        """Use the device information to retrieve the current version. If not supported, should return None"""
        return None


class VendorRegistry(object):
    config = None
    def __init__(self):
        self.vendor_classes = {}
        self.vendor = None

    def init_config(self, config):
        self.vendors = {}
        for vendor_id, klass in self.vendor_classes.items():
            self.vendors[vendor_id] = klass(config)

    def register(self, klass):
        self.vendor_classes[klass.id()] = klass
        if self.config:
            self.vendors[klass.id()] = klass(self.config)
        return klass

    def unregister(self, name):
        if name in self.vendors:
            del self.vendors[name]

    def get(self, name):
        return self.vendors[name] if name in self.vendors else None

    def keys(self):
        return self.vendor_classes.keys()

    def values(self):
        return self.vendors.values()

    def items(self):
        return self.vendors.items()

    def load_vendors(self):
        """ Load all available vendors"""

        # Load local modules
        basepath = dirname(__file__)
        for importer, package_name, _ in pkgutil.iter_modules([basepath]):
            full_package_name = '%s.%s' % ('vendor', package_name)
            if full_package_name not in sys.modules:
                __import__(full_package_name)

        # TODO: Test external loading of vendors
        try:
            from pkg_resources import iter_entry_points
        except ImportError:
            return
        for ep in iter_entry_points(group="homenet-check.vendor"):
            f = ep.load()
            f()


registry = VendorRegistry()
