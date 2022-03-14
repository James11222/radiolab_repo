There are 3 scripts:

### SUN SCRIPT: 
`python3 observe_obj_script.py -obs_time 1 -pause_time 1 -dt 0.1 -obj_type=sun`

### MOON SCRIPT: 
`python3 observe_obj_script.py -obs_time 1 -pause_time 1 -dt 0.1 -obj_type=moon`

### CELESTIAL OBJECT SCRIPT:
`python3 observe_obj_script.py -obs_time 1 -pause_time 1 -dt 0.1 -obj_type=pt_source -RA 5.5755278 -DEC 22.0144722`


Here are examples. The last one is configured for the crab nebula. 

```
- obs_time: observation time (minutes)
- pause_time: how long to wait before moving the telescope again (seconds)
- dt: how often to read voltage (seconds) (time resolution of data)
- obj_type: what kind of object do you want to observe [string] options are ('sun', 'moon', 'pt_source')
- init_ra: initial RA coordinate in float form for pt_source objects only
- init_dec: initial DEC coordinate in float form for pt_source objects only
```