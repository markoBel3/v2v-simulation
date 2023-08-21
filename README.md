## V2V-simulation (Vehicle to vehicle Communication in Improving Road Congestion and Lowering Number of Accidents)
This is a supplemental code part of the master thesis.

# Setup
- install Carla package (https://carla.readthedocs.io/en/latest/start_quickstart/#carla-installation)
- setup XMPP server. Any can work. In these simulations used ejabberd (https://www.ejabberd.im/)
- open the repo and install requirements (pip install -r requirements.txt)

# Running the simulation code
- start Carla
- start XMPP server
- python manual_control.py
- python crash_prevention.py --asynch
