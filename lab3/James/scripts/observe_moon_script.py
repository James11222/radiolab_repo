# Preamble
import ugradio
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.time import Time
from datetime import datetime
from datetime import timedelta
import time
import numpy as np

#---------------------------------------------

import argparse

parser = argparse.ArgumentParser(description='Observing Script')

parser.add_argument('-obs_time', action='store', dest='obs_len',
                    help='Store a constant value for observation window in minutes.')
                    
parser.add_argument('-pause_time', action='store', dest='pause_time',
                    help='Store a constant value for the time taken to pause the telescope when observing.')

parser.add_argument('-dt', action='store', dest='resolution',
                    help='Store a constant value for the time resolution of observation.')

results = parser.parse_args()
print('Observation Time = {0} Minutes'.format(int(results.obs_len)))
print('Pause Time = {0} Seconds'.format(float(results.pause_time)))
print('Time Resolution = {0} Seconds'.format(float(results.resolution)))

#-----------------------------------------------

imf = ugradio.interf.Interferometer()
hpm = ugradio.hp_multi.HP_Multimeter()

def take_data(obs_length, time_per_iter, dt):
    
    """
    - obs_length: observation time (minutes)
    - time_per_iter: how long to wait before moving the telescope again (seconds)
    - dt: how often to read voltage (seconds) (time resolution of data)
    
    RETURNS
    - final_data[0]: array of voltages
    - final_data[1]: array of times
    """
    
    imf.stow() # stow telescope to initialize data collecting (in case someone else didn't stow)
    
    start_time = ugradio.timing.julian_date() # define start time of observation
    delta_jd = obs_length/(24*60) # convert obs_length to Julian date
    end_time = start_time + delta_jd # define when to end observation
    
    jd = ugradio.timing.julian_date() # default=now
    
    # input the time and will return the alt and az of the object
    def calc_pos(jd):
        ra, dec = ugradio.coord.moonpos(jd) # ra and dec coords
        lat, long, alt_nch = ugradio.nch.lat, ugradio.nch.lon, ugradio.nch.alt 
        alt, az = ugradio.coord.get_altaz(ra, dec, jd, lat, long, alt_nch)
        return alt, az # alt, az of the object right now
    
    # point the telescope to initial object position
    alt, az = calc_pos(jd)
    print('Moving to initial object position...')
    imf.point(alt, az)
    
    i = 0
    hpm.start_recording(dt)
    while jd < end_time: 
        print(i, "iteration")
        # how often to move the telescope    
        time.sleep(time_per_iter) # keep telescope at this position for this amount of time -- collects data
        jd = ugradio.timing.julian_date() # recalculate JD
        
        if i%10 == 0: # saving the data frequently in case of error
            final_data = hpm.get_recording_data() # collect data
            np.save("final_data.npy", final_data) # dave data
            print('Saving data.')
            
        alt, az = calc_pos(jd) # recalculate the alt, az of the object at new JD
        
        #pointing
        try:
            imf.point(alt, az) # repoint the telescope to new alt, az, following the object's path
            print("Succesfully pointed, moved to new alt, az: {0:0.3f}, {1:0.3f}".format(alt, az))
            
        except:
            # check if object is in the northern sky
            if alt < ugradio.interf.ALT_MIN or alt > ugradio.interf.ALT_MAX: # if outside alt range
                alt = 180-alt # flip the telescope so that it doesn't error
                #alt -= 180 
                print('Outside altitude range so flipping.')
                
            if az < ugradio.interf.AZ_MIN or az > ugradio.interf.AZ_MAX: # if outside az range
                az += 180 # flip the telescope so that it doesn't error
                print('Outside azimuth range so flipping.')
                
            try:
                imf.point(alt, az) # point to new alt, az in the event that former alt, az was out of range
                print("Succesfully pointed, moved to new alt, az: {0:0.3f}, {1:0.3f}".format(alt, az))
                
            except: # if something else goes wrong
                print("That shit failed, saving data and moving to stow position.")
                break
            
        i+=1

            
    final_data = hpm.get_recording_data()
    np.save("final_data.npy", final_data)
    print('Final data saved.')
    
    hpm.end_recording() # end recording
    imf.stow() # stow telescope
    
    return final_data

#-----------------------------------------------

if __name__ == "__main__":
    take_data(results.obs_len, results.pause_time, results.resolution)