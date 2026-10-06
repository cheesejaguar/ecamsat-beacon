/**
 * EcAMSat beacon decoder — JavaScript port of backend/decoder.py, which is
 * itself the 2017 beacon.py by Aaron Cohen, based on the SCU decoding guide:
 * http://ecamsat.engr.scu.edu/beacon/EcAMSatBeaconDecoding.pdf
 *
 * Pure functions only: imported by site/index.html and by tests/*.test.mjs,
 * which check every result against the Python decoder's golden output.
 */

export const HEADER = 'EcAMSat.org   ';
export const PACKET_LENGTH = 64;

/**
 * Packet layout. `len` is in hex characters; little-endian fields have their
 * byte pairs reversed before parsing (ABCD → CDAB, ABCDEF → EFCDAB).
 */
export const FIELDS = [
  { key: 'header',    label: 'Header',        start: 0,  len: 14, le: false },
  { key: 'busTime',   label: 'Bus time',      start: 14, len: 6,  le: true  },
  { key: 'solarI',    label: 'Solar current', start: 20, len: 4,  le: true  },
  { key: 'solarT',    label: 'Solar temp',    start: 24, len: 4,  le: true  },
  { key: 'health0',   label: 'Health 0',      start: 28, len: 2,  le: false },
  { key: 'health1',   label: 'Health 1',      start: 30, len: 4,  le: true  },
  { key: 'health2',   label: 'Health 2',      start: 34, len: 4,  le: true  },
  { key: 'health3',   label: 'Health 3',      start: 38, len: 4,  le: true  },
  { key: 'page',      label: 'Page',          start: 42, len: 4,  le: true  },
  { key: 'cardTemp',  label: 'Card temp',     start: 46, len: 4,  le: true  },
  { key: 'well',      label: 'Well',          start: 50, len: 2,  le: false },
  { key: 'taosR',     label: 'TAOS red',      start: 52, len: 4,  le: true  },
  { key: 'taosG',     label: 'TAOS green',    start: 56, len: 4,  le: true  },
  { key: 'taosB',     label: 'TAOS blue',     start: 60, len: 4,  le: true  },
];

/** Per-panel calibration: [current mult, current offset, temp mult, temp offset]. */
export const SOLAR_CALIBRATION = {
  1: [1.8678, 3.41, 0.0557, -15.37],
  2: [0.9542, -1.07, 0.0563, -15.85],
  3: [1.8785, -0.41, 0.0559, -14.56],
  4: [0.9562, -1.04, 0.0560, -15.75],
};

export const TYPE_NAMES = {
  1: 'Power and Temperature',
  2: 'Startup and Radiation',
  3: 'Communication and Sensor',
  4: 'Experiment and Bus',
};

export class BeaconDecodeError extends Error {}

/** Python's round(x, n) for the values we see (non-tie cases match exactly). */
const round = (x, n) => Number(x.toFixed(n));
/** Python's bin(n). */
const bin = (n) => '0b' + n.toString(2);
const hex = (s) => parseInt(s, 16);

/** Little-endian hex string → big-endian. `length` is in hex characters. */
export function reverseEndian(byteStr, length) {
  if (length === 2) return byteStr;
  if (length === 4) return byteStr.slice(2, 4) + byteStr.slice(0, 2);
  if (length === 6) return byteStr.slice(4, 6) + byteStr.slice(2, 4) + byteStr.slice(0, 2);
  throw new RangeError(`Unsupported length: ${length}`);
}

/** @returns {[boolean, string]} */
export function validatePacket(packet) {
  if (packet.length !== PACKET_LENGTH) {
    return [false, `Beacon packet must be exactly 64 characters (got ${packet.length})`];
  }
  if (packet.slice(0, 14) !== HEADER) {
    return [false, `Invalid header. Expected '${HEADER}', got '${packet.slice(0, 14)}'`];
  }
  if (!/^[0-9a-fA-F]+$/.test(packet.slice(14))) {
    return [false, 'Packet contains invalid hexadecimal characters'];
  }
  return [true, ''];
}

export function decodeSolarPanel(solarIRaw, solarTRaw, dataType) {
  const [iMult, iOffset, tMult, tOffset] = SOLAR_CALIBRATION[dataType];
  return {
    panel_number: dataType,
    current_ma: round(solarIRaw * iMult + iOffset, 4),
    temperature_c: round(solarTRaw * tMult + tOffset, 4),
  };
}

