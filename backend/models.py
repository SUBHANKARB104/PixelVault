from sqlalchemy import Column, Integer, String, BigInteger, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"

    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String, nullable=False)
    email      = Column(String, unique=True, index=True, nullable=False)
    password   = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    images = relationship("Image", back_populates="owner", cascade="all, delete")


class Image(Base):
    __tablename__ = "images"

    id         = Column(Integer, primary_key=True, index=True)
    filename   = Column(String, nullable=False)
    url        = Column(String, nullable=False)
    size_bytes = Column(BigInteger, default=0)
    mime_type  = Column(String, default="image/jpeg")
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)

    owner = relationship("User", back_populates="images")