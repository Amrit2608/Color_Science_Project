from luxpy.toolboxes import spectro as sp
import luxpy as lx  # package for color science calculations
from matplotlib import pyplot as plt

a = sp.init('jeti')
spd = sp.jeti.get_spd()
lx.SPD(spd).plot()
plt.show()
