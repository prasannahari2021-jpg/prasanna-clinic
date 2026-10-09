from dataclasses import dataclass
from typing import Optional


@dataclass
class Appointment:
    id: Optional[int] = None
    token_number: Optional[str] = None
    owner_name: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[str] = None
    pet_name: Optional[str] = None
    pet_type: Optional[str] = None
    breed: Optional[str] = None
    age: Optional[str] = None
    gender: Optional[str] = None
    weight: Optional[str] = None
    service: Optional[str] = None
    appointment_date: Optional[str] = None
    appointment_time: Optional[str] = None
    symptoms: Optional[str] = None
    status: str = "Pending"
    created_at: Optional[str] = None
