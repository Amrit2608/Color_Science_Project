from DMXEnttecPro.utils import get_port_by_serial_number, get_port_by_product_id
from DMXEnttecPro import Controller
import numpy as np
import time
from matplotlib import pyplot as plt
import datetime
import os


class DMX_Handler():
    def __init__(self, port=None):
        self.port = get_port_by_serial_number('EN279626')
        # my_port = get_port_by_product_id(24577)

    def open(self):
        self.dmx = Controller(self.port, dmx_size=256)

    def set_channel_values(self, R, G, B, W, O, UV):
        dmx.set_channel(channel, v)

    def render(self):
        dmx.submit()  # Sends the update to the controller

    def close(self):
        pass


dmx = None
# my_port = get_port_by_serial_number('EN279626')

channels = [1, 2, 3, 4]
output_values = np.arange(0, 257, 8)

output_values[-1] = 255
print(output_values)


def measure_spectra_jeti():
    return 0


now = datetime.datetime.now()
filename = './output/log_' + now.strftime('%Y%m%d_%H%M%S')
if not os.path.exists(os.path.dirname(filename)):
    os.mkdir(os.path.dirname(filename))


results = []
for channel in channels:
    measured_spectra = []
    for v in output_values:
        if dmx is not None:
            dmx.set_channel(channel, v)
            dmx.submit()  # Sends the update to the controller
        time.sleep(0.01)
        data = measure_spectra_jeti()
        measured_spectra.append(data)
    results.append(measured_spectra)

fig = plt.figure()
for result in results:
    plt.plot(output_values, result, '.')
plt.show()
