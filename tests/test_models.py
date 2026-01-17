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
    SamplePacket,
    SamplesResponse,
    HealthResponse,
)


class TestDecodeRequest:
    """Tests for DecodeRequest model."""

    def test_valid_request(self):
        """Test valid decode request."""
        request = DecodeRequest(
            packet="EcAMSat.org   1DEA21020033021EBA02A80200004400F90830A23661515F5B"
        )
        assert len(request.packet) == 64

    def test_empty_packet_rejected(self):
        """Test that empty packet is rejected."""
        with pytest.raises(ValidationError):
            DecodeRequest(packet="")

    def test_too_long_packet_rejected(self):
        """Test that overly long packet is rejected."""
        with pytest.raises(ValidationError):
            DecodeRequest(packet="x" * 201)


class TestSolarPanelResponse:
    """Tests for SolarPanelResponse model."""

    def test_valid_response(self):
        """Test valid solar panel response."""
        response = SolarPanelResponse(
            panel_number=1,
            current_ma=100.5,
            temperature_c=25.3
        )
        assert response.panel_number == 1
        assert response.current_ma == 100.5
        assert response.temperature_c == 25.3


class TestDataTypeResponses:
    """Tests for data type response models."""

    def test_datatype1_response(self):
        """Test DataType1Response model."""
        response = DataType1Response(
            power_port_status="0b1111",
            payload_board_temp_c=25.0,
            battery_voltage_v=8.0,
            payload_heater_current_ma=100.0
        )
        assert response.type_name == "Power and Temperature"
        assert response.power_port_status == "0b1111"

    def test_datatype2_response(self):
        """Test DataType2Response model."""
        response = DataType2Response(
            startup_counter=10,
            radiation_counts_per_30s=50,
            comm_voltage_v=8.0,
            payload_current_ma=100.0
        )
        assert response.type_name == "Startup and Radiation"
        assert response.startup_counter == 10

    def test_datatype3_response(self):
        """Test DataType3Response model."""
        response = DataType3Response(
            spacecraft_ground_id=42,
            comm_current_ma=100.0,
            sensor_voltage_v=5.0,
            bus_data_page=1
        )
        assert response.type_name == "Communication and Sensor"
        assert response.spacecraft_ground_id == 42

    def test_datatype4_response(self):
        """Test DataType4Response model."""
        response = DataType4Response(
            experiment_phase="0b1010",
            comm_voltage_v=8.0,
            bus_voltage_v=5.0,
            register_file_wrap_count=3
        )
        assert response.type_name == "Experiment and Bus"
        assert response.experiment_phase == "0b1010"


class TestLightSensorResponse:
    """Tests for LightSensorResponse model."""

    def test_valid_response(self):
        """Test valid light sensor response."""
        response = LightSensorResponse(
            red_hz=1000,
            green_hz=2000,
            blue_hz=3000
        )
        assert response.red_hz == 1000
        assert response.green_hz == 2000
        assert response.blue_hz == 3000


class TestDecodeResponse:
    """Tests for DecodeResponse model."""

    def test_valid_response_type1(self):
        """Test valid decode response with type 1 data."""
        response = DecodeResponse(
            success=True,
            raw_packet="EcAMSat.org   1DEA21020033021EBA02A80200004400F90830A23661515F5B",
            bus_time_seconds=2222621,
            solar_panel=SolarPanelResponse(
                panel_number=1,
                current_ma=100.0,
                temperature_c=25.0
            ),
            data_type=1,
            type_specific_data=DataType1Response(
                power_port_status="0b1111",
                payload_board_temp_c=25.0,
                battery_voltage_v=8.0,
                payload_heater_current_ma=100.0
            ),
            payload_page_number=68,
            median_card_temp_c=22.97,
            well_number=48,
            light_sensors=LightSensorResponse(
                red_hz=1000,
                green_hz=2000,
                blue_hz=3000
            )
        )
        assert response.success is True
        assert response.data_type == 1

    def test_valid_response_type2(self):
        """Test valid decode response with type 2 data."""
        response = DecodeResponse(
            success=True,
            raw_packet="test",
            bus_time_seconds=100,
            solar_panel=SolarPanelResponse(
                panel_number=2,
                current_ma=100.0,
                temperature_c=25.0
            ),
            data_type=2,
            type_specific_data=DataType2Response(
                startup_counter=10,
                radiation_counts_per_30s=50,
                comm_voltage_v=8.0,
                payload_current_ma=100.0
            ),
            payload_page_number=1,
            median_card_temp_c=20.0,
            well_number=1,
            light_sensors=LightSensorResponse(
                red_hz=100,
                green_hz=200,
                blue_hz=300
            )
        )
        assert response.data_type == 2

    def test_valid_response_type3(self):
        """Test valid decode response with type 3 data."""
        response = DecodeResponse(
            success=True,
            raw_packet="test",
            bus_time_seconds=100,
            solar_panel=SolarPanelResponse(
                panel_number=3,
                current_ma=100.0,
                temperature_c=25.0
            ),
            data_type=3,
            type_specific_data=DataType3Response(
                spacecraft_ground_id=42,
                comm_current_ma=100.0,
                sensor_voltage_v=5.0,
                bus_data_page=1
            ),
            payload_page_number=1,
            median_card_temp_c=20.0,
            well_number=2,
            light_sensors=LightSensorResponse(
                red_hz=100,
                green_hz=200,
                blue_hz=300
            )
        )
        assert response.data_type == 3

    def test_valid_response_type4(self):
        """Test valid decode response with type 4 data."""
        response = DecodeResponse(
            success=True,
            raw_packet="test",
            bus_time_seconds=100,
            solar_panel=SolarPanelResponse(
                panel_number=4,
                current_ma=100.0,
                temperature_c=25.0
            ),
            data_type=4,
            type_specific_data=DataType4Response(
                experiment_phase="0b1010",
                comm_voltage_v=8.0,
                bus_voltage_v=5.0,
                register_file_wrap_count=3
            ),
            payload_page_number=1,
            median_card_temp_c=20.0,
            well_number=3,
            light_sensors=LightSensorResponse(
                red_hz=100,
                green_hz=200,
                blue_hz=300
            )
        )
        assert response.data_type == 4


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


class TestSamplePacket:
    """Tests for SamplePacket model."""

    def test_sample_packet(self):
        """Test sample packet model."""
        sample = SamplePacket(
            packet="EcAMSat.org   1DEA21020033021EBA02A80200004400F90830A23661515F5B",
            description="Test sample"
        )
        assert len(sample.packet) == 64
        assert sample.description == "Test sample"


class TestSamplesResponse:
    """Tests for SamplesResponse model."""

    def test_samples_response(self):
        """Test samples response model."""
        response = SamplesResponse(
            samples=[
                SamplePacket(packet="x" * 64, description="Sample 1"),
                SamplePacket(packet="y" * 64, description="Sample 2"),
            ]
        )
        assert len(response.samples) == 2


class TestHealthResponse:
    """Tests for HealthResponse model."""

    def test_health_response(self):
        """Test health response model."""
        response = HealthResponse(
            status="healthy",
            version="2.0.0"
        )
        assert response.status == "healthy"
        assert response.version == "2.0.0"
        assert response.service == "EcAMSat Beacon Decoder API"

    def test_health_response_defaults(self):
        """Test health response default values."""
        response = HealthResponse(version="1.0.0")
        assert response.status == "healthy"
        assert response.service == "EcAMSat Beacon Decoder API"
