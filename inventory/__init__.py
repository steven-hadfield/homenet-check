import logging

from cmp_version import cmp_version
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

from vendor import registry

__all__ = ['Base', 'Device']

logger = logging.getLogger('inventory')

Base = declarative_base()

class Device(Base):
    __tablename__ = 'devices'
    id = Column(Integer, primary_key=True, comment='Generated device ID')
    model = Column(String(100), nullable=False, comment='Model ID used for lookup with vendor')
    vendor_id = Column(String(30), nullable=False, comment='Vendor ID corresponding with the vendor module for lookup within homenet')
    version = Column(String(80), comment='Device current known version')
    description = Column(String(255), comment='Meaningful description (like "Home router")')
    address = Column(String(255), comment='Network address for management console (e.g. IP or Web Address)')

    def get_vendor(self):
        vendor = registry.get(self.vendor_id)
        if vendor is None:
            raise ValueError("Vendor not found")
        return vendor

    def get_available_update(self):
        vendor = self.get_vendor()
        version = vendor.get_latest(self)
        logger.info('Latest version for %s %s is %s, current: %s', vendor.name(), self.model, version, self.version)
        if self.version is None or cmp_version(version, self.version) > 0:
            return version

    def has_update(self):
        newer = self.get_available_update()
        return newer is not None

