// The JS decoder must match the Python decoder (backend/decoder.py) exactly.
// Regenerate the golden file with: python3 tools/build_data.py
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import {
  decodeBeacon, reverseEndian, validatePacket, plausibilityWarnings, BeaconDecodeError,
} from '../site/decoder.js';

const golden = JSON.parse(readFileSync(new URL('./golden_decode.json', import.meta.url)));

test('matches the Python decoder on all 32 ham-received packets', () => {
  assert.equal(golden.length, 32);
  for (const { packet, decoded } of golden) {
    assert.deepEqual(decodeBeacon(packet), decoded, packet);
  }
});

test('covers every data type', () => {
  const types = new Set(golden.map((g) => g.decoded.data_type));
  assert.deepEqual([...types].sort(), [1, 2, 3, 4]);
});

test('accepts lowercase hex (one JA0CAW packet has it)', () => {
  const lower = golden.find((g) => /[a-f]/.test(g.packet.slice(14)));
  assert.ok(lower);
  assert.equal(decodeBeacon(lower.packet).raw_packet, lower.packet);
});

test('reverseEndian swaps byte pairs', () => {
  assert.equal(reverseEndian('AB', 2), 'AB');
  assert.equal(reverseEndian('ABCD', 4), 'CDAB');
  assert.equal(reverseEndian('ABCDEF', 6), 'EFCDAB');
  assert.throws(() => reverseEndian('ABCDEFGH', 8), RangeError);
});

test('rejects malformed packets', () => {
  const good = golden[0].packet;
  assert.equal(validatePacket(good)[0], true);
  assert.match(validatePacket(good.slice(0, 63))[1], /exactly 64/);
  assert.match(validatePacket('X' + good.slice(1))[1], /Invalid header/);
  assert.match(validatePacket(good.slice(0, 63) + 'Z')[1], /hexadecimal/);
  assert.throws(() => decodeBeacon('nope'), BeaconDecodeError);
});

test('flags the corrupted JA1GDE packet and no clean ones', () => {
  const flagged = golden.filter((g) => plausibilityWarnings(decodeBeacon(g.packet)).length);
  assert.deepEqual(flagged.map((g) => g.packet), [
    'EcAMSat.org   D909229399C5919F5B99A3914F995199B397366737D6444658',
  ]);
});
