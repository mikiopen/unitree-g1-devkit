import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    result=importlib.util.module_from_spec(spec); spec.loader.exec_module(result); return result

serial=module('serial_lab','examples/career-labs/serial/receiver.py')
control=module('control_lab','examples/career-labs/control_sim.py')


class CareerLabsTests(unittest.TestCase):
    def test_crc_and_fragmented_uart_resynchronization(self):
        self.assertEqual(serial.crc8(b'123456789'),0xf4)
        receiver=serial.Receiver(); bad=bytearray(serial.encode(9,1023,1)); bad[-1]^=1
        stream=b'noise'+bad+serial.encode(255,65535,255)
        frames=[]
        for byte in stream: frames.extend(receiver.feed(bytes([byte])))
        self.assertEqual(frames,[{'sequence':255,'sensor':65535,'buttons':255}])

    def test_damping_reduces_overshoot_in_defined_model(self):
        _,undamped=control.simulate(kd=0); _,damped=control.simulate(kd=4)
        self.assertLess(damped['overshoot_rad'],undamped['overshoot_rad'])
        rows,_=control.simulate(); self.assertTrue(all(abs(row[3])<=5 for row in rows))


if __name__=='__main__': unittest.main()
