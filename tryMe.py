from pydantic import BaseModel, model_validator
from typing_extensions import Self


class UserModel(BaseModel):
    username: str
    password1: str
    password2: str
    bs: str = "sd"

    @model_validator(mode="after")
    def check_passwords_match(self) -> Self:
        pw1 = self.password1
        pw2 = self.password2
        self.bs = "my name is moshe"
        if pw1 is not None and pw2 is not None and pw1 != pw2:
            raise ValueError("passwords do not match")
        return self


print(UserModel(username="scolvin", password1="zxcvbn", password2="zxcvbn"))
