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

    id = Column(Integer, primary_key=True)
    model = Column(String, nullable=False)
    vendor_id = Column(String, nullable=False)
    version = Column(String)
    description = Column(String)

    def get_vendor(self, config):
        vendor = registry.get(self.vendor_id)
        if vendor is None:
            raise ValueError("Vendor not found")
        return vendor(config)

    def get_available_update(self, config):
        vendor = self.get_vendor(config)
        version = vendor.get_latest(self)
        logger.info('Latest version for %s %s is %s, current: %s', vendor.name(), self.model, version, self.version)
        if self.version is None or cmp_version(version, self.version) > 0:
            return version

    def has_update(self, config):
        newer = self.get_available_update(config)
        return newer is not None

