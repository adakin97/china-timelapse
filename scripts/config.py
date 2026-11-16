"""Shared settings: the map window and the picture grid every yearly image uses."""
import math

LON_W, LON_E = 73.0, 136.0
LAT_S, LAT_N = 15.0, 54.5
WIDTH = 4096                      # pixels across; 4096 is the largest picture every phone can draw
R = 6378137.0


def merc_x(lon): return R * math.radians(lon)
def merc_y(lat): return R * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


X0, X1 = merc_x(LON_W), merc_x(LON_E)
Y0, Y1 = merc_y(LAT_S), merc_y(LAT_N)
PX = (X1 - X0) / WIDTH            # metres per pixel in Web Mercator
HEIGHT = int(round((Y1 - Y0) / PX))
FIRST_YEAR, LAST_YEAR = 1992, 2021
EE_PROJECT = "damage-map"
