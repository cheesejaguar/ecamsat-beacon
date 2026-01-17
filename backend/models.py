"""
Pydantic models for API request/response validation
"""

from pydantic import BaseModel, Field
from typing import Union


class DecodeRequest(BaseModel):
    """Request model for beacon decoding"""
    packet: str = Field(
        ...,
        description="64-character EcAMSat beacon packet",
        min_length=1,
        max_length=200,
        examples=["EcAMSat.org   1DEA21020033021EBA02A80200004400F90830A23661515F5B"]
    )


class SolarPanelResponse(BaseModel):
    """Solar panel telemetry data"""
    panel_number: int = Field(..., description="Solar panel number (1-4)")
    current_ma: float = Field(..., description="Current in milliamps")
    temperature_c: float = Field(..., description="Temperature in Celsius")


class DataType1Response(BaseModel):
    """Data Type 1: Power and Temperature Data"""
    type_name: str = "Power and Temperature"
    power_port_status: str = Field(..., description="Binary power port status")
    payload_board_temp_c: float = Field(..., description="Payload board temperature in Celsius")
    battery_voltage_v: float = Field(..., description="Battery voltage in Volts")
    payload_heater_current_ma: float = Field(..., description="Payload heater current in mA")


class DataType2Response(BaseModel):
    """Data Type 2: Startup and Radiation Data"""
    type_name: str = "Startup and Radiation"
    startup_counter: int = Field(..., description="Spacecraft startup counter")
    radiation_counts_per_30s: int = Field(..., description="Radiation counts per 30 seconds")
    comm_voltage_v: float = Field(..., description="Communication voltage in Volts")
    payload_current_ma: float = Field(..., description="Payload current in mA")


class DataType3Response(BaseModel):
    """Data Type 3: Communication and Sensor Data"""
    type_name: str = "Communication and Sensor"
    spacecraft_ground_id: int = Field(..., description="Spacecraft to ground ID")
    comm_current_ma: float = Field(..., description="Communication current in mA")
    sensor_voltage_v: float = Field(..., description="Sensor voltage in Volts")
    bus_data_page: int = Field(..., description="Bus data page number")


class DataType4Response(BaseModel):
    """Data Type 4: Experiment and Bus Data"""
    type_name: str = "Experiment and Bus"
    experiment_phase: str = Field(..., description="Binary experiment phase")
    comm_voltage_v: float = Field(..., description="Communication voltage in Volts")
    bus_voltage_v: float = Field(..., description="Bus voltage in Volts")
    register_file_wrap_count: int = Field(..., description="Register file wrap count")


class LightSensorResponse(BaseModel):
    """TAOS light sensor readings"""
    red_hz: int = Field(..., description="Red light sensor frequency in Hz")
    green_hz: int = Field(..., description="Green light sensor frequency in Hz")
    blue_hz: int = Field(..., description="Blue light sensor frequency in Hz")


class DecodeResponse(BaseModel):
    """Complete decoded beacon response"""
    success: bool = Field(..., description="Whether decoding was successful")
    raw_packet: str = Field(..., description="Original packet string")
    bus_time_seconds: int = Field(..., description="Bus time in seconds")
    solar_panel: SolarPanelResponse = Field(..., description="Solar panel data")
    data_type: int = Field(..., description="Data type (1-4)")
    type_specific_data: Union[
        DataType1Response,
        DataType2Response,
        DataType3Response,
        DataType4Response
    ] = Field(..., description="Type-specific telemetry data")
    payload_page_number: int = Field(..., description="Payload page number")
    median_card_temp_c: float = Field(..., description="Median card temperature in Celsius")
    well_number: int = Field(..., description="Well number")
    light_sensors: LightSensorResponse = Field(..., description="TAOS light sensor readings")


class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    error: str = Field(..., description="Error message")
    details: str = Field(None, description="Additional error details")


class SamplePacket(BaseModel):
    """Sample beacon packet"""
    packet: str
    description: str


class SamplesResponse(BaseModel):
    """Response containing sample packets"""
    samples: list[SamplePacket]


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = "healthy"
    version: str
    service: str = "EcAMSat Beacon Decoder API"
