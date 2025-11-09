import os
from io import BytesIO
from datetime import datetime
import secrets
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from bson import ObjectId
from database import create_document, get_documents, db
from schemas import Appointment

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AppointmentRequest(Appointment):
    pass

@app.get("/")
def read_root():
    return {"message": "Verone API"}

@app.get("/test")
def test_database():
    response = {
        "backend": "Running",
        "database": "Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "Available"
            response["database_url"] = "Set" if os.getenv("DATABASE_URL") else "Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "Connected & Working"
            except Exception as e:
                response["database"] = f"Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "Available but not initialized"
    except Exception as e:
        response["database"] = f"Error: {str(e)[:50]}"
    response["database_url"] = "Set" if os.getenv("DATABASE_URL") else "Not Set"
    response["database_name"] = "Set" if os.getenv("DATABASE_NAME") else "Not Set"
    return response

@app.post("/api/appointments")
def create_appointment(payload: AppointmentRequest):
    code = secrets.token_hex(4).upper()
    data = payload.model_dump()
    data.update({"code": code, "status": "scheduled"})
    appointment_id = create_document("appointment", data)
    return {"id": appointment_id, "code": code}

@app.get("/api/appointments/{code}/receipt")
def get_receipt_pdf(code: str):
    docs = get_documents("appointment", {"code": code})
    if not docs:
        return JSONResponse(status_code=404, content={"detail": "Appointment not found"})
    appt = docs[0]
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    p.setFillColorRGB(0.05, 0.09, 0.2)
    p.rect(0, height-120, width, 120, stroke=0, fill=1)
    p.setFillColorRGB(1,1,1)
    p.setFont("Helvetica-Bold", 28)
    p.drawString(40, height-80, "VERONE")
    p.setFont("Helvetica", 12)
    p.drawString(40, height-100, "Appointment Receipt")
    p.setFillColorRGB(0,0,0)
    y = height-160
    lines = [
        f"Code: {appt.get('code')}",
        f"Name: {appt.get('full_name')}",
        f"Email: {appt.get('email')}",
        f"Phone: {appt.get('phone','-')}",
        f"Preferred Date: {datetime.fromisoformat(str(appt.get('preferred_date'))).strftime('%Y-%m-%d %H:%M') if appt.get('preferred_date') else '-'}",
        f"Product Interest: {appt.get('product_interest','-')}",
        f"Notes: {appt.get('notes','-')}"
    ]
    p.setFont("Helvetica", 12)
    for line in lines:
        p.drawString(40, y, line)
        y -= 24
    p.line(40, y, width-40, y)
    y -= 24
    p.setFont("Helvetica-Oblique", 10)
    p.drawString(40, y, "Thank you for choosing Verone. Our concierge will contact you to confirm your appointment.")
    p.showPage()
    p.save()
    buffer.seek(0)
    headers = {"Content-Disposition": f"inline; filename=verone_receipt_{code}.pdf"}
    return StreamingResponse(buffer, media_type="application/pdf", headers=headers)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
