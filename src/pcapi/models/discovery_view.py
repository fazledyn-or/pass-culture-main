from sqlalchemy import BigInteger, Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from pcapi.models.db import Model


class DiscoveryView(Model):
    __tablename__ = 'discovery_view'

    venueId = Column(BigInteger, ForeignKey('venue.id'))

    mediationId = Column(BigInteger, ForeignKey('mediation.id'))

    id = Column(BigInteger, ForeignKey('offer.id'), primary_key=True, index=True)

    type = Column(String(50))

    url = Column(String(255))

    offerDiscoveryOrder = Column(Integer)

    name = Column(String(140))

    isNational = Column(Boolean)

    offer = relationship('Offer',
                         foreign_keys=[id])
