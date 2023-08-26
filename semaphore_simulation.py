#!/usr/bin/env python
import glob
import os
import sys
import time
import asyncio
import spade
import carla

import argparse
import logging
from numpy import random
from helpers.register_user_ejabberd import register_user
from spade_classes.semaphore_simulation_spade import CarAgent

client = None
agents = []
vehicles_list = []
world_clean = False
camera = None
async def clear_world():
    # Stop all agents
    agents_stopped = 0
    for agent in agents:
        if agent.is_alive:
            await agent.stop()
            await asyncio.sleep(0.2)
            agents_stopped+=1
    world = client.get_world()
    settings = world.get_settings()
    settings.synchronous_mode = False
    settings.fixed_delta_seconds = None
    world.apply_settings(settings)

    print('\ndestroying %d vehicles' % len(vehicles_list))
    print(f"Spade agents stopped: {agents_stopped}")
    client.apply_batch([carla.command.DestroyActor(x) for x in vehicles_list])
    global camera
    if camera:
        camera.destroy()
    global world_clean
    world_clean = True
    time.sleep(2)

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
    argparser.add_argument(
        '--tm-port',
        metavar='P',
        default=8000,
        type=int,
        help='Port to communicate with TM (default: 8000)')
    argparser.add_argument(
        '--asynch',
        action='store_true',
        help='Activate asynchronous mode execution')
    argparser.add_argument(
        '--hybrid',
        action='store_true',
        help='Activate hybrid mode for Traffic Manager')
    argparser.add_argument(
        '--respawn',
        action='store_true',
        default=False,
        help='Automatically respawn dormant vehicles (only in large maps)')

    args = argparser.parse_args()

    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    global client
    client = carla.Client(args.host, args.port)
    client.set_timeout(10.0)
    synchronous_master = False
    seed_to_use = 33
    random.seed(seed_to_use)

    try:
        world = client.get_world()
        traffic_manager = client.get_trafficmanager(args.tm_port)
        traffic_manager.set_random_device_seed(seed_to_use)
        if args.respawn:
            traffic_manager.set_respawn_dormant_vehicles(True)
        if args.hybrid:
            traffic_manager.set_hybrid_physics_mode(True)
            traffic_manager.set_hybrid_physics_radius(70.0)

        settings = world.get_settings()
        if not args.asynch:
            traffic_manager.set_synchronous_mode(True)
            if not settings.synchronous_mode:
                synchronous_master = True
                settings.synchronous_mode = True
                settings.fixed_delta_seconds = 0.03
            else:
                synchronous_master = False
        else:
            print("You are currently in asynchronous mode. If this is a traffic simulation, \
            you could experience some issues. If it's not working correctly, switch to synchronous \
            mode by using traffic_manager.set_synchronous_mode(True)")

        world.apply_settings(settings)

        # @todo cannot import these directly.
        SpawnActor = carla.command.SpawnActor
        SetAutopilot = carla.command.SetAutopilot
        FutureActor = carla.command.FutureActor

        # --------------
        # Spawn vehicles
        # --------------
        custom_transforms = [carla.Transform(carla.Location(x=19.0, y=141.3, z=0.6),carla.Rotation(pitch=0.0, yaw=0.0, roll=0.0)),
                             carla.Transform(carla.Location(x=13.0, y=141.3, z=0.6),carla.Rotation(pitch=0.0, yaw=0.0, roll=0.0)), 
                             carla.Transform(carla.Location(x=7.0, y=141.3, z=0.6),carla.Rotation(pitch=0.0, yaw=0.0, roll=0.0)),
                             carla.Transform(carla.Location(x=1.0, y=141.3, z=0.6),carla.Rotation(pitch=0.0, yaw=0.0, roll=0.0)),
                             carla.Transform(carla.Location(x=-6.0, y=141.3, z=0.6),carla.Rotation(pitch=0.0, yaw=0.0, roll=0.0)),
                             carla.Transform(carla.Location(x=-12.0, y=141.3, z=0.6),carla.Rotation(pitch=0.0, yaw=0.0, roll=0.0)),
                             carla.Transform(carla.Location(x=-18.0, y=141.3, z=0.6),carla.Rotation(pitch=0.0, yaw=0.0, roll=0.0)),
                             carla.Transform(carla.Location(x=-24.0, y=141.3, z=0.6),carla.Rotation(pitch=0.0, yaw=0.0, roll=0.0)),
                             carla.Transform(carla.Location(x=19.0, y=137.4, z=0.6),carla.Rotation(pitch=0.0, yaw=0.0, roll=0.0)),
                             carla.Transform(carla.Location(x=13.0, y=137.4, z=0.6),carla.Rotation(pitch=0.0, yaw=0.0, roll=0.0)), 
                             carla.Transform(carla.Location(x=7.0, y=137.4, z=0.6),carla.Rotation(pitch=0.0, yaw=0.0, roll=0.0)),
                             carla.Transform(carla.Location(x=1.0, y=137.4, z=0.6),carla.Rotation(pitch=0.0, yaw=0.0, roll=0.0)),
                             carla.Transform(carla.Location(x=-6.0, y=137.4, z=0.6),carla.Rotation(pitch=0.0, yaw=0.0, roll=0.0)),
                             carla.Transform(carla.Location(x=-12.0, y=137.4, z=0.6),carla.Rotation(pitch=0.0, yaw=0.0, roll=0.0)),
                             carla.Transform(carla.Location(x=-18.0, y=137.4, z=0.6),carla.Rotation(pitch=0.0, yaw=0.0, roll=0.0)),
                            carla.Transform(carla.Location(x=-24.0, y=137.4, z=0.6),carla.Rotation(pitch=0.0, yaw=0.0, roll=0.0))]
        batch = []
        blueprint = random.choice([x for x in world.get_blueprint_library().filter('vehicle.*') if 'tesla' in x.id.lower()])
        for ct in custom_transforms:
            if blueprint.has_attribute('color'):
                color = random.choice(blueprint.get_attribute('color').recommended_values)
                blueprint.set_attribute('color', color)
            if blueprint.has_attribute('driver_id'):
                driver_id = random.choice(blueprint.get_attribute('driver_id').recommended_values)
                blueprint.set_attribute('driver_id', driver_id)
            blueprint.set_attribute('role_name', 'autopilot')

            # spawn the cars and set their autopilot
            batch.append(SpawnActor(blueprint, ct).then(SetAutopilot(FutureActor, True, traffic_manager.get_port())))
        
        for response in client.apply_batch_sync(batch, synchronous_master):
            if response.error:
                logging.error(response.error)
            else:
                vehicles_list.append(response.actor_id)
                car = world.get_actor(response.actor_id)
                agent = CarAgent(f"car{response.actor_id}@localhost", f"pass{response.actor_id}", car)
                try:
                    await agent.start(auto_register=False)
                except spade.agent.AuthenticationFailure:
                    register_user(f"car{response.actor_id}", f"pass{response.actor_id}")
                    await agent.start()
                agents.append(agent)
        for agent in agents:
            receivers = [f"{a.name}@localhost" for a in agents if a != agent]
            agent.receivers = receivers


        print('spawned %d vehicles, press Ctrl+C to exit.' % (len(vehicles_list)))

        traffic_lights = world.get_actors().filter('traffic.traffic_light')
        for tl in traffic_lights:
            tl.set_state(carla.TrafficLightState.Red)  
            tl.freeze(True)

        traffic_manager.global_percentage_speed_difference(-100.0)
        route_to_follow = [carla.Location(x=105, y=-40, z=0.6), carla.Location(x=27.4, y=-66.4, z=0.6)]
        for actor_id in vehicles_list:
            vehicle = world.get_actor(actor_id)
            traffic_manager.set_desired_speed(vehicle, 100.0)
            traffic_manager.distance_to_leading_vehicle(vehicle, 2.5)
            traffic_manager.set_path(vehicle, route_to_follow)

        # blueprint_library = world.get_blueprint_library()
        # camera_bp = blueprint_library.find('sensor.camera.rgb')
        # camera_bp.set_attribute('image_size_x', '1920')
        # camera_bp.set_attribute('image_size_y', '1080')
        camera_location = carla.Location(x=123.42, y=72.08, z=41.52)
        camera_rotation = carla.Rotation(pitch=-63.41, yaw=-167.49, roll=0.0)
        camera_transform = carla.Transform(camera_location, camera_rotation)
        # global camera
        # camera = world.spawn_actor(camera_bp, camera_transform)
        # def process_image(image):
        #     image.save_to_disk('camera-photos/%06d.png' % image.frame)

        # camera.listen(lambda image: process_image(image))

        spectator = world.get_spectator()
        spectator.set_transform(camera_transform)

        while True:
            if not args.asynch and synchronous_master:
                world.tick()
            else:
                world.wait_for_tick()
                await asyncio.sleep(2)
    finally:
        await clear_world()

if __name__ == '__main__':

    try:
        # start with --asynch
        asyncio.run(main())
    except KeyboardInterrupt:
        if not world_clean:
            asyncio.run(clear_world())
    finally:
        print('\ndone.')