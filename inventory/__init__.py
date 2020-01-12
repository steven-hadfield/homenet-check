from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

from vendor import registry

__all__ = ['Base', 'Device']

Base = declarative_base()

class Device(Base):
    __tablename__ = 'devices'

    id = Column(Integer, primary_key=True)
    model = Column(String, nullable=False)
    vendor_id = Column(String, nullable=False)
    version = Column(String)
    description = Column(String)

    def get_vendor(self):
        vendor = registry.get(self.vendor_id)
        if vendor is None:
            raise ValueError("Vendor not found")
        return vendor

