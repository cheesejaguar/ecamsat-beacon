"""
Unit tests for the beacon decoder module.
"""

import json
from dataclasses import asdict
from pathlib import Path

import pytest
from backend.decoder import (
    reverse_endian,
    validate_packet,
    decode_solar_panel,
    decode_type1,
    decode_type2,
    decode_type3,
    decode_type4,
    decode_beacon,
    BeaconDecodeError,
    SAMPLE_BEACONS,
    SolarPanelData,
    DataType1,
    DataType2,
    DataType3,
    DataType4,
    DecodedBeacon,
)

GOLDEN_FILE = Path(__file__).parent / "golden_decode.json"


class TestReverseEndian:
    """Tests for the reverse_endian function."""

    def test_reverse_endian_2_bytes(self):
        """2-byte values should be returned unchanged."""
        assert reverse_endian("AB", 2) == "AB"
        assert reverse_endian("00", 2) == "00"
        assert reverse_endian("FF", 2) == "FF"

    def test_reverse_endian_4_bytes(self):
        """4-byte values should swap byte pairs."""
        assert reverse_endian("ABCD", 4) == "CDAB"
        assert reverse_endian("1234", 4) == "3412"
        assert reverse_endian("0000", 4) == "0000"
        assert reverse_endian("FFFF", 4) == "FFFF"

    def test_reverse_endian_6_bytes(self):
        """6-byte values should reverse in 2-byte chunks."""
        assert reverse_endian("ABCDEF", 6) == "EFCDAB"
        assert reverse_endian("123456", 6) == "563412"
        assert reverse_endian("000000", 6) == "000000"

    def test_reverse_endian_invalid_length(self):
        """Invalid lengths should raise ValueError."""
        with pytest.raises(ValueError, match="Unsupported length"):
            reverse_endian("ABCDEFGH", 8)
        with pytest.raises(ValueError, match="Unsupported length"):
            reverse_endian("A", 1)
        with pytest.raises(ValueError, match="Unsupported length"):
            reverse_endian("ABC", 3)


class TestValidatePacket:
    """Tests for the validate_packet function."""

    def test_valid_packet(self):
        """Valid packets should pass validation."""
        packet = "EcAMSat.org   1DEA21020033021EBA02A80200004400F90830A23661515F5B"
        is_valid, error = validate_packet(packet)
        assert is_valid is True
        assert error == ""

    def test_packet_wrong_length_short(self):
        """Packets shorter than 64 chars should fail."""
        packet = "EcAMSat.org   1DEA21"
        is_valid, error = validate_packet(packet)
        assert is_valid is False
        assert "exactly 64 characters" in error
        assert "got 20" in error

    def test_packet_wrong_length_long(self):
        """Packets longer than 64 chars should fail."""
        packet = "EcAMSat.org   1DEA21020033021EBA02A80200004400F90830A23661515F5BEXTRA"
        is_valid, error = validate_packet(packet)
        assert is_valid is False
        assert "exactly 64 characters" in error

    def test_packet_wrong_header(self):
        """Packets with wrong header should fail."""
        packet = "WrongHeader   1DEA21020033021EBA02A80200004400F90830A23661515F5B"
        is_valid, error = validate_packet(packet)
        assert is_valid is False
        assert "Invalid header" in error

    def test_packet_invalid_hex(self):
        """Packets with invalid hex characters should fail."""
        packet = "EcAMSat.org   ZZZZ21020033021EBA02A80200004400F90830A23661515F5B"
        is_valid, error = validate_packet(packet)
        assert is_valid is False
        assert "invalid hexadecimal" in error

    @pytest.mark.parametrize("hex_portion", [
        # int(x, 16) accepts all of these, but none is a hex digit string
        "+DEA21020033021EBA02A80200004400F90830A23661515F5B",
        "1D_A21020033021EBA02A80200004400F90830A23661515F5B",
        "0xEA21020033021EBA02A80200004400F90830A23661515F5B",
        " DEA21020033021EBA02A80200004400F90830A23661515F5B",
        "1DEA21020033021EBA02A80200004400F90830A23661515F5\u0663",
    ])
    def test_packet_int_parsable_but_not_hex(self, hex_portion):
        """Signs, underscores, 0x prefixes, spaces and non-ASCII digits are rejected."""
        packet = "EcAMSat.org   " + hex_portion
        assert len(packet) == 64
        is_valid, error = validate_packet(packet)
        assert is_valid is False
        assert "invalid hexadecimal" in error

    def test_lowercase_hex_accepted(self):
        """Lowercase hex digits are valid (one ham-received packet uses them)."""
        packet = "EcAMSat.org   1dea21020033021eba02a80200004400f90830a23661515f5b"
        assert validate_packet(packet) == (True, "")


