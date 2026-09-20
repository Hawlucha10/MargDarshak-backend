"""SQLAlchemy database models for Stations, Timetables, and Delay Records."""

from sqlalchemy import (
    Column,
    String,
    Integer,
    SmallInteger,
    Time,
    Date,
    Numeric,
    Boolean,
    ForeignKey,
    BigInteger,
    Index,
)
from geoalchemy2 import Geometry
from app.db.postgres import Base


class StationModel(Base):
    __tablename__ = "stations"

    code = Column(String(30), primary_key=True, index=True)
    name = Column(String(150), nullable=False, index=True)
    state = Column(String(80), nullable=True)
    zone = Column(String(20), nullable=True, index=True)
    address = Column(String(255), nullable=True)
    lat = Column(Numeric(10, 6), nullable=False)
    lon = Column(Numeric(10, 6), nullable=False)
    geom = Column(Geometry(geometry_type="POINT", srid=4326), nullable=True)


class TimetableModel(Base):
    __tablename__ = "timetable"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    train_number = Column(String(20), nullable=False, index=True)
    train_name = Column(String(150), nullable=False)
    station_code = Column(String(30), ForeignKey("stations.code", ondelete="CASCADE"), nullable=False, index=True)
    station_name = Column(String(150), nullable=True)
    arrival = Column(Time, nullable=True)
    departure = Column(Time, nullable=True)
    day = Column(SmallInteger, default=1)
    stop_sequence = Column(SmallInteger, nullable=True)

    __table_args__ = (
        Index("idx_timetable_station_dep", "station_code", "departure"),
        Index("idx_timetable_train_seq", "train_number", "stop_sequence"),
    )


class DelayRecordModel(Base):
    __tablename__ = "delay_records"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    journey_id = Column(String(30), nullable=True, index=True)
    train_number = Column(String(10), nullable=False, index=True)
    train_type = Column(String(50), nullable=True)
    departure_date = Column(Date, nullable=True)
    month = Column(SmallInteger, nullable=True)
    day_of_week = Column(SmallInteger, nullable=True)
    zone = Column(String(20), nullable=True)
    distance_km = Column(Integer, nullable=True)
    is_fog_risk = Column(Boolean, default=False)
    is_monsoon_season = Column(Boolean, default=False)
    fog_risk_score = Column(Numeric(5, 3), nullable=True)
    zone_congestion_index = Column(Numeric(5, 3), nullable=True)
    delay_minutes = Column(Integer, default=0)
    is_delayed = Column(Boolean, default=False)
