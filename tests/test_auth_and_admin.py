"""Tests for User Authentication, Role-Based Access Control, and Telemetry API."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_demo_login_customer(async_client: AsyncClient) -> None:
    """Test 1-click customer/planner demo login endpoint."""
    response = await async_client.post("/api/v1/auth/demo-login/customer")
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "planner@aerocool.ai"
    assert data["user"]["role"] == "customer"


@pytest.mark.asyncio
async def test_demo_login_admin(async_client: AsyncClient) -> None:
    """Test 1-click admin demo login endpoint."""
    response = await async_client.post("/api/v1/auth/demo-login/admin")
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "admin@aerocool.ai"
    assert data["user"]["role"] == "admin"


@pytest.mark.asyncio
async def test_user_registration_and_login_flow(async_client: AsyncClient) -> None:
    """Test user registration and subsequent login."""
    test_email = "test.officer@delhi.gov.in"
    reg_payload = {
        "email": test_email,
        "password": "Password123!",
        "full_name": "Delhi Heat Officer",
        "role": "customer",
        "organization": "Delhi Disaster Management Authority",
    }
    reg_resp = await async_client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_resp.status_code == 201
    reg_data = reg_resp.json()
    assert reg_data["user"]["email"] == test_email
    assert reg_data["user"]["full_name"] == "Delhi Heat Officer"

    # Login with newly created credentials
    login_payload = {
        "email": test_email,
        "password": "Password123!",
    }
    login_resp = await async_client.post("/api/v1/auth/login", json=login_payload)
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    assert "access_token" in login_data

    # Test /auth/me endpoint with bearer token
    token = login_data["access_token"]
    me_resp = await async_client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["email"] == test_email


@pytest.mark.asyncio
async def test_admin_rbac_protection(async_client: AsyncClient) -> None:
    """Ensure regular customer token is denied access to admin telemetry."""
    # 1. Login as customer
    cust_resp = await async_client.post("/api/v1/auth/demo-login/customer")
    cust_token = cust_resp.json()["access_token"]

    # 2. Attempt admin telemetry access -> Must return 403 Forbidden
    cust_admin_resp = await async_client.get(
        "/api/v1/admin/telemetry",
        headers={"Authorization": f"Bearer {cust_token}"},
    )
    assert cust_admin_resp.status_code == 403

    # 3. Login as admin
    admin_resp = await async_client.post("/api/v1/auth/demo-login/admin")
    admin_token = admin_resp.json()["access_token"]

    # 4. Access admin telemetry with admin token -> Must return 200 OK
    admin_telemetry_resp = await async_client.get(
        "/api/v1/admin/telemetry",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert admin_telemetry_resp.status_code == 200
    tel_data = admin_telemetry_resp.json()
    assert "total_requests" in tel_data
    assert "avg_latency_ms" in tel_data

    # 5. Access admin logs
    logs_resp = await async_client.get(
        "/api/v1/admin/telemetry/logs",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert logs_resp.status_code == 200
    logs_data = logs_resp.json()
    assert isinstance(logs_data, list)

    # 6. Access admin health
    health_resp = await async_client.get(
        "/api/v1/admin/health",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert health_resp.status_code == 200
    health_data = health_resp.json()
    assert health_data["status"] == "operational"
    assert "pinn_engine_device" in health_data