class TestDecodeSolarPanel:
    """Tests for the decode_solar_panel function."""

    def test_solar_panel_type1(self):
        """Test solar panel decoding for data type 1."""
        result = decode_solar_panel(100, 500, 1)
        assert isinstance(result, SolarPanelData)
        assert result.panel_number == 1
        # 100 * 1.8678 + 3.41 = 190.19
        assert result.current_ma == pytest.approx(190.19, rel=0.01)
        # 500 * 0.0557 - 15.37 = 12.48
        assert result.temperature_c == pytest.approx(12.48, rel=0.01)

    def test_solar_panel_type2(self):
        """Test solar panel decoding for data type 2."""
        result = decode_solar_panel(100, 500, 2)
        assert result.panel_number == 2
        # 100 * 0.9542 - 1.07 = 94.35
        assert result.current_ma == pytest.approx(94.35, rel=0.01)
        # 500 * 0.0563 - 15.85 = 12.30
        assert result.temperature_c == pytest.approx(12.30, rel=0.01)

    def test_solar_panel_type3(self):
        """Test solar panel decoding for data type 3."""
        result = decode_solar_panel(100, 500, 3)
        assert result.panel_number == 3
        # 100 * 1.8785 - 0.41 = 187.44
        assert result.current_ma == pytest.approx(187.44, rel=0.01)
        # 500 * 0.0559 - 14.56 = 13.39
        assert result.temperature_c == pytest.approx(13.39, rel=0.01)

    def test_solar_panel_type4(self):
        """Test solar panel decoding for data type 4."""
        result = decode_solar_panel(100, 500, 4)
        assert result.panel_number == 4
        # 100 * 0.9562 - 1.04 = 94.58
        assert result.current_ma == pytest.approx(94.58, rel=0.01)
        # 500 * 0.0560 - 15.75 = 12.25
        assert result.temperature_c == pytest.approx(12.25, rel=0.01)


class TestDecodeType1:
    """Tests for decode_type1 function."""

    def test_decode_type1_basic(self):
        """Test basic type 1 decoding."""
        result = decode_type1("1E", 500, 700, 100)
        assert isinstance(result, DataType1)
        assert result.power_port_status == "0b11110"
        # 500 * 0.0554 - 15.75 = 11.95
        assert result.payload_board_temp_c == pytest.approx(11.95, rel=0.01)
        # 700 * 0.0119 - 0.05 = 8.28
        assert result.battery_voltage_v == pytest.approx(8.28, rel=0.01)
        # 100 * 3.2922 + 8.04 = 337.26
        assert result.payload_heater_current_ma == pytest.approx(337.26, rel=0.01)

    def test_decode_type1_zeros(self):
        """Test type 1 decoding with zero values."""
        result = decode_type1("00", 0, 0, 0)
        assert result.power_port_status == "0b0"
        assert result.payload_board_temp_c == pytest.approx(-15.75, rel=0.01)
        assert result.battery_voltage_v == pytest.approx(-0.05, rel=0.01)
        assert result.payload_heater_current_ma == pytest.approx(8.04, rel=0.01)


