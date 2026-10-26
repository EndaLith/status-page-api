from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Service
from app.schemas import ServiceCreate, ServiceRead

app = FastAPI(title="Status Page API")


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
def create_service(data: ServiceCreate, db: Session = Depends(get_db)):
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
def update_service(service_id: int, data: ServiceCreate, db: Session = Depends(get_db)):
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
def archive_service(service_id: int, db: Session = Depends(get_db)):
    service = (
        db.query(Service)
        .filter(Service.id == service_id, Service.is_active == True)
        .first()
    )
    if service is None:
        raise HTTPException(status_code=404, detail="Service not found")
    service.is_active = False
    db.commit()
