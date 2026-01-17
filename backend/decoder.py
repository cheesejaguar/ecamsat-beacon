"""
EcAMSat Beacon Decoder Logic

Originally written by Aaron Cohen on 11/20/2017
Based on information from publicly available beacon decoding instructions:
http://ecamsat.engr.scu.edu/beacon/EcAMSatBeaconDecoding.pdf

Rewritten for FastAPI by Claude
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SolarPanelData:
    panel_number: int
    current_ma: float
    temperature_c: float


@dataclass
class DataType1:
    """Data Type 1: Power and Temperature Data"""
    power_port_status: str
    payload_board_temp_c: float
    battery_voltage_v: float
    payload_heater_current_ma: float


@dataclass
class DataType2:
    """Data Type 2: Startup and Radiation Data"""
    startup_counter: int
    radiation_counts_per_30s: int
    comm_voltage_v: float
    payload_current_ma: float


@dataclass
class DataType3:
    """Data Type 3: Communication and Sensor Data"""
    spacecraft_ground_id: int
    comm_current_ma: float
    sensor_voltage_v: float
    bus_data_page: int


@dataclass
class DataType4:
    """Data Type 4: Experiment and Bus Data"""
    experiment_phase: str
    comm_voltage_v: float
    bus_voltage_v: float
    register_file_wrap_count: int


@dataclass
class DecodedBeacon:
    """Complete decoded beacon data"""
    raw_packet: str
    bus_time_seconds: int
    solar_panel: SolarPanelData
    data_type: int
    type_specific_data: DataType1 | DataType2 | DataType3 | DataType4
    payload_page_number: int
    median_card_temp_c: float
    well_number: int
    taos_r_hz: int
    taos_g_hz: int
    taos_b_hz: int


class BeaconDecodeError(Exception):
    """Exception raised when beacon decoding fails"""
    pass


def reverse_endian(byte_str: str, length: int) -> str:
    """
    Convert little-endian hexadecimal string to big-endian format.

    Args:
        byte_str: Hexadecimal string to convert
        length: Number of characters (2, 4, or 6)

    Returns:
        Big-endian hexadecimal string
    """
    if length == 2:
        return byte_str
    elif length == 4:
        return byte_str[2:4] + byte_str[0:2]
    elif length == 6:
        return byte_str[4:6] + byte_str[2:4] + byte_str[0:2]
    else:
        raise ValueError(f"Unsupported length: {length}")


def validate_packet(packet: str) -> tuple[bool, str]:
    """
    Validate the beacon packet format.

    Args:
        packet: The raw beacon packet string

    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(packet) != 64:
        return False, f"Beacon packet must be exactly 64 characters (got {len(packet)})"

    expected_header = 'EcAMSat.org   '
    if packet[0:14] != expected_header:
        return False, f"Invalid header. Expected '{expected_header}', got '{packet[0:14]}'"

    # Check if remaining characters are valid hex
    hex_portion = packet[14:]
    try:
        int(hex_portion, 16)
    except ValueError:
        return False, "Packet contains invalid hexadecimal characters"

    return True, ""


def decode_solar_panel(solar_i_raw: int, solar_t_raw: int, data_type: int) -> SolarPanelData:
    """
    Decode solar panel data based on data type.

    Each solar panel has unique calibration factors.
    """
    calibration = {
        1: (1.8678, 3.41, 0.0557, -15.37),
        2: (0.9542, -1.07, 0.0563, -15.85),
        3: (1.8785, -0.41, 0.0559, -14.56),
        4: (0.9562, -1.04, 0.0560, -15.75),
    }

    i_mult, i_offset, t_mult, t_offset = calibration[data_type]

    current_ma = solar_i_raw * i_mult + i_offset
    temperature_c = solar_t_raw * t_mult + t_offset

    return SolarPanelData(
        panel_number=data_type,
        current_ma=round(current_ma, 4),
        temperature_c=round(temperature_c, 4)
    )


def decode_type1(health0: str, health1: int, health2: int, health3: int) -> DataType1:
    """Decode Data Type 1: Power and Temperature Data"""
    power_port_status = bin(int(health0, 16))
    payload_board_temp_c = (health1 * 0.0554) - 15.75
    battery_voltage_v = (health2 * 0.0119) - 0.05
    payload_heater_current_ma = (health3 * 3.2922) + 8.04

    return DataType1(
        power_port_status=power_port_status,
        payload_board_temp_c=round(payload_board_temp_c, 4),
        battery_voltage_v=round(battery_voltage_v, 4),
        payload_heater_current_ma=round(payload_heater_current_ma, 4)
    )


def decode_type2(health0: str, health1: int, health2: int, health3: int) -> DataType2:
    """Decode Data Type 2: Startup and Radiation Data"""
    startup_counter = int(health0, 16)
    radiation_counts = health1
    comm_voltage_v = (health2 * 0.0119) + 0.01
    payload_current_ma = (health3 * 3.4281) - 22.69

    return DataType2(
        startup_counter=startup_counter,
        radiation_counts_per_30s=radiation_counts,
        comm_voltage_v=round(comm_voltage_v, 4),
        payload_current_ma=round(payload_current_ma, 4)
    )


