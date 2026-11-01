"""
Unit tests for the Pydantic models.
"""

import pytest
from pydantic import ValidationError

from backend.models import (
    DecodeRequest,
    SolarPanelResponse,
    DataType1Response,
    DataType2Response,
    DataType3Response,
    DataType4Response,
    LightSensorResponse,
    DecodeResponse,
    ErrorResponse,
    HealthResponse,
)


class TestDecodeRequest:
    """Tests for DecodeRequest model."""

    def test_valid_request(self):
        """Test valid decode request keeps the packet unchanged."""
        packet = "EcAMSat.org   1DEA21020033021EBA02A80200004400F90830A23661515F5B"
        assert DecodeRequest(packet=packet).packet == packet

    def test_empty_packet_rejected(self):
        """Test that empty packet is rejected."""
        with pytest.raises(ValidationError, match="at least 1 character"):
            DecodeRequest(packet="")

    def test_max_length_packet_accepted(self):
        """A 200-character packet is the longest the model accepts."""
        assert len(DecodeRequest(packet="x" * 200).packet) == 200

    def test_too_long_packet_rejected(self):
        """Test that overly long packet is rejected."""
        with pytest.raises(ValidationError, match="at most 200 characters"):
            DecodeRequest(packet="x" * 201)

    def test_missing_packet_rejected(self):
        """The packet field is required."""
        with pytest.raises(ValidationError, match="packet"):
            DecodeRequest()


class TestDataTypeResponses:
    """Tests for the default type_name on each data type response model."""

    def test_datatype1_response(self):
        """Test DataType1Response model."""
        response = DataType1Response(
            power_port_status="0b1111",
            payload_board_temp_c=25.0,
            battery_voltage_v=8.0,
            payload_heater_current_ma=100.0
        )
        assert response.type_name == "Power and Temperature"

    def test_datatype2_response(self):
        """Test DataType2Response model."""
        response = DataType2Response(
            startup_counter=10,
            radiation_counts_per_30s=50,
            comm_voltage_v=8.0,
            payload_current_ma=100.0
        )
        assert response.type_name == "Startup and Radiation"

    def test_datatype3_response(self):
        """Test DataType3Response model."""
        response = DataType3Response(
            spacecraft_ground_id=42,
            comm_current_ma=100.0,
            sensor_voltage_v=5.0,
            bus_data_page=1
        )
        assert response.type_name == "Communication and Sensor"

    def test_datatype4_response(self):
        """Test DataType4Response model."""
        response = DataType4Response(
            experiment_phase="0b1010",
            comm_voltage_v=8.0,
            bus_voltage_v=5.0,
            register_file_wrap_count=3
        )
        assert response.type_name == "Experiment and Bus"


TYPE_SPECIFIC = [
    DataType1Response(
        power_port_status="0b1111",
        payload_board_temp_c=25.0,
        battery_voltage_v=8.0,
        payload_heater_current_ma=100.0,
    ),
    DataType2Response(
        startup_counter=10,
        radiation_counts_per_30s=50,
        comm_voltage_v=8.0,
        payload_current_ma=100.0,
    ),
    DataType3Response(
        spacecraft_ground_id=42,
        comm_current_ma=100.0,
        sensor_voltage_v=5.0,
        bus_data_page=1,
    ),
    DataType4Response(
        experiment_phase="0b1010",
        comm_voltage_v=8.0,
        bus_voltage_v=5.0,
        register_file_wrap_count=3,
    ),
]


class TestDecodeResponse:
    """Tests for DecodeResponse model."""

    @pytest.mark.parametrize("type_data", TYPE_SPECIFIC, ids=lambda t: type(t).__name__)
    def test_json_round_trip_keeps_data_type(self, type_data):
        """Parsing the JSON form picks the right member of the type_specific_data union."""
        response = DecodeResponse(
            success=True,
            raw_packet="EcAMSat.org   1DEA21020033021EBA02A80200004400F90830A23661515F5B",
            bus_time_seconds=2222621,
            solar_panel=SolarPanelResponse(panel_number=1, current_ma=100.0, temperature_c=25.0),
            data_type=1,
            type_specific_data=type_data,
            payload_page_number=68,
            median_card_temp_c=22.97,
            well_number=48,
            light_sensors=LightSensorResponse(red_hz=1000, green_hz=2000, blue_hz=3000),
        )
        parsed = DecodeResponse.model_validate_json(response.model_dump_json())

        assert type(parsed.type_specific_data) is type(type_data)
        assert parsed == response

    def test_missing_field_rejected(self):
        """A response without light sensor data is invalid."""
        with pytest.raises(ValidationError, match="light_sensors"):
            DecodeResponse(
                success=True,
                raw_packet="x",
                bus_time_seconds=1,
                solar_panel=SolarPanelResponse(panel_number=1, current_ma=1.0, temperature_c=1.0),
                data_type=1,
                type_specific_data=TYPE_SPECIFIC[0],
                payload_page_number=1,
                median_card_temp_c=1.0,
                well_number=0,
            )


class TestErrorResponse:
    """Tests for ErrorResponse model."""

    def test_error_response(self):
        """Test error response model."""
        response = ErrorResponse(
            error="Test error",
            details="Additional details"
        )
        assert response.success is False
        assert response.error == "Test error"
        assert response.details == "Additional details"

    def test_error_response_no_details(self):
        """Test error response without details."""
        response = ErrorResponse(error="Test error")
        assert response.success is False
        assert response.error == "Test error"
        assert response.details is None


class TestHealthResponse:
    """Tests for HealthResponse model."""

    def test_health_response_defaults(self):
        """Test health response default values."""
        response = HealthResponse(version="1.0.0")
        assert response.status == "healthy"
        assert response.service == "EcAMSat Beacon Decoder API"
        assert response.version == "1.0.0"
