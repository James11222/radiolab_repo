#!/usr/bin/env python
# coding: utf-8


import ugradio

import numpy as np
import matplotlib.pyplot as plt

import astropy
from astropy import units as u
from astropy.time import Time
from astropy.coordinates import SkyCoord, AltAz, EarthLocation

# ------------------------------------------------------------------------------------------------------------------------------------------

def take_leusch_data(init_l, init_b, nspec, filename_noise_on, filename_noise_off):
    
    """
    Take data using the Leuschner Telescope at Leuschner Observatory.
    
    Input:
        init_l: galactic longitude(s)
        init_b: galactic latitude(s)
        nspec: number of spectra to collect at each coordinate point 
            Each iteration takes ~0.7s, so nspec = 1 will take approxmately 700 seconds to run
        filename_noise_on: name of the file that will collect data with the noise diode on. Input as a string, ending with '.fits' so that it saves as a FITS file.
            Example: filename_noise_on = 'file_with_noise_on.fits'
        filename_noise_off: name of the file that will collect data with the noise diode off. Input as a string, ending with '.fits' so that it saves as a FITS file.
            Example: filename_noise_off = 'file_with_noise_off.fits'
            
                
    Returns:
        Two FITS files, one in which the noise diode was one and another in which the noise diode was off, named according to input strings.
    """
    
    #-------------------------------------------------------------------------------------------------------
    #                                          Initialize Objects        
    #-------------------------------------------------------------------------------------------------------
    telescope = ugradio.leusch.LeuschTelescope()
    spectrometer = ugradio.leusch.Spectrometer()
    noise = ugradio.leusch.LeuschNoise()
    
    
    LT_lat, LT_lon, LT_alt = ugradio.leo.lat, ugradio.leo.lon, ugradio.leo.alt # get LT coords
    
    
    #-------------------------------------------------------------------------------------------------------
    #                      Define function that transforms between coordinate systems            
    #-------------------------------------------------------------------------------------------------------
    def calc_pos(l, b):
            from astropy.coordinates import SkyCoord, AltAz, EarthLocation
            gc = SkyCoord(l=l*u.degree, b=b*u.degree, frame='galactic')
            loc = EarthLocation(lat=LT_lat*u.deg, lon=LT_lon*u.deg, height=LT_alt*u.m)
            time = Time(ugradio.timing.utc(fmt='%Y-%m-%d %X'))
            AltAz = gc.transform_to(AltAz(obstime=time, location=loc))
            alt, az = AltAz.alt.degree, AltAz.az.degree
        return alt, az
    
    #-------------------------------------------------------------------------------------------------------
    #                            Point the telescope and collect data            
    #-------------------------------------------------------------------------------------------------------
    n_fails = 0
    end_obs = False
    
    for l in init_l:
        for b in init_b:
            alt, az = calc_pos(l, b) #calculate alt, az,
            print('Moving to position... \n')
            
            
            try:
                telescope.point(alt, az) # point LT to calculated alt, az
                
                print('Current L.T. alt, az (degrees): {0:.4f}, {1:.4f}'.format(alt, az), 
                      '\nTurning on noise diode.)
                noise.on()
                print('Collecting spectrum with noise diode on.')
                spectrometer.read_spec(filename_noise_on+'_'+str((l, b)), nspec, (l,b), 'ga')
                      
                print('Finished collecting spectrum with noide diode on. Turning off noise diode...')
                noise.off()
                print('Collecting spectrum with noise diode off.')
                spectrometer.read_spec(filename_noise_off+'_'+str((l, b)), nspec, (l,b), 'ga')
                print('Finished collecting spectrum with noise diode off.')
                      
                      
            except: # If pointing fails...
                print('Failed to point to (alt, az)=({0:.4f}, {1:.4f}) (degrees)'.format(alt, az), 
                      '\nPointing to next (alt, az).')
                n_fails += 1
                if n_fails == 10: # If number of pointing errors = 10 then break and end obs
                    end_obs = True
                    break
                continue
                      
                      
        if end_obs:
            print('Too many pointing errors... Ending observation.')
            break # end the observation
            
    
    telescope.stow() # stow when finished
                

# ------------------------------------------------------------------------------------------------------------------------------------------

#take_leusch_data(init_l, init_b, nspec, filename_noise_on, filename_noise_off)

