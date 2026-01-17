"""
EcAMSat Beacon Decoder API

A FastAPI application for decoding EcAMSat satellite beacon packets.

Originally written by Aaron Cohen on 11/20/2017
API rewrite by Claude
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from .decoder import (
    decode_beacon,
    BeaconDecodeError,
    SAMPLE_BEACONS,
    DataType1,
    DataType2,
    DataType3,
    DataType4,
)
from .models import (
    DecodeRequest,
    DecodeResponse,
    ErrorResponse,
    SolarPanelResponse,
    DataType1Response,
    DataType2Response,
    DataType3Response,
    DataType4Response,
    LightSensorResponse,
    SamplesResponse,
    SamplePacket,
    HealthResponse,
)

__version__ = "2.0.0"

app = FastAPI(
    title="EcAMSat Beacon Decoder API",
    description="""
    A web API for decoding EcAMSat satellite beacon packets.

    ## About EcAMSat

    EcAMSat (E. coli AntiMicrobial Satellite) was a NASA CubeSat mission launched in 2017
    to study the effects of microgravity on antibiotic resistance in E. coli bacteria.

    ## Beacon Format

    Beacon packets are 64 characters long and contain telemetry data including:
    - Solar panel current and temperature
    - Battery and bus voltages
    - Payload temperatures
    - Light sensor readings
    - And more...

    ## Data Types

    Packets are categorized into 4 data types based on the well number:
    - **Type 1**: Power and Temperature Data
    - **Type 2**: Startup and Radiation Data
    - **Type 3**: Communication and Sensor Data
    - **Type 4**: Experiment and Bus Data

    ## Credits

    Based on decoding information from:
    http://ecamsat.engr.scu.edu/beacon/EcAMSatBeaconDecoding.pdf
    """,
    version=__version__,
    contact={
        "name": "EcAMSat Project",
        "url": "http://ecamsat.engr.scu.edu/",
    },
    license_info={
        "name": "MIT License",
    },
)

# Add CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"


def convert_type_data(data_type: int, type_data):
    """Convert decoder dataclass to response model"""
    if data_type == 1 and isinstance(type_data, DataType1):
        return DataType1Response(
            power_port_status=type_data.power_port_status,
            payload_board_temp_c=type_data.payload_board_temp_c,
            battery_voltage_v=type_data.battery_voltage_v,
            payload_heater_current_ma=type_data.payload_heater_current_ma,
        )
    elif data_type == 2 and isinstance(type_data, DataType2):
        return DataType2Response(
            startup_counter=type_data.startup_counter,
            radiation_counts_per_30s=type_data.radiation_counts_per_30s,
            comm_voltage_v=type_data.comm_voltage_v,
            payload_current_ma=type_data.payload_current_ma,
        )
    elif data_type == 3 and isinstance(type_data, DataType3):
        return DataType3Response(
            spacecraft_ground_id=type_data.spacecraft_ground_id,
            comm_current_ma=type_data.comm_current_ma,
            sensor_voltage_v=type_data.sensor_voltage_v,
            bus_data_page=type_data.bus_data_page,
        )
    elif data_type == 4 and isinstance(type_data, DataType4):
        return DataType4Response(
            experiment_phase=type_data.experiment_phase,
            comm_voltage_v=type_data.comm_voltage_v,
            bus_voltage_v=type_data.bus_voltage_v,
            register_file_wrap_count=type_data.register_file_wrap_count,
        )
    raise ValueError(f"Unknown data type: {data_type}")


@app.get("/", include_in_schema=False)
async def serve_frontend():
    """Serve the frontend HTML"""
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version=__version__,
    )


@app.post(
    "/api/decode",
    response_model=DecodeResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid beacon packet"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    tags=["Decoder"],
    summary="Decode a beacon packet",
    description="Decodes a 64-character EcAMSat beacon packet and returns telemetry data.",
)
async def decode_packet(request: DecodeRequest):
    """
    Decode an EcAMSat beacon packet.

    The packet must be exactly 64 characters and start with 'EcAMSat.org   '.
    """
    try:
        decoded = decode_beacon(request.packet)

        return DecodeResponse(
            success=True,
            raw_packet=decoded.raw_packet,
            bus_time_seconds=decoded.bus_time_seconds,
            solar_panel=SolarPanelResponse(
                panel_number=decoded.solar_panel.panel_number,
                current_ma=decoded.solar_panel.current_ma,
                temperature_c=decoded.solar_panel.temperature_c,
            ),
            data_type=decoded.data_type,
            type_specific_data=convert_type_data(
                decoded.data_type,
                decoded.type_specific_data
            ),
            payload_page_number=decoded.payload_page_number,
            median_card_temp_c=decoded.median_card_temp_c,
            well_number=decoded.well_number,
            light_sensors=LightSensorResponse(
                red_hz=decoded.taos_r_hz,
                green_hz=decoded.taos_g_hz,
                blue_hz=decoded.taos_b_hz,
            ),
        )
    except BeaconDecodeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Decoding error: {str(e)}")


@app.get(
    "/api/samples",
    response_model=SamplesResponse,
    tags=["Decoder"],
    summary="Get sample beacon packets",
    description="Returns a list of sample beacon packets for testing.",
)
async def get_samples():
    """Get sample beacon packets for testing"""
    descriptions = [
        "Sample from JA0CAW station - Data Type 3",
        "Sample from JA0CAW station - Data Type 2",
        "Sample from JA1GDE station - Data Type 4",
        "Sample from DK3WN station - Data Type 2",
        "Sample from DK3WN station - Data Type 2",
    ]

    return SamplesResponse(
        samples=[
            SamplePacket(packet=packet, description=desc)
            for packet, desc in zip(SAMPLE_BEACONS, descriptions)
        ]
    )


# Mount static files (CSS, JS)
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR / "static"), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
