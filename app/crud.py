import datetime
import calendar
from sqlite3 import Date
from typing import Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from . import models, schemas


class UnableToBook(Exception):
    pass


class UnableToExtend(Exception):
    pass


class BookingNotFound(Exception):
    pass


def create_booking(db: Session, booking: schemas.BookingBaseRequest) -> models.Booking:
    (is_possible, reason) = is_booking_possible(db=db, booking=booking)
    if not is_possible:
        raise UnableToBook(reason)

    db_booking = models.Booking(
        guest_name=booking.guest_name,
        unit_id=booking.unit_id,
        check_in_date=booking.check_in_date,
        number_of_nights=booking.number_of_nights
    )
    db.add(db_booking)

    availabilities = [
        models.UnitAvailability(
            unit_id=booking.unit_id,
            date=booking.check_in_date + datetime.timedelta(days=i)
        ) for i in range(booking.number_of_nights)
    ]

    db.add_all(availabilities)
    db.commit()
    db.refresh(db_booking)
    return db_booking


def extend_booking(db: Session, booking: models.Booking, number_of_nights: int) -> models.Booking:
    start_date = booking.check_in_date + datetime.timedelta(booking.number_of_nights)
    end_date = start_date + datetime.timedelta(number_of_nights)

    if not is_unit_available(db, booking.unit_id, start_date, end_date):
        raise UnableToExtend('For the given extend dates, the unit is already occupied')

    booking.number_of_nights += number_of_nights

    availabilities = [
        models.UnitAvailability(
            unit_id=booking.unit_id,
            date=end_date + datetime.timedelta(days=i)
        ) for i in range(number_of_nights)
    ]

    db.add_all(availabilities)
    db.commit()
    db.refresh(booking)
    return booking


def is_booking_possible(db: Session, booking: schemas.BookingBaseRequest) -> Tuple[bool, str]:
    # check 1 : The Same guest cannot book the same unit multiple times
    is_same_guest_booking_same_unit = db.query(models.Booking) \
        .filter_by(guest_name=booking.guest_name, unit_id=booking.unit_id).first()

    if is_same_guest_booking_same_unit:
        return False, 'The given guest name cannot book the same unit multiple times'

    # check 2 : the same guest cannot be in multiple units at the same time
    is_same_guest_already_booked = db.query(models.Booking) \
        .filter_by(guest_name=booking.guest_name).first()
    if is_same_guest_already_booked:
        return False, 'The same guest cannot be in multiple units at the same time'

    # check 3 : Unit is available for the check-in date
    start_date = booking.check_in_date
    end_date = booking.check_in_date + datetime.timedelta(booking.number_of_nights)
    if not is_unit_available(db, booking.unit_id, start_date, end_date):
        return False, 'For the given check-in date, the unit is already occupied'

    return True, 'OK'


def is_unit_available(db: Session, unit_id: str, start_date: Date, end_date: Date) -> bool:
    return db.query(func.count()).select_from(models.UnitAvailability).filter(
        models.UnitAvailability.unit_id == unit_id,
        models.UnitAvailability.date >= start_date,
        models.UnitAvailability.date <= end_date,
    ).scalar() == 0
