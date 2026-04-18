from pydantic import BaseModel


class AuthUserResponse(BaseModel):
    username: str
    display_name: str
    role: str
