import asyncio
import math
import spade
import carla
from exceptions.carla_related_exceptions import VehicleDestroyed

bsm_template = spade.template.Template()
bsm_template.metadata = {"performative": "inform", "ontology": "bsm"}

environment_template = spade.template.Template()
environment_template.metadata = {"performative": "inform", "ontology": "environment"}

def is_vehicle_stationary(vehicle, threshold=15):
    velocity = vehicle.get_velocity()
    # speed = 3.6 * math.sqrt(velocity.x**2 + velocity.y**2 + velocity.z**2)
    speed = math.sqrt(velocity.x**2 + velocity.y**2 + velocity.z**2)
    # print(f"speed {speed}")
    return speed < threshold

class CarAgent(spade.agent.Agent):
    def __init__(self, jid, password, carla_vehicle):
        super().__init__(jid, password)
        self.carla_vehicle = carla_vehicle
        self.receivers = []

    class SendBSMBehaviour(spade.behaviour.PeriodicBehaviour):
        async def run(self):
            try:
                msg = self.create_bsm_message()
                if msg.body == "":
                    return
            except VehicleDestroyed:
                await self.agent.stop()
                return
            await self.send_message_to_all(msg)

        async def on_end(self):
            pass

        async def on_start(self):
            pass

        def create_bsm_message(self):
            msg = spade.message.Message()
            if not self.agent.carla_vehicle:
                msg.body = ""
            if not self.agent.carla_vehicle.is_alive:
                raise VehicleDestroyed("Please stop agent")
            location = self.agent.carla_vehicle.get_transform().location
            crash = False
            if hasattr(self.agent.carla_vehicle, "crash") and self.agent.carla_vehicle.crash:
                crash = True
                self.agent.carla_vehicle.crash = False
            msg.set_metadata("performative", "inform")
            msg.set_metadata("ontology", "bsm")
            msg.body = f"{self.agent.name}*Location:{location.x},{location.y},{location.z}*Crash:{crash}"
            return msg
        
        async def send_message_to_all(self, msg):
            for a in self.agent.receivers:
                msg.to = a
                await self.send(msg)

    class ParseBSM(spade.behaviour.CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)
            if msg:
                msg_splitted = msg.body.split("*")
                if msg_splitted[2] == "Crash:True":
                    print("breaking")
                    self.agent.carla_vehicle.set_autopilot(False)
                    control = carla.VehicleControl(throttle=0.0, steer=0.0, brake=1.0, hand_brake=True)
                    self.agent.carla_vehicle.apply_control(control)
                    await asyncio.sleep(5)
                    self.agent.carla_vehicle.set_autopilot(True)
                # print(f"{self.agent.name} got message: {msg.body}")
    
    class ParseEnvMsg(spade.behaviour.CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)
            if msg:
                if "Semaphore:Green" in msg.body:
                    msg_splitted = msg.body.split(",")
                    semaphore_location = carla.Location(x=float(msg_splitted[1]), y=float(msg_splitted[2]), z=0)
                    vehicle_location = self.agent.carla_vehicle.get_transform().location
                    print(f"{self.agent.name} - distance: {vehicle_location.distance(semaphore_location)}")
                    print(f"{self.agent.name} - stationary: {is_vehicle_stationary(self.agent.carla_vehicle)}")
                    if is_vehicle_stationary(self.agent.carla_vehicle) and vehicle_location.distance(semaphore_location) < 90:
                        print("starting")
                        self.agent.carla_vehicle.set_autopilot(False)
                        control = carla.VehicleControl(throttle=1.0, steer=0.0, brake=0.0)
                        self.agent.carla_vehicle.apply_control(control)
                        await asyncio.sleep(4)
                        self.agent.carla_vehicle.set_autopilot(True)
                # print(f"{self.agent.name} got message: {msg.body}")

    async def setup(self):
        #self.add_behaviour(self.SendBSMBehaviour(period=0.5), None)
        #self.add_behaviour(self.ParseBSM(), bsm_template)
        self.add_behaviour(self.ParseEnvMsg(), environment_template)


class SemaphoreAgent(spade.agent.Agent):
    def __init__(self, jid, password, semaphore_obj):
        super().__init__(jid, password)
        self.semaphore = semaphore_obj
        self.receivers = []

    class SendLightStateBehaviour(spade.behaviour.PeriodicBehaviour):
        async def run(self):
            try:
                msg = self.create_semaphore_message()
                if msg.body == "":
                    return
            except:
                await self.agent.stop()
                return
            await self.send_message_to_all(msg)

        async def on_end(self):
            pass

        async def on_start(self):
            pass

        def create_semaphore_message(self):
            msg = spade.message.Message()
            if not self.agent.semaphore:
                msg.body = ""
            location = self.agent.semaphore.get_transform().location
            msg.set_metadata("performative", "inform")
            msg.set_metadata("ontology", "environment")
            msg.body = f"Semaphore:{self.agent.semaphore.get_state()},{location.x},{location.y}"
            #print(msg.body)
            return msg
        
        async def send_message_to_all(self, msg):
            for a in self.agent.receivers:
                msg.to = a
                await self.send(msg)

    async def setup(self):
        self.add_behaviour(self.SendLightStateBehaviour(period=0.5), None)