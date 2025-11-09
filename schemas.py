from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime

class Appointment(BaseModel):
    full_name: str = Field(...)
    email: EmailStr = Field(...)
    phone: Optional[str] = Field(None)
    preferred_date: datetime = Field(...)
    notes: Optional[str] = Field(None)
    product_interest: Optional[str] = Field(None)