const TYPE_DECODERS = {
  1: (h0, h1, h2, h3) => ({
    power_port_status: bin(hex(h0)),
    payload_board_temp_c: round(h1 * 0.0554 - 15.75, 4),
    battery_voltage_v: round(h2 * 0.0119 - 0.05, 4),
    payload_heater_current_ma: round(h3 * 3.2922 + 8.04, 4),
  }),
  2: (h0, h1, h2, h3) => ({
    startup_counter: hex(h0),
    radiation_counts_per_30s: h1,
    comm_voltage_v: round(h2 * 0.0119 + 0.01, 4),
    payload_current_ma: round(h3 * 3.4281 - 22.69, 4),
  }),
  3: (h0, h1, h2, h3) => ({
    spacecraft_ground_id: hex(h0),
    comm_current_ma: round(h1 * 4.3330 + 16.27, 4),
    sensor_voltage_v: round(h2 * 0.0130 - 0.48, 4),
    bus_data_page: h3,
  }),
  4: (h0, h1, h2, h3) => ({
    experiment_phase: bin(hex(h0)),
    comm_voltage_v: round(h1 * 0.0119 + 0.01, 4),
    bus_voltage_v: round(h2 * 0.0059, 4),
    register_file_wrap_count: h3,
  }),
};

/**
 * Split a packet into its fields, showing each step the decoder takes.
 * Used by the decoder bench to animate the byte swaps.
 */
export function sliceFields(packet) {
  return FIELDS.map((f) => {
    const raw = packet.slice(f.start, f.start + f.len);
    const swapped = f.le ? reverseEndian(raw, f.len) : raw;
    return { ...f, raw, swapped, value: f.key === 'header' ? null : hex(swapped) };
  });
}

/** Decode a beacon packet. Output keys match backend/decoder.py's DecodedBeacon. */
export function decodeBeacon(input) {
  const packet = input.trim();
  const [ok, error] = validatePacket(packet);
  if (!ok) throw new BeaconDecodeError(error);

  const f = Object.fromEntries(sliceFields(packet).map((x) => [x.key, x]));
  const dataType = (f.well.value % 4) + 1;

  return {
    raw_packet: packet,
    bus_time_seconds: f.busTime.value,
    solar_panel: decodeSolarPanel(f.solarI.value, f.solarT.value, dataType),
    data_type: dataType,
    type_specific_data: TYPE_DECODERS[dataType](
      f.health0.raw, f.health1.value, f.health2.value, f.health3.value,
    ),
    payload_page_number: f.page.value,
    median_card_temp_c: round(f.cardTemp.value / 100, 2),
    well_number: f.well.value,
    taos_r_hz: f.taosR.value,
    taos_g_hz: f.taosG.value,
    taos_b_hz: f.taosB.value,
  };
}

/**
 * Sanity checks the 2017 script never had. Returns human-readable warnings for
 * values a healthy spacecraft couldn't report — usually a corrupted packet.
 */
export function plausibilityWarnings(d) {
  const w = [];
  if (d.median_card_temp_c > 80) w.push(`Card temperature ${d.median_card_temp_c} °C — the card was held near 37 °C`);
  if (d.payload_page_number > 4095) w.push(`Payload page ${d.payload_page_number} is far beyond the data recorded`);
  if (d.solar_panel.current_ma > 3000) w.push(`Solar panel ${d.solar_panel.panel_number} current ${d.solar_panel.current_ma} mA is far more than one panel can make`);
  if (d.solar_panel.temperature_c > 150 || d.solar_panel.temperature_c < -80) {
    w.push(`Solar panel temperature ${d.solar_panel.temperature_c} °C is outside physical limits`);
  }
  if (d.bus_time_seconds > 5 * 365 * 86400) w.push('Bus time is later than the spacecraft existed');
  if (d.well_number >= WELL_COUNT) w.push(`Well ${d.well_number} does not exist on a ${WELL_COUNT}-well card`);
  return w;
}

/**
 * The fluidic card's wells are addressed 0–59: five rows of 12. NASA describes
 * 48 wells in 4 dose banks, and one slide mentions "all 60 wells"; the ham
 * packets report wells up to 54, so the beacon addresses all five rows.
 */
export const WELL_COUNT = 60;
export const WELLS_PER_ROW = 12;

/** Well number → row (0–4) and slot (0–11). */
export function wellPosition(well) {
  return { row: Math.floor(well / WELLS_PER_ROW), slot: well % WELLS_PER_ROW };
}

/**
 * Bus time origin, approximately 2017-10-25 16:00 UTC (the NanoRacks integration day).
 * Derived, not documented: the bus telemetry was saved 2017-12-08 06:11 UTC and
 * its newest sample is at bus day 43.5, while the first in-orbit sample (day
 * 25.64) and every ham packet (days 25.7–26.5) must fall after deployment on
 * 2017-11-20. Treat dates computed from it as good to a few hours.
 */
export const BUS_EPOCH_MS = Date.UTC(2017, 9, 25, 16);
export const busTimeToDate = (s) => new Date(BUS_EPOCH_MS + s * 1000);
