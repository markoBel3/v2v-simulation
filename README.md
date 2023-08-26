## V2V-simulation (Vehicle to vehicle Communication in Improving Road Congestion and Lowering Number of Accidents)
This is a supplemental code part of the master thesis.

# Setup
- install Carla package (https://carla.readthedocs.io/en/latest/start_quickstart/#carla-installation)
- setup XMPP server. Any can work. In these simulations used ejabberd (https://www.ejabberd.im/)
- open the repo and install requirements (pip install -r requirements.txt)

# Running the simulation code
- start Carla
- start XMPP server
## Crash Prevention Simulation
- python manual_control.py
- python crash_prevention.py --asynch

## Lane Change Assist Simulation
- python manual_control_lane_change.py
- python lane_change_simulation.py --asynch

## Road Congestion Improvement Using Semaphore Messages
- python semaphore_simulation.py --asynch
- python semaphore_control.py
