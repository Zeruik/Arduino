"""Package validation shared by import and the last check before invoking esptool."""
import hashlib
from pathlib import Path

LAYOUTS = {
    'N16R8': {'bootloader.bin': (0, 0x8000), 'partitions.bin': (0x8000, 0x1000),
              'firmware.bin': (0x10000, 0x1f0000), 'model.bin': (0x200000, 0xd80000),
              'tokenizer.bin': (0xf80000, 0x80000)},
    'N32R16': {'bootloader.bin': (0, 0x8000), 'partitions.bin': (0x8000, 0x1000),
               'firmware.bin': (0x10000, 0x100000), 'model.bin': (0x110000, 0xef0000),
               'tokenizer.bin': (0x1000000, 0x80000)},
}

def validate_package(base, manifest, expected_profile=None):
    profile = manifest.get('profile')
    if profile not in LAYOUTS:
        raise ValueError('未知交付包型号')
    if expected_profile is not None and profile != expected_profile:
        raise ValueError('所选型号与交付包不一致')
    base = Path(base).resolve()
    layout = LAYOUTS[profile]
    seen = set()
    for f in manifest['files']:
        name = f['name']
        if not isinstance(name, str) or name in ('', '.', '..') or '/' in name or '\\' in name:
            raise ValueError('交付包文件名无效')
        if name in seen:
            raise ValueError('交付包包含重复文件')
        seen.add(name)
        path = (base/name).resolve()
        if not path.is_relative_to(base):
            raise ValueError('交付包路径越界')
        if name in layout:
            offset, limit = layout[name]
            if type(f.get('offset')) is not int or f['offset'] != offset:
                raise ValueError('交付包分区偏移错误：'+name)
            size = path.stat().st_size
            if size < 1 or size > limit or f.get('size') != size:
                raise ValueError('交付包文件大小错误：'+name)
        elif 'offset' in f:
            raise ValueError('非固件文件包含烧录地址')
        with path.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        if digest != f['sha256']:
            raise ValueError('文件校验失败：'+name)
    if not set(layout).issubset(seen):
        raise ValueError('缺少必要的固件或模型文件')
    return profile
