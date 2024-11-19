from fastapi.testclient import TestClient
import pytest
import os

from flowex import flow


def test_simple_alert():
    print("aaa")
    os.remove("flow.db")
    client = TestClient(app, lifespan=flow.lifespan)
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