def decode_type3(health0: str, health1: int, health2: int, health3: int) -> DataType3:
    """Decode Data Type 3: Communication and Sensor Data"""
    spacecraft_ground_id = int(health0, 16)
    comm_current_ma = (health1 * 4.3330) + 16.27
    sensor_voltage_v = (health2 * 0.0130) - 0.48
    bus_data_page = health3

    return DataType3(
        spacecraft_ground_id=spacecraft_ground_id,
        comm_current_ma=round(comm_current_ma, 4),
        sensor_voltage_v=round(sensor_voltage_v, 4),
        bus_data_page=bus_data_page
    )


def decode_type4(health0: str, health1: int, health2: int, health3: int) -> DataType4:
    """Decode Data Type 4: Experiment and Bus Data"""
    experiment_phase = bin(int(health0, 16))
    comm_voltage_v = (health1 * 0.0119) + 0.01
    bus_voltage_v = (health2 * 0.0059)
    wrap_count = health3

    return DataType4(
        experiment_phase=experiment_phase,
        comm_voltage_v=round(comm_voltage_v, 4),
        bus_voltage_v=round(bus_voltage_v, 4),
        register_file_wrap_count=wrap_count
    )


def decode_beacon(packet: str) -> DecodedBeacon:
    """
    Decode a complete EcAMSat beacon packet.

    Args:
        packet: 64-character beacon packet string

    Returns:
        DecodedBeacon object with all decoded data

    Raises:
        BeaconDecodeError: If packet validation or decoding fails
    """
    # Clean up the packet (remove whitespace)
    packet = packet.strip()

    # Validate the packet
    is_valid, error = validate_packet(packet)
    if not is_valid:
        raise BeaconDecodeError(error)

    # Parse raw fields
    bus_time_raw = packet[14:20]
    solar_i_raw = packet[20:24]
    solar_t_raw = packet[24:28]
    health0 = packet[28:30]
    health1_raw = packet[30:34]
    health2_raw = packet[34:38]
    health3_raw = packet[38:42]
    page_number_raw = packet[42:46]
    card_temp_raw = packet[46:50]
    well_number_raw = packet[50:52]
    taos_r_raw = packet[52:56]
    taos_g_raw = packet[56:60]
    taos_b_raw = packet[60:64]

    # Convert little-endian to big-endian
    bus_time = reverse_endian(bus_time_raw, 6)
    solar_i = reverse_endian(solar_i_raw, 4)
    solar_t = reverse_endian(solar_t_raw, 4)
    health1 = reverse_endian(health1_raw, 4)
    health2 = reverse_endian(health2_raw, 4)
    health3 = reverse_endian(health3_raw, 4)
    page_number = reverse_endian(page_number_raw, 4)
    card_temp = reverse_endian(card_temp_raw, 4)
    taos_r = reverse_endian(taos_r_raw, 4)
    taos_g = reverse_endian(taos_g_raw, 4)
    taos_b = reverse_endian(taos_b_raw, 4)

    # Convert to integers
    bus_time_seconds = int(bus_time, 16)
    solar_i_int = int(solar_i, 16)
    solar_t_int = int(solar_t, 16)
    health1_int = int(health1, 16)
    health2_int = int(health2, 16)
    health3_int = int(health3, 16)
    page_number_int = int(page_number, 16)
    card_temp_int = int(card_temp, 16)
    well_number_int = int(well_number_raw, 16)
    taos_r_int = int(taos_r, 16)
    taos_g_int = int(taos_g, 16)
    taos_b_int = int(taos_b, 16)

    # Determine data type
    data_type = (well_number_int % 4) + 1

    # Decode solar panel data
    solar_panel = decode_solar_panel(solar_i_int, solar_t_int, data_type)

    # Decode type-specific data
    if data_type == 1:
        type_data = decode_type1(health0, health1_int, health2_int, health3_int)
    elif data_type == 2:
        type_data = decode_type2(health0, health1_int, health2_int, health3_int)
    elif data_type == 3:
        type_data = decode_type3(health0, health1_int, health2_int, health3_int)
    else:  # data_type == 4
        type_data = decode_type4(health0, health1_int, health2_int, health3_int)

    # Calculate median card temperature
    median_card_temp_c = card_temp_int / 100.0

    return DecodedBeacon(
        raw_packet=packet,
        bus_time_seconds=bus_time_seconds,
        solar_panel=solar_panel,
        data_type=data_type,
        type_specific_data=type_data,
        payload_page_number=page_number_int,
        median_card_temp_c=round(median_card_temp_c, 2),
        well_number=well_number_int,
        taos_r_hz=taos_r_int,
        taos_g_hz=taos_g_int,
        taos_b_hz=taos_b_int
    )


# Sample beacon packets for testing
SAMPLE_BEACONS = [
    "EcAMSat.org   1DEA21020033021EBA02A80200004400F90830A23661515F5B",
    "EcAMSat.org   1DEA210000F10101000007000A004400F9080DA236BC4DB84F",
    "EcAMSat.org   D900220000C6010F5B00A2014F005100B3082ACC3C674A5F5B",
    "EcAMSat.org   06DD22000004011E3902A2020100CE006F0610E1357D42E462",
    "EcAMSat.org   7EDD22010099000100000B000800CE00690619D336EF43674A",
]
