"""Tests for the sensor and binary sensor entities."""

from homeassistant.const import PERCENTAGE, STATE_OFF, STATE_ON, UnitOfTemperature
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.components.binary_sensor import BinarySensorDeviceClass

from custom_components.dukasmartfan.sensor import SCAN_INTERVAL


async def test_humidity_and_temperature(hass, setup_entry):
    humidity = hass.states.get("sensor.bathroom_humidity")
    assert humidity.state == "45"
    assert humidity.attributes["unit_of_measurement"] == PERCENTAGE
    assert humidity.attributes["device_class"] == SensorDeviceClass.HUMIDITY

    temperature = hass.states.get("sensor.bathroom_temperature")
    assert temperature.state == "21"
    assert temperature.attributes["unit_of_measurement"] == UnitOfTemperature.CELSIUS
    assert temperature.attributes["device_class"] == SensorDeviceClass.TEMPERATURE


async def test_sensors_update_on_push(hass, device, setup_entry, onchange):
    device.humidity, device.temperature = 60, 19
    onchange()
    await hass.async_block_till_done()
    assert hass.states.get("sensor.bathroom_humidity").state == "60"
    assert hass.states.get("sensor.bathroom_temperature").state == "19"


async def test_fan_speed_polled(hass, device, setup_entry):
    from datetime import timedelta

    from homeassistant.util import dt as dt_util
    from pytest_homeassistant_custom_component.common import async_fire_time_changed

    assert hass.states.get("sensor.bathroom_fan_speed").state == "0"
    device.fan_speed = 1200
    async_fire_time_changed(hass, dt_util.utcnow() + SCAN_INTERVAL + timedelta(seconds=1))
    await hass.async_block_till_done()
    assert hass.states.get("sensor.bathroom_fan_speed").state == "1200"


async def test_motor_running_follows_is_active(hass, device, setup_entry, onchange):
    state = hass.states.get("binary_sensor.bathroom_motor_running")
    assert state.state == STATE_OFF
    assert state.attributes["device_class"] == BinarySensorDeviceClass.RUNNING

    device.is_active = True
    onchange()
    await hass.async_block_till_done()
    assert hass.states.get("binary_sensor.bathroom_motor_running").state == STATE_ON
