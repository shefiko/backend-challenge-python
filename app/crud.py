from typing import Tuple

from sqlalchemy.orm import Session

from . import models, schemas


class UnableToBook(Exception):
    pass


def create_booking(db: Session, booking: schemas.BookingBase) -> models.Booking:
    (is_possible, reason) = is_booking_possible(db=db, booking=booking)
    if not is_possible:
        raise UnableToBook(reason)
    db_booking = models.Booking(
        guest_name=booking.guest_name, unit_id=booking.unit_id,
        check_in_date=booking.check_in_date, number_of_nights=booking.number_of_nights)
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    return db_booking


def is_booking_possible(db: Session, booking: schemas.BookingBase) -> Tuple[bool, str]:
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
    is_unit_available_on_check_in_date = db.query(models.Booking) \
        .filter_by(check_in_date=booking.check_in_date, unit_id=booking.unit_id).first()

    if is_unit_available_on_check_in_date:
        return False, 'For the given check-in date, the unit is already occupied'

    return True, 'OK'
