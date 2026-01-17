# EcAMSat Beacon Decoder

A web application for decoding telemetry data from NASA's EcAMSat (E. coli AntiMicrobial Satellite) beacon packets.

## About EcAMSat

EcAMSat was a NASA CubeSat mission launched in 2017 to study the effects of microgravity on antibiotic resistance in E. coli bacteria. The satellite transmitted beacon packets containing telemetry data that amateur radio operators could receive and decode.

## Features

- **FastAPI Backend**: Modern, high-performance Python API for beacon decoding
- **Beautiful Web Interface**: Space-themed UI for pasting and decoding beacon packets
- **Complete Telemetry**: Decodes all 4 data types with calibrated sensor values
- **Sample Packets**: Built-in sample packets for testing
- **API Documentation**: Auto-generated OpenAPI/Swagger docs
- **100% Test Coverage**: Comprehensive test suite with full coverage

## Quick Start

### Prerequisites

- Python 3.10 or higher
- [UV](https://docs.astral.sh/uv/) (recommended) or pip

### Installation with UV (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ecamsat-beacon.git
   cd ecamsat-beacon
   ```

2. Install dependencies with UV:
   ```bash
   uv sync
   ```

### Installation with pip (Alternative)

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ecamsat-beacon.git
   cd ecamsat-beacon
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -e .
   ```

### Running the Application

With UV:
```bash
uv run python run.py
```

With pip/venv:
```bash
python run.py
```

With development mode (auto-reload):
```bash
uv run python run.py --reload
```

Then open your browser to:
- **Web Interface**: http://127.0.0.1:8000
- **API Documentation**: http://127.0.0.1:8000/docs

## Testing

Run the test suite with coverage:

```bash
uv run pytest
```

This will run all tests and display a coverage report. The project maintains 100% test coverage.

To run tests without coverage:
```bash
uv run pytest --no-cov
```

## Usage

### Web Interface

1. Open the web interface at http://127.0.0.1:8000
2. Paste a 64-character beacon packet into the text area
3. Click "Decode Packet" or press Enter
4. View the decoded telemetry data

You can also click "Load Sample" to try a pre-loaded beacon packet.

### API

Send a POST request to `/api/decode`:

```bash
curl -X POST "http://127.0.0.1:8000/api/decode" \
  -H "Content-Type: application/json" \
  -d '{"packet": "EcAMSat.org   1DEA21020033021EBA02A80200004400F90830A23661515F5B"}'
```

### Beacon Packet Format

Beacon packets are exactly 64 characters:
- Characters 0-13: Header (`EcAMSat.org   `)
- Characters 14-63: Hexadecimal telemetry data

Example:
```
EcAMSat.org   1DEA21020033021EBA02A80200004400F90830A23661515F5B
```

## Decoded Data

### Common Fields (All Data Types)
- **Bus Time**: Mission elapsed time in seconds
- **Solar Panel Current**: Panel current in mA
- **Solar Panel Temperature**: Panel temperature in °C
- **Payload Page Number**: Current payload page
- **Median Card Temperature**: Card temperature in °C
- **Well Number**: Experiment well number
- **TAOS Light Sensors**: Red, Green, Blue frequencies in Hz

### Data Type-Specific Fields

#### Type 1: Power and Temperature
- Bus Power Port Status
- Payload Board Temperature
- Battery Voltage
- Payload Heater Current

#### Type 2: Startup and Radiation
- Spacecraft Startup Counter
- Radiation Counts (per 30 seconds)
- Comm Voltage
- Payload Current

#### Type 3: Communication and Sensor
- Spacecraft to Ground ID
- Comm Current
- Sensor Voltage
- Bus Data Page

#### Type 4: Experiment and Bus
- Experiment Phase
- Comm Voltage
- Bus Voltage
- Register File Wrap Count

## Project Structure

```
ecamsat-beacon/
├── backend/
│   ├── __init__.py
│   ├── main.py          # FastAPI application
│   ├── decoder.py       # Beacon decoding logic
│   └── models.py        # Pydantic models
├── frontend/
│   ├── index.html       # Web interface
│   └── static/
│       ├── css/
│       │   └── style.css
│       └── js/
│           └── app.js
├── tests/
│   ├── test_decoder.py  # Decoder unit tests
│   ├── test_api.py      # API endpoint tests
│   └── test_models.py   # Pydantic model tests
├── beacons/
│   └── beacon.txt.txt   # Sample beacon packets
├── beacon.py            # Original CLI decoder (legacy)
├── pyproject.toml       # Project configuration
├── run.py               # Server startup script
└── README.md
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Serve web interface |
| `/api/decode` | POST | Decode a beacon packet |
| `/api/samples` | GET | Get sample beacon packets |
| `/health` | GET | Health check endpoint |
| `/docs` | GET | OpenAPI documentation |

## Development

### Adding Dependencies

```bash
uv add <package>           # Add runtime dependency
uv add --dev <package>     # Add development dependency
```

### Running Linters

```bash
uv run ruff check .        # Run linter
uv run ruff format .       # Format code
```

## Credits

- **Original Decoder**: Aaron Cohen (2017)
- **API Rewrite**: Claude
- **Decoding Specification**: [EcAMSat Beacon Decoding PDF](http://ecamsat.engr.scu.edu/beacon/EcAMSatBeaconDecoding.pdf)

## License

MIT License - see [LICENSE](LICENSE) file for details.
