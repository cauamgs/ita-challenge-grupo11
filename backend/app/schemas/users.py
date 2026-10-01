import uuid

from pydantic import BaseModel, ConfigDict

from app.models import UserRole


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    role: UserRole
