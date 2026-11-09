"""Inspect the selected legacy stage JSON without importing robot services."""
import hashlib
import json
import math
from pathlib import Path

MAX_FILE_BYTES = 10 * 1024 * 1024


def _finite_number(value):
    try:
        return type(value) in (int, float) and math.isfinite(value)
    except OverflowError:
        return False


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key: ' + key)
        result[key] = value
    return result


def inspect_action(path, dof, max_abs_rad=None):
    if type(dof) is not int or dof not in (23, 29):
        raise ValueError('Choose an explicit 23 or 29 DOF device contract')
    if max_abs_rad is not None and (not _finite_number(max_abs_rad) or max_abs_rad <= 0):
        raise ValueError('max_abs_rad must be positive and finite')
    path = Path(path)
    with path.open('rb') as stream:
        raw = stream.read(MAX_FILE_BYTES + 1)
    if len(raw) > MAX_FILE_BYTES:
        raise ValueError('Action JSON exceeds 10 MiB')
    stages = json.loads(raw.decode('utf-8-sig'), object_pairs_hook=_unique_object)
    if not isinstance(stages, list) or not 1 <= len(stages) <= 10000:
        raise ValueError('Action must contain 1 to 10000 stage objects')
    total = 0.0
    maximum = 0.0
    conversions = {'unchanged': 0, '18_to_12': 0, '12_to_18': 0}
    widths = set()
    for index, stage in enumerate(stages, 1):
        if not isinstance(stage, dict) or not isinstance(stage.get('data'), list):
            raise ValueError(f'Stage {index}: expected an object with a data list')
        data = stage['data']
        if len(data) not in (12, 18):
            raise ValueError(f'Stage {index}: data must contain duration plus 11 or 17 targets')
        if any(not _finite_number(v) for v in data):
            raise ValueError(f'Stage {index}: all data must be finite JSON numbers, not booleans or strings')
        if data[0] <= 0:
            raise ValueError(f'Stage {index}: duration must be positive')
        total += data[0]
        if not math.isfinite(total):
            raise ValueError('Total duration is not finite')
        widths.add(len(data))
        maximum = max(maximum, max(abs(v) for v in data[1:]))
        # Check even targets dropped by a legacy conversion so data is not silently hidden.
        if max_abs_rad is not None and any(abs(v) > max_abs_rad for v in data[1:]):
            raise ValueError(f'Stage {index}: exceeds the caller-supplied review bound')
        conversion = '18_to_12' if dof == 23 and len(data) == 18 else (
            '12_to_18' if dof == 29 and len(data) == 12 else 'unchanged')
        conversions[conversion] += 1
    return {'schema': 'app-udp/stages-json', 'file': path.name, 'sha256': hashlib.sha256(raw).hexdigest(),
            'bytes': len(raw), 'stages': len(stages), 'dof': dof, 'input_widths': sorted(widths),
            'target_count': 11 if dof == 23 else 17, 'total_duration_s': total,
            'max_abs_target_rad': maximum, 'review_bound_rad': max_abs_rad,
            'legacy_conversions': conversions, 'schema_valid': True,
            'motion_validated': False, 'executed': False,
            'limits': 'Static shape/numeric checks only; joint order, firmware, collision and stop behavior require device evidence'}
