"""
Tests for request processing helpers.

These tests cover JSON parsing, error responses, and success responses.
"""

import json
from unittest.mock import AsyncMock

import pytest
from aiohttp import web

from cityhive.app.helpers.request import (
    create_error_response,
    create_success_response,
    parse_json_request,
)


@pytest.fixture
def valid_json_data():
    """Test data for valid JSON requests."""
    return {"name": "John", "email": "john@example.com"}


@pytest.fixture
def mock_request_with_valid_json(valid_json_data):
    """Mock request with valid JSON data."""
    mock_request = AsyncMock()
    mock_request.json.return_value = valid_json_data
    return mock_request


@pytest.fixture
def mock_request_with_json_decode_error():
    """Mock request that raises JSONDecodeError."""
    mock_request = AsyncMock()
    mock_request.json.side_effect = json.JSONDecodeError("Expecting value", "", 0)
    mock_request.method = "POST"
    mock_request.path = "/api/users"
    return mock_request


@pytest.fixture
def mock_request_with_unexpected_error():
    """Mock request that raises unexpected ValueError."""
    mock_request = AsyncMock()
    mock_request.json.side_effect = ValueError("Unexpected error")
    mock_request.method = "POST"
    mock_request.path = "/api/users"
    return mock_request


async def test_parse_json_request_with_valid_json_returns_data_and_no_error(
    mock_request_with_valid_json, valid_json_data
):
    data, error = await parse_json_request(mock_request_with_valid_json)

    assert data == valid_json_data
    assert error is None


async def test_parse_json_request_with_invalid_json_returns_error_message_and_no_data(
    mock_request_with_json_decode_error,
):
    data, error = await parse_json_request(mock_request_with_json_decode_error)

    assert data is None
    assert error == "Invalid JSON format"


async def test_parse_json_request_with_unexpected_error_returns_generic_error_message(
    mock_request_with_unexpected_error,
):
    data, error = await parse_json_request(mock_request_with_unexpected_error)

    assert data is None
    assert error == "Unable to parse request data"


def test_create_error_response_with_default_status_returns_400_json_response():
    response = create_error_response("Test error")

    assert isinstance(response, web.Response)
    assert response.status == 400
    assert response.content_type == "application/json"


def test_create_error_response_with_custom_status_returns_response_with_custom_status():
    response = create_error_response("Not found", 404)

    assert response.status == 404
    assert response.content_type == "application/json"


@pytest.fixture
def success_response_data():
    """Test data for success responses."""
    return {"user": {"id": 1, "name": "John"}}


def test_create_success_response_with_default_status_returns_200_json_response(
    success_response_data,
):
    response = create_success_response(success_response_data)

    assert isinstance(response, web.Response)
    assert response.status == 200
    assert response.content_type == "application/json"


def test_create_success_response_with_custom_status_returns_response_with_custom_status(
    success_response_data,
):
    response = create_success_response(success_response_data, 201)

    assert response.status == 201
    assert response.content_type == "application/json"
