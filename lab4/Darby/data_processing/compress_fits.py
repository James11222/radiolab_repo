import os
from astropy.io import fits
import numpy as np

# data_dict = {} # dict where key is coordinate [l, b] and value is [main, noise_on, noise_off]
for filename in os.listdir(os.getcwd()):
    if filename == ".ipynb_checkpoints":
        continue
    split_name = filename.split("_")
    if split_name[0] != 'celestial':
        continue

    if split_name[2] == 'off':
        prefix = 'off' # off
    elif split_name[2] == 'on':
        prefix = 'on' # on
    else:
        prefix = 'main' # main

    l, b = split_name[-1].split(" , ")
    b = b.split('.fits')[0]
    num_l, num_b = float(l), float(b) # convert strings to floats

#         if not data_dict.get([l, b]):
#             data_dict[[l, b]] = [[], [], []]
#         data_dict[[l, b]][fits_type] = curr_data
    fits_data = fits.open(filename)
    data_arr = np.zeros((8192, len(fits_data)-1))

    for i in range(1, len(fits_data)):
        data_arr[:,i-1] = fits_data[i].data['auto0_real']
    
    new_filename = os.getcwd() +'/celestial_data/' + prefix + '_' + l + '_' + b + '_.fits'
    np.save(data_arr, new_filename)
    
        