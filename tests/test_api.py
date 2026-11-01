"""
Unit tests for the FastAPI endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app, convert_type_data, __version__
from backend.decoder import (
    DataType1, DataType2, DataType3, DataType4, SAMPLE_BEACONS, decode_beacon,
)


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

        samples = response.json()["samples"]
        assert [s["packet"] for s in samples] == SAMPLE_BEACONS

        # Each description names the data type the packet actually decodes to
        for sample in samples:
            data_type = decode_beacon(sample["packet"]).data_type
            assert sample["description"].endswith(f"Data Type {data_type}")


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

        assert data["well_number"] == 48
        assert data["payload_page_number"] == 68
        assert data["median_card_temp_c"] == 22.97
        assert data["solar_panel"] == {
            "panel_number": 1, "current_ma": 7.1456, "temperature_c": 15.9891,
        }
        assert data["type_specific_data"] == {
            "type_name": "Power and Temperature",
            "power_port_status": "0b11110",
            "payload_board_temp_c": 22.9192,
            "battery_voltage_v": 8.042,
            "payload_heater_current_ma": 8.04,
        }
        assert data["light_sensors"] == {
            "red_hz": 13986, "green_hz": 20833, "blue_hz": 23391,
        }

    def test_decode_type2_packet(self, client):
        """Test decoding a Type 2 packet."""
        packet = "EcAMSat.org   1DEA210000F10101000007000A004400F9080DA236BC4DB84F"
        response = client.post("/api/decode", json={"packet": packet})

        assert response.status_code == 200
        data = response.json()

        assert data["data_type"] == 2
        assert data["type_specific_data"] == {
            "type_name": "Startup and Radiation",
            "startup_counter": 1,
            "radiation_counts_per_30s": 0,
            "comm_voltage_v": 0.0933,
            "payload_current_ma": 11.591,
        }

    def test_decode_type3_packet(self, client):
        """Test decoding a Type 3 packet."""
        packet = "EcAMSat.org   D900220000C6010F5B00A2014F005100B3082ACC3C674A5F5B"
        response = client.post("/api/decode", json={"packet": packet})

        assert response.status_code == 200
        data = response.json()

        assert data["data_type"] == 3
        assert data["type_specific_data"] == {
            "type_name": "Communication and Sensor",
            "spacecraft_ground_id": 15,
            "comm_current_ma": 410.573,
            "sensor_voltage_v": 4.954,
            "bus_data_page": 79,
        }

    def test_decode_type4_packet(self, client):
        """Test decoding a Type 4 packet."""
        # Well number 0x03 = 3, 3 % 4 = 3, so type = 4
        packet = "EcAMSat.org   1DEA21020033021EBA02A80200004400F90803A23661515F5B"
        response = client.post("/api/decode", json={"packet": packet})

        assert response.status_code == 200
        data = response.json()

        assert data["data_type"] == 4
        assert data["well_number"] == 3
        assert data["type_specific_data"] == {
            "type_name": "Experiment and Bus",
            "experiment_phase": "0b11110",
            "comm_voltage_v": 8.3162,
            "bus_voltage_v": 4.012,
            "register_file_wrap_count": 0,
        }

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
        assert data["raw_packet"] == packet.strip()
        assert data["bus_time_seconds"] == 2222621

    def test_decode_signed_hex_rejected(self, client):
        """A packet int() would parse but that is not pure hex is a 400, not a 500."""
        packet = "EcAMSat.org   +DEA21020033021EBA02A80200004400F90830A23661515F5B"
        response = client.post("/api/decode", json={"packet": packet})

        assert response.status_code == 400
        assert "hexadecimal" in response.json()["detail"]


class TestFrontendEndpoint:
    """Tests for the frontend serving endpoint."""

    def test_serve_frontend(self, client):
        """Test that root serves the frontend HTML."""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "/static/js/app.js" in response.text


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