class TestDecodeType2:
    """Tests for decode_type2 function."""

    def test_decode_type2_basic(self):
        """Test basic type 2 decoding."""
        result = decode_type2("0A", 50, 700, 100)
        assert isinstance(result, DataType2)
        assert result.startup_counter == 10
        assert result.radiation_counts_per_30s == 50
        # 700 * 0.0119 + 0.01 = 8.34
        assert result.comm_voltage_v == pytest.approx(8.34, rel=0.01)
        # 100 * 3.4281 - 22.69 = 320.12
        assert result.payload_current_ma == pytest.approx(320.12, rel=0.01)

    def test_decode_type2_max_values(self):
        """Test type 2 decoding with larger values."""
        result = decode_type2("FF", 1000, 1000, 1000)
        assert result.startup_counter == 255
        assert result.radiation_counts_per_30s == 1000
        # 1000 * 0.0119 + 0.01 = 11.91
        assert result.comm_voltage_v == pytest.approx(11.91)
        # 1000 * 3.4281 - 22.69 = 3405.41
        assert result.payload_current_ma == pytest.approx(3405.41)


class TestDecodeType3:
    """Tests for decode_type3 function."""

    def test_decode_type3_basic(self):
        """Test basic type 3 decoding."""
        result = decode_type3("2A", 100, 500, 42)
        assert isinstance(result, DataType3)
        assert result.spacecraft_ground_id == 42
        # 100 * 4.3330 + 16.27 = 449.57
        assert result.comm_current_ma == pytest.approx(449.57, rel=0.01)
        # 500 * 0.0130 - 0.48 = 6.02
        assert result.sensor_voltage_v == pytest.approx(6.02, rel=0.01)
        assert result.bus_data_page == 42


class TestDecodeType4:
    """Tests for decode_type4 function."""

    def test_decode_type4_basic(self):
        """Test basic type 4 decoding."""
        result = decode_type4("0F", 700, 1000, 5)
        assert isinstance(result, DataType4)
        assert result.experiment_phase == "0b1111"
        # 700 * 0.0119 + 0.01 = 8.34
        assert result.comm_voltage_v == pytest.approx(8.34, rel=0.01)
        # 1000 * 0.0059 = 5.9
        assert result.bus_voltage_v == pytest.approx(5.9, rel=0.01)
        assert result.register_file_wrap_count == 5


