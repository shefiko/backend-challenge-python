import datetime

from pydantic import BaseModel, ConfigDict


class BookingBaseRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    guest_name: str
    unit_id: str
    check_in_date: datetime.date
    number_of_nights: int


class BookingBaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    guest_name: str
    unit_id: str
    check_in_date: datetime.date
    number_of_nights: int


class ExtendBooking(BaseModel):
    number_of_nights: int
