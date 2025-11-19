from __future__ import annotations

from unittest.mock import patch

import pytest
from aiohttp import ClientError
from homeassistant import config_entries
from homeassistant.const import CONF_HOST
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.candy_bianca.const import (
    CONF_FINISH_NOTIFICATION,
    CONF_SATELLITE_ENTITY,
    CONF_SCAN_INTERVAL,
    DOMAIN,
)


class MockResponse:
    def __init__(self, json_data: dict | None = None, status: int = 200) -> None:
        self._json = json_data or {}
        self.status = status

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def json(self, content_type=None):
        return self._json


class MockSession:
    def __init__(self, response: MockResponse) -> None:
        self._response = response

    def get(self, url, timeout):
        return self._response


@pytest.mark.asyncio
async def test_user_flow_creates_entry(hass):
    session = MockSession(MockResponse({"statusLavatrice": {}}))

    with patch(
        "custom_components.candy_bianca.config_flow.async_get_clientsession",
        return_value=session,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        assert result["type"] == FlowResultType.FORM

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.2.3.4",
                CONF_SCAN_INTERVAL: 45,
                CONF_FINISH_NOTIFICATION: True,
                CONF_SATELLITE_ENTITY: "",
            },
        )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Candy Bianca (1.2.3.4)"
    assert result["data"] == {CONF_HOST: "1.2.3.4"}
    assert result["options"] == {
        CONF_SCAN_INTERVAL: 45,
        CONF_FINISH_NOTIFICATION: True,
    }


@pytest.mark.asyncio
async def test_user_flow_cannot_connect(hass):
    session = MockSession(MockResponse({}, status=500))

    with patch(
        "custom_components.candy_bianca.config_flow.async_get_clientsession",
        return_value=session,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.2.3.4",
                CONF_SCAN_INTERVAL: 30,
                CONF_FINISH_NOTIFICATION: False,
                CONF_SATELLITE_ENTITY: "",
            },
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


@pytest.mark.asyncio
async def test_user_flow_connection_error(hass):
    class ErrorSession(MockSession):
        def get(self, url, timeout):
            raise ClientError

    with patch(
        "custom_components.candy_bianca.config_flow.async_get_clientsession",
        return_value=ErrorSession(MockResponse()),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.2.3.4",
                CONF_SCAN_INTERVAL: 30,
                CONF_FINISH_NOTIFICATION: False,
                CONF_SATELLITE_ENTITY: "",
            },
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


@pytest.mark.asyncio
async def test_reconfigure_updates_existing_entry(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "1.2.3.4"},
        options={
            CONF_SCAN_INTERVAL: 30,
            CONF_FINISH_NOTIFICATION: False,
        },
        unique_id="1.2.3.4",
    )
    entry.add_to_hass(hass)

    session = MockSession(MockResponse({"statusLavatrice": {}}))

    with patch(
        "custom_components.candy_bianca.config_flow.async_get_clientsession",
        return_value=session,
    ), patch("custom_components.candy_bianca.async_setup_entry", return_value=True), patch(
        "custom_components.candy_bianca.async_unload_entry", return_value=True
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={
                "source": config_entries.SOURCE_RECONFIGURE,
                "entry_id": entry.entry_id,
            },
        )

        assert result["type"] == FlowResultType.FORM

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.2.3.4",
                CONF_SCAN_INTERVAL: 60,
                CONF_FINISH_NOTIFICATION: True,
                CONF_SATELLITE_ENTITY: "select.satellite", 
            },
        )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"

    await hass.async_block_till_done()

    assert entry.data[CONF_HOST] == "1.2.3.4"
    assert entry.options == {
        CONF_SCAN_INTERVAL: 60,
        CONF_FINISH_NOTIFICATION: True,
        CONF_SATELLITE_ENTITY: "select.satellite",
    }


@pytest.mark.asyncio
async def test_options_flow_strips_and_clears_satellite(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "1.2.3.4"},
        options={
            CONF_SCAN_INTERVAL: 90,
            CONF_FINISH_NOTIFICATION: False,
            CONF_SATELLITE_ENTITY: "select.old",
        },
        unique_id="1.2.3.4",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] == FlowResultType.FORM

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_SCAN_INTERVAL: 120,
            CONF_FINISH_NOTIFICATION: True,
            CONF_SATELLITE_ENTITY: "   ",
        },
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_SCAN_INTERVAL: 120,
        CONF_FINISH_NOTIFICATION: True,
    }
