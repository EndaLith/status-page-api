from datetime import UTC, datetime, timedelta

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.incident_rules import INITIAL_STATUS, can_transition
from app.models import (
    HealthCheck,
    Incident,
    IncidentService,
    IncidentUpdate,
    MaintenanceWindow,
    Service,
    User,
)
from app.schemas import (
    HealthCheckCreate,
    HealthCheckRead,
    IncidentCreate,
    IncidentDetail,
    IncidentRead,
    IncidentStatusUpdate,
    MaintenanceCreate,
    MaintenanceRead,
    ServiceCreate,
    ServiceRead,
    Token,
    UptimeRead,
    UserCreate,
    UserRead,
)
from app.security import create_access_token, hash_password, verify_password

app = FastAPI(title="Status Page API")


@app.post("/auth/register", response_model=UserRead, status_code=201)
def register(data: UserCreate, db: Session = Depends(get_db)):
    user = User(
        username=data.username, password_hash=hash_password(data.password), role="user"
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Username already taken")
    db.refresh(user)
    return user


@app.get("/home")
def root():
    return {"status": "ok"}


@app.get("/services", response_model=list[ServiceRead])
def list_services(db: Session = Depends(get_db)):
    return db.query(Service).filter(Service.is_active == True).all()


@app.get("/services/{service_id}", response_model=ServiceRead)
def get_service(service_id: int, db: Session = Depends(get_db)):
    service = (
        db.query(Service)
        .filter(Service.id == service_id, Service.is_active == True)
        .first()
    )
    if service is None:
        raise HTTPException(status_code=404, detail="Service not found")
    return service


@app.post("/services", response_model=ServiceRead, status_code=201)
def create_service(
    data: ServiceCreate,
    db: Session = Depends(get_db),
    admin: User = (Depends(require_admin)),
):
    service = Service(name=data.name, description=data.description, url=data.url)
    db.add(service)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="A service with this name already exists"
        )
    db.refresh(service)
    return service


@app.put("/services/{service_id}", response_model=ServiceRead)
def update_service(
    service_id: int,
    data: ServiceCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    service = (
        db.query(Service)
        .filter(Service.id == service_id, Service.is_active == True)
        .first()
    )
    if service is None:
        raise HTTPException(status_code=404, detail="Service not found")
    else:
        service.name = data.name
        service.description = data.description
        service.url = data.url
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=409, detail="A service with this name already exists"
            )
        db.refresh(service)
        return service


