#!/usr/bin/env python
# coding: utf-8

# In[2]:


import numpy as np
from astropy.io import fits
import os


# In[3]:


for filename in os.listdir(os.getcwd()):
    if filename == ".ipynb_checkpoints" or filename == 'celestial_data':
        continue
    split_name = filename.split("_")
    if split_name[0] != 'celestial':
        continue
    print(split_name)
    if split_name[2] == 'off':
        prefix = 'off' # off
    elif split_name[2] == 'on':
        prefix = 'on' # on
    else:
        prefix = 'main' # main

    
#     l, b = split_name[-1].split(" , ")
#     b = b.split('.fits')[0]
#     num_l, num_b = float(l), float(b) # convert strings to floats

    
    fits_file = fits.open(filename)
    header = fits_file[0].header
    l, b, ra, dec, jd = header[18], header[19], header[20], header[21], header[22]
    
    data_arr = np.zeros((8192, len(fits_file)-1))

    for i in range(1, len(fits_file)):         
        data_arr[:,i-1] = fits_file[i].data['auto0_real']

    new_filename = os.getcwd() + '/celestial_data/' + prefix + '_' + l + '_' + b + '_' + ra + '_' + dec + '_' + jd + '_.npy'
    np.save(new_filename, data_arr)


# In[ ]:




