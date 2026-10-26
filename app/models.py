from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    text,
)
from sqlalchemy.sql import func

from app.database import Base


class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=False)
    url = Column(String, nullable=False)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    is_active = Column(Boolean, nullable=False, server_default=text("True"))


class HealthCheck(Base):
    __tablename__ = "health_checks"
    id = Column(Integer, primary_key=True)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    checked_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    is_up = Column(Boolean, nullable=False)
    response_ms = Column(Integer, nullable=True)
    message = Column(String, nullable=True)
    __table_args__ = (
        Index("ix_health_checks_service_checked", "service_id", "checked_at"),
    )


class Incident(Base):
    __tablename__ = "incidents"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    status = Column(String, nullable=False)
    started_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    resolved_at = Column(DateTime(timezone=True), nullable=True)


class IncidentUpdate(Base):
    __tablename__ = "incident_updates"
    id = Column(Integer, primary_key=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    message = Column(String, nullable=False)
    status = Column(String, nullable=False)


class IncidentService(Base):
    __tablename__ = "incident_services"
    incident_id = Column(Integer, ForeignKey("incidents.id"), primary_key=True)
    service_id = Column(Integer, ForeignKey("services.id"), primary_key=True)


class MaintenanceWindow(Base):
    __tablename__ = "maintenance_windows"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        CheckConstraint("ended_at>started_at", name="ck_maintenance_window_order"),
    )


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "role IN ('admin','user')",
            name="ck_users_role",
        ),
    )
