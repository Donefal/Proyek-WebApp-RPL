from pydantic import BaseModel

class UserBase(BaseModel):
    name: str
    email: str

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    name: str | None = None
    email: str | None = None

class User(UserBase):
    id: int

    class Config:
        orm_mode = True