@app.delete("/services/{service_id}", status_code=204)
def archive_service(
    service_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    service = (
        db.query(Service)
        .filter(Service.id == service_id, Service.is_active == True)
        .first()
    )
    if service is None:
        raise HTTPException(status_code=404, detail="Service not found")
    service.is_active = False
    db.commit()


@app.post("/auth/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form.username).first()
    if user is None or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_access_token(user.username)
    return {"access_token": token, "token_type": "bearer"}


@app.get("/auth/me", response_model=UserRead)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user


@app.post(
    "/services/{service_id}/health_checks",
    response_model=HealthCheckRead,
    status_code=201,
)
def create_health_check(
    service_id: int,
    data: HealthCheckCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    service = (
        db.query(Service)
        .filter(Service.id == service_id, Service.is_active == True)
        .first()
    )
    if service is None:
        raise HTTPException(status_code=404, detail="Service not found")
    check = HealthCheck(
        service_id=service_id,
        is_up=data.is_up,
        response_ms=data.response_ms,
        message=data.message,
    )
    db.add(check)
    db.commit()
    db.refresh(check)
    return check


@app.get("/services/{service_id}/health_checks", response_model=list[HealthCheckRead])
def list_health_checks(
    service_id: int,
    since: datetime | None = None,
    until: datetime | None = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    service = (
        db.query(Service)
        .filter(Service.id == service_id, Service.is_active == True)
        .first()
    )
    if service is None:
        raise HTTPException(status_code=404, detail="Service not found")
    query = db.query(HealthCheck).filter(HealthCheck.service_id == service.id)
    if since is not None:
        query = query.filter(HealthCheck.checked_at >= since)
    if until is not None:
        query = query.filter(HealthCheck.checked_at <= until)
    return (
        query.order_by(HealthCheck.checked_at.desc()).limit(limit).offset(offset).all()
    )


@app.post("/incidents", response_model=IncidentRead, status_code=201)
def create_incident(
    data: IncidentCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    unique_ids = set(data.service_ids)
    found = (
        db.query(Service)
        .filter(Service.id.in_(unique_ids), Service.is_active == True)
        .count()
    )
    if found != len(unique_ids):
        raise HTTPException(status_code=404, detail="Service not found")

    incident = Incident(title=data.title, status=INITIAL_STATUS)
    db.add(incident)
    db.flush()

    for service_id in unique_ids:
        db.add(IncidentService(incident_id=incident.id, service_id=service_id))
    db.add(
        IncidentUpdate(
            incident_id=incident.id,
            message=data.message,
            status=INITIAL_STATUS,
        )
    )
    db.commit()
    db.refresh(incident)
    return incident


@app.get("/incidents", response_model=list[IncidentRead])
def list_incidents(active: bool = False, db: Session = Depends(get_db)):
    query = db.query(Incident)
    if active:
        query = query.filter(Incident.resolved_at.is_(None))
    return query.order_by(Incident.started_at.desc()).all()


@app.get("/incidents/{incident_id}", response_model=IncidentDetail)
def get_incident(incident_id: int, db: Session = Depends(get_db)):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@app.patch("/incidents/{incident_id}/status", response_model=IncidentDetail)
def change_incident_status(
    incident_id: int,
    data: IncidentStatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    if not can_transition(incident.status, data.status):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot change status from {incident.status} to {data.status}",
        )
    incident.status = data.status
    if data.status == "resolved":
        incident.resolved_at = datetime.now(UTC)
    else:
        incident.resolved_at = None
    db.add(
        IncidentUpdate(
            incident_id=incident.id, message=data.message, status=data.status
        )
    )
    db.commit()
    db.refresh(incident)
    return incident


@app.get("/services/{service_id}/uptime", response_model=UptimeRead)
def get_uptime(
    service_id: int,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    service = (
        db.query(Service)
        .filter(Service.id == service_id, Service.is_active == True)
        .first()
    )
    if service is None:
        raise HTTPException(status_code=404, detail="Service not found")
    since = datetime.now(UTC) - (timedelta(days=days))
    total, up = (
        db.query(
            func.count(HealthCheck.id),
            func.count(HealthCheck.id).filter(HealthCheck.is_up.is_(True)),
        )
        .filter(HealthCheck.service_id == service_id, HealthCheck.checked_at >= since)
        .one()
    )
    percent = None if total == 0 else round(up / total * 100, 2)
    return UptimeRead(
        service_id=service_id,
        days=days,
        total_checks=total,
        up_checks=up,
        uptime_percent=percent,
    )


@app.post("/maintenance-windows", response_model=MaintenanceRead, status_code=201)
def create_maintenance(
    data: MaintenanceCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    service = (
        db.query(Service)
        .filter(Service.id == data.service_id, Service.is_active == True)
        .first()
    )
    if service is None:
        raise HTTPException(status_code=404, detail="Service not found")
    window = MaintenanceWindow(**data.model_dump())
    db.add(window)
    db.commit()
    db.refresh(window)
    return window


@app.get("/maintenance-windows", response_model=list[MaintenanceRead])
def list_maintenance(
    upcoming: bool = False,
    db: Session = Depends(get_db),
):
    query = db.query(MaintenanceWindow)
    if upcoming:
        query = query.filter(MaintenanceWindow.ended_at >= datetime.now(UTC))
    return query.order_by(MaintenanceWindow.started_at.asc()).all()
