"""Read-only BSP evidence inventory; never change drivers or permissions."""
import json, platform
from pathlib import Path

if __name__=='__main__':
    root=Path('/sys/class')
    print(json.dumps({'platform':platform.system(),'kernel':platform.release(),
                      'source':'read-only host inventory',
                      'classes':{name:sorted(p.name for p in (root/name).glob('*'))[:32]
                                 for name in ('net','tty','gpio','i2c-adapter')},
                      'device_tree_available':Path('/sys/firmware/devicetree/base').exists(),
                      'limits':'Windows empty lists are not Linux BSP evidence; no kernel build or board flashing'},indent=2))
