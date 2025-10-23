# server.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from supabase import create_client, Client
from datetime import datetime
import os

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://fghshuosamdxtdgqmvzc.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZnaHNodW9zYW1keHRkZ3FtdnpjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjExMzQwNzksImV4cCI6MjA3NjcxMDA3OX0.hactpM5pt6Tb3vf0hqCkMoTRG4BoYBFYpnGZaR3niuM")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


app = FastAPI(
    title="Ticket Management DB Tool",
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)


class CancelRequest(BaseModel):
    ticket_id: int
    user_id: int | None = None

class CancelResponse(BaseModel):
    status: str
    source: str = "custom_db"
    data: dict
    message: str

class ConfirmationRequest(BaseModel):
    ticket_id: int
    user_id: int

class FlightDetails(BaseModel):
    flight_id: int
    flight_name: str
    source: str
    destination: str
    takeoff_time: str
    company: str

class ConfirmationResponse(BaseModel):
    status: str
    source: str = "custom_db"
    data: FlightDetails
    message: str


@app.post("/mcp/db/cancel_ticket", response_model=CancelResponse)
def cancel_ticket(req: CancelRequest):
    ticket_res = supabase.table("tickets").select("*").eq("ticket_id", req.ticket_id).execute()
    
    if not ticket_res.data:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    ticket = ticket_res.data[0]

    if ticket.get("status") == "cancelled":
        return CancelResponse(
            status="success",
            data={"ticket_id": req.ticket_id, "status": "cancelled"},
            message="Ticket was already cancelled"
        )
    
    update_res = supabase.table("tickets").update({
        "status": "cancelled",
    }).eq("ticket_id", req.ticket_id).execute()

    return CancelResponse(
        status="success",
        data={"ticket_id": req.ticket_id, "status": "cancelled"},
        message="Ticket cancelled successfully"
    )

@app.post("/mcp/db/confirm_flight", response_model=ConfirmationResponse)
def confirm_flight(req: ConfirmationRequest):
    ticket_res = supabase.table("tickets") \
        .select("*") \
        .eq("ticket_id", req.ticket_id) \
        .eq("user_id", req.user_id) \
        .execute()
    
    if not ticket_res.data:
        raise HTTPException(status_code=404, detail="Ticket not found for this user")

    ticket = ticket_res.data[0]

    flight_id = ticket.get("flight_id")
    if not flight_id:
        raise HTTPException(status_code=404, detail="Flight ID not found for this ticket")
    flight_res = supabase.table("flights").select("*").eq("flight_id", flight_id).execute()
    if not flight_res.data:
        raise HTTPException(status_code=404, detail="Flight not found")
    flight = flight_res.data[0]

    flight_details = FlightDetails(
        flight_id=flight["flight_id"],
        flight_name=flight["flight_name"],
        source=flight["source"],
        destination=flight["destination"],
        takeoff_time=flight["takeoff_time"],
        company=flight["company"]
    )

    return ConfirmationResponse(
        status="success",
        data=flight_details,
        message="Ticket is already cancelled, here is flight details retrieved"
    )
