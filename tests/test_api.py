"""
Unit tests for the FastAPI endpoints.
"""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from backend.main import app, convert_type_data, __version__
from backend.decoder import DataType1, DataType2, DataType3, DataType4


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    def test_health_check(self, client):
        """Test health endpoint returns correct data."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == __version__
        assert data["service"] == "EcAMSat Beacon Decoder API"


class TestSamplesEndpoint:
    """Tests for the /api/samples endpoint."""

    def test_get_samples(self, client):
        """Test samples endpoint returns sample packets."""
        response = client.get("/api/samples")
        assert response.status_code == 200

        data = response.json()
        assert "samples" in data
        assert len(data["samples"]) > 0

        # Verify sample structure
        sample = data["samples"][0]
        assert "packet" in sample
        assert "description" in sample
        assert len(sample["packet"]) == 64


class TestDecodeEndpoint:
    """Tests for the /api/decode endpoint."""

    def test_decode_valid_packet(self, client):
        """Test decoding a valid packet."""
        packet = "EcAMSat.org   1DEA21020033021EBA02A80200004400F90830A23661515F5B"
        response = client.post("/api/decode", json={"packet": packet})

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["raw_packet"] == packet
        assert data["bus_time_seconds"] == 2222621
        assert data["data_type"] == 1

        # Check solar panel data
        assert "solar_panel" in data
        assert data["solar_panel"]["panel_number"] == 1
        assert "current_ma" in data["solar_panel"]
        assert "temperature_c" in data["solar_panel"]

        # Check type-specific data
        assert "type_specific_data" in data
        assert data["type_specific_data"]["type_name"] == "Power and Temperature"

        # Check light sensors
        assert "light_sensors" in data
        assert "red_hz" in data["light_sensors"]
        assert "green_hz" in data["light_sensors"]
        assert "blue_hz" in data["light_sensors"]

    def test_decode_type2_packet(self, client):
        """Test decoding a Type 2 packet."""
        packet = "EcAMSat.org   1DEA210000F10101000007000A004400F9080DA236BC4DB84F"
        response = client.post("/api/decode", json={"packet": packet})

        assert response.status_code == 200
        data = response.json()

        assert data["data_type"] == 2
        assert data["type_specific_data"]["type_name"] == "Startup and Radiation"
        assert "startup_counter" in data["type_specific_data"]
        assert "radiation_counts_per_30s" in data["type_specific_data"]

    def test_decode_type3_packet(self, client):
        """Test decoding a Type 3 packet."""
        packet = "EcAMSat.org   D900220000C6010F5B00A2014F005100B3082ACC3C674A5F5B"
        response = client.post("/api/decode", json={"packet": packet})

        assert response.status_code == 200
        data = response.json()

        assert data["data_type"] == 3
        assert data["type_specific_data"]["type_name"] == "Communication and Sensor"
        assert "spacecraft_ground_id" in data["type_specific_data"]
        assert "comm_current_ma" in data["type_specific_data"]

    def test_decode_type4_packet(self, client):
        """Test decoding a Type 4 packet."""
        # Well number 0x03 = 3, 3 % 4 = 3, so type = 4
        packet = "EcAMSat.org   1DEA21020033021EBA02A80200004400F90803A23661515F5B"
        response = client.post("/api/decode", json={"packet": packet})

        assert response.status_code == 200
        data = response.json()

        assert data["data_type"] == 4
        assert data["well_number"] == 3
        assert data["type_specific_data"]["type_name"] == "Experiment and Bus"
        assert "experiment_phase" in data["type_specific_data"]
        assert "bus_voltage_v" in data["type_specific_data"]

    def test_decode_invalid_packet_short(self, client):
        """Test decoding a packet that's too short."""
        response = client.post("/api/decode", json={"packet": "short"})

        assert response.status_code == 400
        data = response.json()
        assert "64 characters" in data["detail"]

    def test_decode_invalid_packet_wrong_header(self, client):
        """Test decoding a packet with wrong header."""
        packet = "WrongHeader   1DEA21020033021EBA02A80200004400F90830A23661515F5B"
        response = client.post("/api/decode", json={"packet": packet})

        assert response.status_code == 400
        data = response.json()
        assert "Invalid header" in data["detail"]

    def test_decode_invalid_hex(self, client):
        """Test decoding a packet with invalid hex."""
        packet = "EcAMSat.org   ZZZZ21020033021EBA02A80200004400F90830A23661515F5B"
        response = client.post("/api/decode", json={"packet": packet})

        assert response.status_code == 400
        data = response.json()
        assert "hexadecimal" in data["detail"]

    def test_decode_empty_packet(self, client):
        """Test decoding an empty packet."""
        response = client.post("/api/decode", json={"packet": ""})

        # Pydantic validation should catch this
        assert response.status_code == 422  # Validation error

    def test_decode_missing_packet_field(self, client):
        """Test request without packet field."""
        response = client.post("/api/decode", json={})

        assert response.status_code == 422  # Validation error

    def test_decode_with_whitespace(self, client):
        """Test that whitespace around packet is handled."""
        packet = "  EcAMSat.org   1DEA21020033021EBA02A80200004400F90830A23661515F5B  "
        response = client.post("/api/decode", json={"packet": packet})

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_decode_internal_error(self, client):
        """Test that unexpected errors return 500."""
        with patch("backend.main.decode_beacon") as mock_decode:
            mock_decode.side_effect = RuntimeError("Unexpected error")
            packet = "EcAMSat.org   1DEA21020033021EBA02A80200004400F90830A23661515F5B"
            response = client.post("/api/decode", json={"packet": packet})

            assert response.status_code == 500
            data = response.json()
            assert "Decoding error" in data["detail"]
            assert "Unexpected error" in data["detail"]


