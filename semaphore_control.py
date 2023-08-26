#!/usr/bin/env python
import asyncio
import select
import sys
import carla

import argparse
import logging

import spade
from helpers.register_user_ejabberd import register_user

from spade_classes.semaphore_simulation_spade import SemaphoreAgent
from aioconsole import ainput

def find_closes_semaphore(carla_location, traffic_lights):
    closest_light = None
    closest_distance = float('inf')
    for light in traffic_lights:
        light_location = light.get_location()
        distance = light_location.distance(carla_location)
        if distance < closest_distance:
            closest_distance = distance
            closest_light = light
    return closest_light

def get_receiver_vehicles(world):
    all_actors = world.get_actors()
    vehicle_actors = all_actors.filter('vehicle.*')
    receiver_vehicles = []
    for vh in vehicle_actors:
        receiver_vehicles.append(f"car{vh.id}@localhost")
    return receiver_vehicles

async def main():
    argparser = argparse.ArgumentParser(
        description=__doc__)
    argparser.add_argument(
        '--host',
        metavar='H',
        default='127.0.0.1',
        help='IP of the host server (default: 127.0.0.1)')
    argparser.add_argument(
        '-p', '--port',
        metavar='P',
        default=2000,
        type=int,
        help='TCP port to listen to (default: 2000)')
    args = argparser.parse_args()

    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    client = carla.Client(args.host, args.port)
    client.set_timeout(10.0)

    world = client.get_world()

    traffic_lights = world.get_actors().filter('traffic.traffic_light')
    target_location = carla.Location(x=110, y=27, z=0)
    target_semaphore = find_closes_semaphore(target_location, traffic_lights)
    if not target_semaphore:
        return
    else:
        agent = SemaphoreAgent(f"semaphore{target_semaphore.id}@localhost", f"pass{target_semaphore.id}", target_semaphore)
        try:
            await agent.start(auto_register=False)
        except spade.agent.AuthenticationFailure:
                register_user(f"semaphore{target_semaphore.id}@localhost", f"pass{target_semaphore.id}")
                await agent.start()
        agent.receivers = get_receiver_vehicles(world)
    while True:
        command_from_user = await ainput("Enter 'g' for green light, 'r' for red light and 'x' for exit: ")
        if command_from_user == "g":
            target_semaphore.set_state(carla.TrafficLightState.Green)
        elif command_from_user == "r":
            target_semaphore.set_state(carla.TrafficLightState.Red)
        else:
            break
    await agent.stop()

if __name__ == '__main__':
    # first run semaphore_simulation.py
    asyncio.run(main())
    print('\ndone.')