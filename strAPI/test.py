from typing import Optional, Dict

from sqlmodel import JSON, Field, SQLModel, Column


class Hero(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    secret_name: Dict[int, float] = Field(default={}, sa_column=Column(JSON))
    age: Optional[int] = None

    class Config:
        arbitrary_types_allowed = True


Hero(name="Max", secret_name={"name": "bob"}, age=12)