class TestFrontendEndpoint:
    """Tests for the frontend serving endpoint."""

    def test_serve_frontend(self, client):
        """Test that root serves the frontend HTML."""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


class TestConvertTypeData:
    """Tests for the convert_type_data helper function."""

    def test_convert_type1_data(self):
        """Test converting DataType1 to response model."""
        data = DataType1(
            power_port_status="0b1111",
            payload_board_temp_c=25.0,
            battery_voltage_v=8.0,
            payload_heater_current_ma=100.0
        )
        result = convert_type_data(1, data)

        assert result.type_name == "Power and Temperature"
        assert result.power_port_status == "0b1111"
        assert result.payload_board_temp_c == 25.0
        assert result.battery_voltage_v == 8.0
        assert result.payload_heater_current_ma == 100.0

    def test_convert_type2_data(self):
        """Test converting DataType2 to response model."""
        data = DataType2(
            startup_counter=10,
            radiation_counts_per_30s=50,
            comm_voltage_v=8.0,
            payload_current_ma=100.0
        )
        result = convert_type_data(2, data)

        assert result.type_name == "Startup and Radiation"
        assert result.startup_counter == 10
        assert result.radiation_counts_per_30s == 50

    def test_convert_type3_data(self):
        """Test converting DataType3 to response model."""
        data = DataType3(
            spacecraft_ground_id=42,
            comm_current_ma=100.0,
            sensor_voltage_v=5.0,
            bus_data_page=1
        )
        result = convert_type_data(3, data)

        assert result.type_name == "Communication and Sensor"
        assert result.spacecraft_ground_id == 42

    def test_convert_type4_data(self):
        """Test converting DataType4 to response model."""
        data = DataType4(
            experiment_phase="0b1010",
            comm_voltage_v=8.0,
            bus_voltage_v=5.0,
            register_file_wrap_count=3
        )
        result = convert_type_data(4, data)

        assert result.type_name == "Experiment and Bus"
        assert result.experiment_phase == "0b1010"

    def test_convert_invalid_type(self):
        """Test that invalid type raises ValueError."""
        data = DataType1(
            power_port_status="0b1111",
            payload_board_temp_c=25.0,
            battery_voltage_v=8.0,
            payload_heater_current_ma=100.0
        )
        # Pass wrong type number
        with pytest.raises(ValueError, match="Unknown data type"):
            convert_type_data(5, data)

    def test_convert_mismatched_type(self):
        """Test that mismatched type/data raises ValueError."""
        data = DataType1(
            power_port_status="0b1111",
            payload_board_temp_c=25.0,
            battery_voltage_v=8.0,
            payload_heater_current_ma=100.0
        )
        # Pass DataType1 but say it's type 2
        with pytest.raises(ValueError, match="Unknown data type"):
            convert_type_data(2, data)


class TestStaticFiles:
    """Tests for static file serving."""

    def test_css_served(self, client):
        """Test that CSS file is served."""
        response = client.get("/static/css/style.css")
        assert response.status_code == 200
        assert "text/css" in response.headers["content-type"]

    def test_js_served(self, client):
        """Test that JS file is served."""
        response = client.get("/static/js/app.js")
        assert response.status_code == 200
        assert "javascript" in response.headers["content-type"]
