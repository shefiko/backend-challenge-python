import datetime
from http import HTTPStatus

from fastapi import FastAPI, Depends
from fastapi.exceptions import HTTPException
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .crud import UnableToBook, BookingNotFound, UnableToExtend
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def hello_world():
    return {"message": "OK"}


@app.post("/api/v1/booking", response_model=schemas.BookingBaseResponse)
def create_booking(booking: schemas.BookingBaseRequest, db: Session = Depends(get_db)):
    try:
        return crud.create_booking(db=db, booking=booking)
    except UnableToBook as unable_to_book:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST,
                            detail=str(unable_to_book))


@app.post("/api/v1/booking/{id}/extend", response_model=schemas.BookingBaseResponse)
def extend_booking(id: int, extend: schemas.ExtendBooking, db: Session = Depends(get_db)):
    booking = db.query(models.Booking).filter_by(id=id).first()
    if booking is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(BookingNotFound))

    try:
        return crud.extend_booking(db, booking, extend.number_of_nights)
    except UnableToExtend as unable_to_extend:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(unable_to_extend))
