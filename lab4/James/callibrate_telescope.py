# Preamble
import ugradio
import sys
import time
import numpy as np

#---------------------------------------------
#            Initialize Objects
#---------------------------------------------

telescope = ugradio.leusch.LeuschTelescope()
spectrometer = ugradio.leusch.Spectrometer()
noise_diode = ugradio.leusch.LeuschNoise()

#---------------------------------------------
print("We are starting with an initial pointing alt, az of:", telescope.get_pointing())
telescope.stow() # move to the stow position for callibration
#---------------------------------------------
N = 10
ra,dec = 0, 0 
noise_diode.on()
spectrometer.read_spec("callibration_noise.fits", N, (ra,dec), "eq") 
noise_diode.off() 
spectrometer.read_spec("callibration_no_noise.fits", N, (ra,dec), "eq") 

