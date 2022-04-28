import ugradio
import numpy as np
import matplotlib.pyplot as plt
import astropy
import time
from astropy import units as u
from astropy.time import Time
from astropy.coordinates import SkyCoord, AltAz, EarthLocation

# -----------------------------------------------------------------------------------------------------------

import argparse

parser = argparse.ArgumentParser(description='Observing Script')

parser.add_argument('-nspec', action='store', dest='nspec',
                    help='Store a constant value for number of spectra taken per coordinate.')

parser.add_argument('-fname', action='store', dest='filename',
                    help='Store a string for filenames we will save the data as.')

results = parser.parse_args()
print('nspec = {0}'.format(int(results.nspec)))
print('filename = {0}'.format(str(results.filename)))


# -----------------------------------------------------------------------------------------------------------

def take_leusch_data(nspec, filename):
    
    """
    Take data using the Leuschner Telescope at Leuschner Observatory.
    
    Input:
        nspec: number of spectra to collect at each coordinate point 
               Each iteration takes ~0.7s, so nspec = 1 will take approxmately 700 seconds to run
               
        filename: name of the files that will collect data on. 
                  Input as a string, without the '.fits' extension
                  Example: "north_hemisphere_data"
                             
    Returns: 
        Several .fits files, 2 per set of galactic coordinates (one with noise on and the other with noise off)
       
    """
    filename_noise_on, filename_noise_off = filename + "_noise_on", filename + "_noise_off"

    #-------------------------------------------------------------------------------------------------------
    #                                          Make Coordinate Grid        
    #-------------------------------------------------------------------------------------------------------
    
    # l_min, l_max = 105, 160
    # b_min, b_max = 15, 50

    # db = 2
    # dl = lambda b: 2/np.cos(b * (np.pi/180))

    # Δb = b_max - b_min
    # Δl = l_max - l_min

    # bs = np.array([b_min + i*db for i in range(50) if (b_min + i*db) < b_max])

    # ls = []
    # for b in bs:
    #     ls.append(np.array([l_min + i*dl(b) for i in range(50) if (l_min + i*dl(b)) < l_max]))

    # coords = []
    # for i in range(len(bs)):
    #     for j in range(len(ls[i])):
    #         coords.append([ls[i][j], bs[i]])

    coords = np.load("../Raphael/missed_coords.npy")
    
    #-------------------------------------------------------------------------------------------------------
    #                                          Initialize Objects        
    #-------------------------------------------------------------------------------------------------------
    
    telescope = ugradio.leusch.LeuschTelescope()
    spectrometer = ugradio.leusch.Spectrometer()
    noise = ugradio.leusch.LeuschNoise()
    synthesizer = ugradio.agilent.SynthDirect()
    synthesizer.set_amplitude(10.0,'dBm')
    
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
    unhit_coords = list(coords.copy())
    print(f"We start observing with {len(unhit_coords)} target coordinates")
    
    num_failed_whiles = 0
    while len(unhit_coords) != 0 or num_failed_whiles >= 5:

        num_coords_remaining_pre_loop = len(unhit_coords)

        for i,coord in enumerate(unhit_coords): 

            l, b = coord 
            
            alt, az = calc_pos(l, b) #calculate alt, az,
            if alt >= ugradio.leusch.ALT_MAX or alt <= ugradio.leusch.ALT_MIN:
                continue
            elif az >= ugradio.leusch.AZ_MAX or az <= ugradio.leusch.AZ_MIN:
                continue
            else:
                print('Moving to position... \n')
                try:
                    telescope.point(alt, az) # point LT to calculated alt, az
                    index_string = "{0:0.3f} , {1:0.3f}".format(l,b)

                    print('Current L.T. alt, az (degrees): {0:.4f}, {1:.4f}'.format(alt, az), 
                        '\nTurning on noise diode.')
                    
                    synthesizer.set_frequency(635,'MHz')
                    spectrometer.read_spec(filename "_main" +'_'+index_string + ".fits", nspec, (l,b), 'ga')
                    
                    synthesizer.set_frequency(670,'MHz')
                    noise.on()
                    print('Collecting spectrum with noise diode on.')

                    spectrometer.read_spec(filename_noise_on+'_'+index_string + ".fits", nspec, (l,b), 'ga')

                    print('Finished collecting spectrum with noide diode on. Turning off noise diode...')
                    noise.off()
                    print('Collecting spectrum with noise diode off.')
        
                    spectrometer.read_spec(filename_noise_off+'_'+index_string + ".fits", nspec, (l,b), 'ga')
                    print('Finished collecting spectrum with noise diode off.')

                    unhit_coords.pop(i)


                except: # If pointing fails...
                    print('Failed to point to (alt, az)=({0:.4f}, {1:.4f}) (degrees)'.format(alt, az), 
                        '\nPointing to next (alt, az).')
                    n_fails += 1
                    if n_fails == 200: # If number of pointing errors = 200 then break and end obs
                        end_obs = True
                        break
                    continue
            
            if end_obs:
                print('Too many pointing errors... Ending observation.')
                break # end the observation
            
        num_coords_remaining_post_loop = len(unhit_coords)

        if num_coords_remaining_post_loop == num_coords_remaining_pre_loop:
            num_failed_whiles += 1
            print("No new coordinates observed, I'm gonna sleep for 1 hour and hopefully we will see some more points.")
            time.sleep(3600) #sleep for an hour if all of our coordinates are out of bounds and see
        else:
            print(f"We have {num_coords_remaining_post_loop} coordinates remaining.")

            
            
    print("Stowing the Telescope!")
    telescope.stow() # stow when finished
                

# -----------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    take_leusch_data(int(results.nspec), str(results.filename))

