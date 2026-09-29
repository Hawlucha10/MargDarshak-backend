"""SQLAlchemy database models for Stations, Timetables, Delay Records, and Bus Network."""

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
    ARRAY,
    TIMESTAMP,
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


class BusOperatorModel(Base):
    __tablename__ = "bus_operators"

    operator_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    short_code = Column(String(20), nullable=False, unique=True)
    operator_type = Column(String(20), nullable=False)
    state = Column(String(80), nullable=True)
    website = Column(String(255), nullable=True)
    rating = Column(Numeric(2, 1), default=3.5)
    has_live_tracking = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, nullable=True)


class BusTerminalModel(Base):
    __tablename__ = "bus_terminals"

    terminal_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(150), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(80), nullable=True)
    lat = Column(Numeric(10, 6), nullable=False)
    lon = Column(Numeric(10, 6), nullable=False)
    nearest_station_code = Column(String(30), ForeignKey("stations.code", ondelete="SET NULL"), nullable=True)
    transfer_walk_minutes = Column(SmallInteger, default=15)
    terminal_type = Column(String(30), default="ISBT")
    amenities = Column(ARRAY(String), nullable=True)
    geom = Column(Geometry(geometry_type="POINT", srid=4326), nullable=True)
    created_at = Column(TIMESTAMP, nullable=True)


class BusRouteModel(Base):
    __tablename__ = "bus_routes"

    route_id = Column(Integer, primary_key=True, autoincrement=True)
    operator_id = Column(Integer, ForeignKey("bus_operators.operator_id", ondelete="CASCADE"), nullable=False)
    route_code = Column(String(30), nullable=True)
    from_terminal_id = Column(Integer, ForeignKey("bus_terminals.terminal_id", ondelete="CASCADE"), nullable=False)
    to_terminal_id = Column(Integer, ForeignKey("bus_terminals.terminal_id", ondelete="CASCADE"), nullable=False)
    bus_type = Column(String(40), nullable=False)
    departure = Column(Time, nullable=False)
    arrival = Column(Time, nullable=False)
    duration_minutes = Column(SmallInteger, nullable=False)
    distance_km = Column(SmallInteger, nullable=False)
    fare = Column(Integer, nullable=False)
    frequency = Column(String(30), default="DAILY")
    is_ac = Column(Boolean, default=False)
    is_sleeper = Column(Boolean, default=False)
    has_charging = Column(Boolean, default=False)
    has_wifi = Column(Boolean, default=False)
    rating = Column(Numeric(2, 1), nullable=True)
    via_cities = Column(ARRAY(String), nullable=True)
    created_at = Column(TIMESTAMP, nullable=True)

    __table_args__ = (
        Index("idx_bus_routes_from_dep", "from_terminal_id", "departure"),
        Index("idx_bus_routes_to", "to_terminal_id"),
    )


class BusDelayRecordModel(Base):
    __tablename__ = "bus_delay_records"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    route_id = Column(Integer, ForeignKey("bus_routes.route_id", ondelete="SET NULL"), nullable=True)
    operator_type = Column(String(20), nullable=True)
    bus_type = Column(String(40), nullable=True)
    route_distance_km = Column(SmallInteger, nullable=True)
    month = Column(SmallInteger, nullable=True)
    day_of_week = Column(SmallInteger, nullable=True)
    departure_hour = Column(SmallInteger, nullable=True)
    is_highway = Column(Boolean, default=True)
    is_urban_stretch = Column(Boolean, default=False)
    is_monsoon = Column(Boolean, default=False)
    is_fog_risk = Column(Boolean, default=False)
    traffic_congestion_index = Column(Numeric(4, 2), default=1.0)
    delay_minutes = Column(Integer, default=0)
    is_delayed = Column(Boolean, default=False)
