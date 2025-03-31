from app.database.BaseModel import Base
from app.database.DatabaseConnection import engine
from app.database.models.LinkModel import Link
from app.database.models.UserModel import User

def init_db():
    Base.metadata.create_all(bind=engine)