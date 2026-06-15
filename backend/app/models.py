from pydantic import BaseModel, EmailStr


class ReservationCreate(BaseModel):
    seat_number: str
    customer_name: str
    customer_email: EmailStr
    movie_id: str


class ReservationUpdate(BaseModel):
    customer_name: str
    customer_email: EmailStr