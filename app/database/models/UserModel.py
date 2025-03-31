from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database.BaseModel import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    token = Column(String, unique=True, nullable=False)

    # Обратное отношение к ссылкам
    links = relationship("Link", back_populates="user")