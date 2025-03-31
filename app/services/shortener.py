import random
import string
from typing import Optional
from sqlalchemy.orm import Session
from app.crud import crud_link


class URLShortener:
    def __init__(self, db: Session):
        self.db = db

    def generate_short_code(self, length: int = 6) -> str:
        chars = string.ascii_letters + string.digits
        while True:
            code = ''.join(random.choices(chars, k=length))
            if not crud_link.get_link_by_short_code(self.db, code):
                return code

    def create_short_code_or_custom(self, custom_alias: Optional[str]) -> str:
        if custom_alias:
            if crud_link.get_link_by_custom_alias(self.db, custom_alias):
                raise ValueError("Alias already in use")
            return custom_alias
        return self.generate_short_code()
