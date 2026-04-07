from flask_login import UserMixin

from app import models as m


class AdminUser(UserMixin):
    def __init__(self, doc: dict):
        self.id = str(doc["_id"])
        self.username = doc["username"]


def load_user(user_id: str) -> AdminUser | None:
    doc = m.admin_get_by_id(user_id)
    if not doc:
        return None
    return AdminUser(doc)
