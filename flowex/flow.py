#!/usr/bin/env python3

from typing import Dict, List

from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from pydantic import BaseModel

from flowex.model import AlertReasonModel, EventModel, ServerTypeModel, init
from flowex.alerts import ALERT_VALUES


# Define the schema for the input JSON
class ServerTypeRequest(BaseModel):
    name: str
    type: str


class Event(BaseModel):
    date: int
    source: str
    destination: str
    values: Dict[str, str]


server_type = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Server is starting up...")
    init()
    # Perform startup tasks
    yield
    print("Server is shutting down...")
    # Perform cleanup tasks


app = FastAPI(lifespan=lifespan)


@app.post("/v1/set_server_type")
async def set_server_type(request: ServerTypeRequest):
    # TODO use enum
    if request.type not in ["external", "internal"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid server type. Must be 'external' or 'internal'.",
        )

    ServerTypeModel.insert(**request.model_dump()).on_conflict_replace().execute()
    # we're async, so no concurrency problem
    server_type[request.name] = request.type
    return {"message": "Server type set successfully", "data": request}


@app.post("/v1/event")
async def handle_event(events: List[Event]):
    num_alerts = 0
    for e in events:
        EventModel.insert(**e.model_dump()).on_conflict_replace().execute()
        reasons = ALERT_VALUES.intersection(e.values.values())
        if reasons:
            severity = "low"
            for host in (e.source, e.destination):
                type = server_type.get(host, "internal")
                severity = "low" if type == "internal" else "high"
                need_alert = False
                for reason in reasons:
                    affected_rows = (
                        AlertReasonModel.insert(host=host, reason=reason)
                        .on_conflict_ignore()
                        .as_rowcount()
                        .execute()
                    )
                    need_alert |= affected_rows > 0
                if need_alert:
                    num_alerts += 1
                    print(
                        f"we had {severity} on host {host} alert due to {e.model_dump_json()}"
                    )
    return {
        "message": "events handled successfully",
        "event_num": len(events),
        "alerts_num": num_alerts,
    }


from fastapi.testclient import TestClient
import pytest
import os


def test_simple_alert():
    print("aaa")
    os.remove("flow.db")
    init()
    client = TestClient(app)
    alerts = client.post(
        "/v1/event",
        json=[
            {
                "date": "1610293274000",
                "source": "users",
                "destination": "payment",
                "values": {"cc": "CREDIT_CARD_NUMBER"},
            }
        ],
    ).json()["alerts_num"]
    assert alerts == 2
    alerts = client.post(
        "/v1/event",
        json=[
            {
                "date": "1610293274001",
                "source": "users2",
                "destination": "payment",
                "values": {"cc": "CREDIT_CARD_NUMBER"},
            }
        ],
    ).json()["alerts_num"]
    assert alerts == 1
    os.remove("flow.db")
