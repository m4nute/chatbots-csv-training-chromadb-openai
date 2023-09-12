from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base
from .utils import generate_random_string


class Client(Base):
    __tablename__ = "clients"
     
    clientId = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, index=True)
    max_bots_allowed = Column(Integer, index=True, default=2)
    token = Column(String, nullable=False, unique=True, default=lambda: generate_random_string(32))

    chatbots = relationship("Chatbot", back_populates="client")

class Chatbot(Base):
    __tablename__ = "chatbots"

    name = Column(String, index=True)
    token = Column(String, primary_key=True, index=True, default=lambda: generate_random_string(32))
    clientId = Column(Integer, ForeignKey("clients.clientId"))

    client = relationship("Client", back_populates="chatbots")