# Preamble
import ugradio
import sys
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

parser.add_argument('-obj_type', action='store', dest='obj_type',
                    help='Store a string value for the type of celestial object being observed.')
                    
parser.add_argument('-RA', action='store', nargs="?", default=None, dest='RA', 
                    help='Store a constant value for the RA of object.')

parser.add_argument('-DEC', action='store', nargs="?", default=None, dest='DEC',
                    help='Store a constant value for the declination of object.')

results = parser.parse_args()
print('Observation Time = {0} Minutes'.format(float(results.obs_len)))
print('Pause Time = {0} Seconds'.format(float(results.pause_time)))
print('Time Resolution = {0} Seconds'.format(float(results.resolution)))
print('Object Type = {0}'.format(results.obj_type))
print('RA = {0} degrees'.format(results.RA))
print('DEC = {0} degrees'.format(results.DEC))

#-----------------------------------------------

imf = ugradio.interf.Interferometer()
hpm = ugradio.hp_multi.HP_Multimeter()

def take_data(obs_length, time_per_iter, dt, obj_type="pt_source", init_ra=None, init_dec=None):
    
    """
    - obs_length: observation time (minutes)
    - time_per_iter: how long to wait before moving the telescope again (seconds)
    - dt: how often to read voltage (seconds) (time resolution of data)
    - obj_type: what kind of object do you want to observe [string] options are ('sun', 'moon', 'pt_source')
    - init_ra: initial RA coordinate in float form for pt_source objects only
    - init_dec: initial DEC coordinate in float form for pt_source objects only
    
    RETURNS
    - final_data[0]: array of voltages
    - final_data[1]: array of times
    """
    
    imf.stow() # stow telescope to initialize data collecting (in case someone else didn't stow)
    
    start_time = ugradio.timing.julian_date() # define start time of observation
    delta_jd = obs_length/(24*60) # convert obs_length to Julian date
    end_time = start_time + delta_jd # define when to end observation
    print("Observation Started with Julian Date: {0}".format(start_time))
    
    jd = ugradio.timing.julian_date() # default=now
    
    # input the time and will return the alt and az of the object
    def calc_pos(jd):
        if init_ra is not None and init_dec is not None and obj_type == "pt_source":
            ra, dec = ugradio.coord.precess(init_ra, init_dec, jd, equinox="J2000") #point source
        elif init_ra is None and init_dec is None:
            if obj_type == "sun":
                ra, dec = ugradio.coord.sunpos(jd)
            elif obj_type == "moon":
                ra, dec = ugradio.coord.moonpos(jd)
            else:
                raise AssertionError("You need to supply RA & DEC")

        lat, long, alt_nch = ugradio.nch.lat, ugradio.nch.lon, ugradio.nch.alt 
        alt, az = ugradio.coord.get_altaz(ra, dec, jd, lat, long, alt_nch)
        return alt, az # alt, az of the object right now
    
    # point the telescope to initial object position
    alt, az = calc_pos(jd)
    print('Moving to initial object position... \n')
    print("Using initial alt, az = {0:0.4f}, {1:0.4f}".format(alt,az))
    imf.point(alt, az)
    
    i = 0
    flipped_flag = False
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
            
        
        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        #                             Pointing
        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

        alt, az = calc_pos(jd) # recalculate the alt, az of the object at new JD
        if flipped_flag == True:
            #if telescope has been flipped already, keep it flipped.
            az += 180 # flip the telescope so that it doesn't error
            alt = 180-alt # flip the telescope so that it doesn't error
            
        try:
            imf.point(alt, az) # repoint the telescope to new alt, az, following the object's path
            print("Succesfully pointed, moved to new alt, az: {0:0.3f}, {1:0.3f}".format(alt, az))
            
        except(AssertionError):
            print("Failed alt, az = {0}, {1}".format(alt,az))
            # check if object is in the northern sky                
            if az < ugradio.interf.AZ_MIN or az > ugradio.interf.AZ_MAX and flipped_flag == False: # if outside az range
                az += 180 # flip the telescope so that it doesn't error
                alt = 180-alt # flip the telescope so that it doesn't error
                print('Outside azimuth range... attempting a flip.')

                try:
                    imf.point(alt, az) # point to new alt, az in the event that former alt, az was out of range
                    flipped_flag = True
                    print("Succesfully pointed, moved to new alt, az: {0:0.3f}, {1:0.3f}".format(alt, az))
                
                except: # if something else goes wrong
                    print("Flip Pointing Failed alt, az = {0}, {1}".format(alt,az))
                    print("That shit failed, saving data and moving to stow position.")
                    break

            elif az < ugradio.interf.AZ_MIN or az > ugradio.interf.AZ_MAX and flipped_flag == True:
                az -= 180
                alt = 180 - alt
                print('Flipped telescope outside azimuth range... attempting a reverse flip.')

                try:
                    imf.point(alt, az) # point to new alt, az in the event that former alt, az was out of range
                    flipped_flag = False
                    print("Succesfully pointed, moved to new alt, az: {0:0.3f}, {1:0.3f}".format(alt, az))
                
                except: # if something else goes wrong
                    print("Reverse flip Pointing Failed alt, az = {0}, {1}".format(alt,az))
                    print("That shit failed, saving data and moving to stow position.")
                    break
                
            else:
                print("The code probably broke because ugradio/interferometer is broken.")

        i+=1
        sys.stdout.flush()

            
    final_data = hpm.get_recording_data()
    np.save("final_data.npy", final_data)
    print('Final data saved.')
    
    hpm.end_recording() # end recording
    imf.stow() # stow telescope
    
    return final_data

#-----------------------------------------------

if __name__ == "__main__":
    take_data(float(results.obs_len), float(results.pause_time), 
              float(results.resolution), results.obj_type, 
              float(results.RA), float(results.DEC))