class TestDecodeBeacon:
    """Tests for the main decode_beacon function."""

    def test_decode_beacon_sample1(self):
        """Test decoding of first sample packet (Type 1)."""
        packet = "EcAMSat.org   1DEA21020033021EBA02A80200004400F90830A23661515F5B"
        result = decode_beacon(packet)

        assert isinstance(result, DecodedBeacon)
        assert result.raw_packet == packet
        assert result.bus_time_seconds == 2222621
        assert result.data_type == 1
        assert result.well_number == 48
        assert result.payload_page_number == 68
        assert isinstance(result.type_specific_data, DataType1)

    def test_decode_beacon_sample2(self):
        """Test decoding of second sample packet (Type 2)."""
        packet = "EcAMSat.org   1DEA210000F10101000007000A004400F9080DA236BC4DB84F"
        result = decode_beacon(packet)

        assert result.data_type == 2
        assert result.well_number == 13
        assert result.solar_panel == SolarPanelData(2, -1.07, 12.1311)
        assert result.type_specific_data == DataType2(
            startup_counter=1,
            radiation_counts_per_30s=0,
            comm_voltage_v=0.0933,
            payload_current_ma=11.591,
        )

    def test_decode_beacon_type3(self):
        """Test decoding of a Type 3 packet."""
        packet = "EcAMSat.org   D900220000C6010F5B00A2014F005100B3082ACC3C674A5F5B"
        result = decode_beacon(packet)

        assert result.data_type == 3
        assert result.well_number == 42
        assert result.bus_time_seconds == 2228441
        assert result.solar_panel == SolarPanelData(3, -0.41, 10.8186)
        assert result.type_specific_data == DataType3(
            spacecraft_ground_id=15,
            comm_current_ma=410.573,
            sensor_voltage_v=4.954,
            bus_data_page=79,
        )

    def test_decode_beacon_type4(self):
        """Test decoding of a Type 4 packet."""
        # Well number 0x03 = 3, 3 % 4 = 3, so type = 4
        # Modified packet with well number changed to 03 at position 50:52
        packet = "EcAMSat.org   1DEA21020033021EBA02A80200004400F90803A23661515F5B"
        result = decode_beacon(packet)

        assert result.data_type == 4
        assert result.well_number == 3
        # Same raw bytes as sample 1, decoded with panel 4 / type 4 calibration
        assert result.solar_panel == SolarPanelData(4, 0.8724, 15.778)
        assert result.type_specific_data == DataType4(
            experiment_phase="0b11110",
            comm_voltage_v=8.3162,
            bus_voltage_v=4.012,
            register_file_wrap_count=0,
        )

    def test_decode_beacon_with_whitespace(self):
        """Test that whitespace is trimmed from packet."""
        packet = "  EcAMSat.org   1DEA21020033021EBA02A80200004400F90830A23661515F5B  \n"
        result = decode_beacon(packet)
        assert result.bus_time_seconds == 2222621

    def test_decode_beacon_invalid_packet(self):
        """Test that invalid packets raise BeaconDecodeError."""
        with pytest.raises(BeaconDecodeError, match="exactly 64 characters"):
            decode_beacon("short")

    def test_decode_beacon_invalid_header(self):
        """Test that wrong header raises BeaconDecodeError."""
        packet = "WrongHeader   1DEA21020033021EBA02A80200004400F90830A23661515F5B"
        with pytest.raises(BeaconDecodeError, match="Invalid header"):
            decode_beacon(packet)

    def test_decode_beacon_invalid_hex(self):
        """Test that invalid hex raises BeaconDecodeError."""
        packet = "EcAMSat.org   ZZZZ21020033021EBA02A80200004400F90830A23661515F5B"
        with pytest.raises(BeaconDecodeError, match="invalid hexadecimal"):
            decode_beacon(packet)

    def test_decode_all_sample_beacons(self):
        """Sample beacons decode to the data types the API describes them as."""
        assert [decode_beacon(p).data_type for p in SAMPLE_BEACONS] == [1, 2, 3, 1, 2]

    def test_matches_golden_file(self):
        """Every ham-received packet decodes exactly as recorded in golden_decode.json.

        The JS decoder is tested against the same file, so this keeps both in sync.
        """
        golden = json.loads(GOLDEN_FILE.read_text())
        assert len(golden) == 32
        for entry in golden:
            assert asdict(decode_beacon(entry["packet"])) == entry["decoded"], entry["packet"]

    def test_decode_beacon_light_sensors(self):
        """Test that light sensor values are decoded correctly."""
        packet = "EcAMSat.org   1DEA21020033021EBA02A80200004400F90830A23661515F5B"
        result = decode_beacon(packet)

        # 3661 -> 6136 = 13986, 5151 -> 5151 = 20833, 5F5B -> 5B5F = 23391
        assert result.taos_r_hz == 13986
        assert result.taos_g_hz == 20833
        assert result.taos_b_hz == 23391

    def test_decode_beacon_median_card_temp(self):
        """Test median card temperature calculation."""
        packet = "EcAMSat.org   1DEA21020033021EBA02A80200004400F90830A23661515F5B"
        result = decode_beacon(packet)

        # 46:50 is "F908" -> reversed = "08F9" = 2297 -> /100 = 22.97
        assert result.median_card_temp_c == 22.97


class TestSampleBeacons:
    """Tests for the SAMPLE_BEACONS constant."""

    def test_sample_beacons_exist(self):
        """Verify sample beacons are defined."""
        assert len(SAMPLE_BEACONS) > 0

    def test_sample_beacons_valid_format(self):
        """Verify all sample beacons have correct format."""
        for packet in SAMPLE_BEACONS:
            assert len(packet) == 64
            assert packet.startswith("EcAMSat.org   ")
