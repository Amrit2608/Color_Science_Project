from DMXEnttecPro import Controller
from DMXEnttecPro.utils import get_port_by_serial_number, get_port_by_product_id
import numpy as np
import time
from matplotlib import pyplot as plt
import datetime
import os
import luxpy as lx  # package for color science calculations
from luxpy.toolboxes import spectro as sp
import glob
from luxpy.toolboxes import spdbuild as spb

cieobs = '1964_10'


class DMXHandler():
    def __init__(self, product_id) -> None:
        self.product_id = product_id
        self.dmx = None
        self.is_connected = False

    def open(self):
        try:
            port = get_port_by_product_id(self.product_id)
            self.dmx = Controller(port)
            print('DMX connected')
            self.is_connected = True
        except:
            self.dmx = None
            print('no DMX connection')
            self.is_connected = False

    def control_channels(self, dr_value_in, channels_idx=[0, 1, 2, 3, 4]):
        # example:  turn on R 100, B 10
        # dmx.control_channels(dr_value_in=[100, 10], channels_idx=[0, 1])
        if len(channels_idx) != len(dr_value_in):
            print('Both input variables should have same length.')

        for (c, v) in zip(channels_idx):
            self.dmx.set_channel(c+1, int(v))
        self.dmx.submit()

    def close(self):
        if self.is_connected:
            dmx.set_channel(1, 0)
            dmx.submit()
            self.dmx.close()


dmx = DMXHandler(24577)

dmx.open()
sp.init('jeti')


if dmx.is_connected:
    sp.jeti.set_laser(laser_on=True)
    dmx.control_channels(dr_value_in=[0, 0, 0, 0, 0])
    time.sleep(2)
    sp.jeti.set_laser(laser_on=False)


def measureSPD(channels_idx, driver_values):
    if not dmx.is_connected:
        return None
    # Avoid to measure with 0 output value because JETI can't be used in a dark room.
    if np.sum(driver_values) == 0:
        return None
    dmx.control_channels(dr_value_in=driver_values, channels_idx=channels_idx)
    time.sleep(0.2)
    spd = sp.jeti.get_spd()
    return spd


def measureSPDforCalibration(channels_idx, dr_value_in):
    measured_spd_all = []
    for channel in channels_idx:
        measured_spd = []
        for v in dr_value_in:
            print(channel, v)
            spd = measureSPD(dr_value_in=[v], channels_idx=[channel])
            measured_spd.append(spd)

            #  fill None data as zero spectrum
            if measured_spd[0] is None:
                measured_spd[0] = measured_spd[1].copy()
                measured_spd[0][-1] = measured_spd[0][-1]*0

        first_spd = measured_spd[0].copy()
        after_first_spd_intensity = measured_spd[1:, 1, :].copy()
        spd_channel = np.concatenate(
            [first_spd, after_first_spd_intensity], axis=0)
        measured_spd_all.append(spd_channel)

    return measured_spd_all


def calibrate(filename=None):
    # try to load existing calibration data when filename is specified.
    if filename is not None:
        return np.load(filename)

    if not dmx.is_connected:
        print('Connect DMX controller to run calibration.')
        return False

    now = datetime.datetime.now()
    filename = './output/data_' + now.strftime('%Y%m%d_%H%M%S')
    if not os.path.exists(os.path.dirname(filename)):
        os.mkdir(os.path.dirname(filename))

    channels = [0, 1, 2, 3, 4]
    dr_value_in = np.concatenate([np.arange(0, 50, 5), np.arange(50, 255, 10)])
    if dr_value_in[-1] < 255:  # make sure the last output is max.
        dr_value_in = np.append(dr_value_in, 255)

    measured_spd_all = measureSPDforCalibration(channels, dr_value_in)
    np.savez(filename, spd=measured_spd_all,
             dr_value_in=dr_value_in, channels=channels)
    return np.load(filename+'.npz')


luminance = lx.spd_to_power(
    measured_spd_all[i], ptype='pu', cieobs=cieobs)[:, 0]
# luminance = luminance - luminance[0]
normalized_luminance = (luminance-min(luminance)) / \
    (max(luminance)-min(luminance))
# normalized_luminance = luminance / max(luminance)

z = np.polyfit(luminance, dr_value_in, 6)
z_norm = np.polyfit(normalized_luminance, dr_value_in, 6)

func = np.poly1d(z)
func_norm = np.poly1d(z_norm)
