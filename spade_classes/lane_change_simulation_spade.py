import asyncio
from collections import deque
import math
import spade
import carla
from exceptions.carla_related_exceptions import VehicleDestroyed

bsm_template = spade.template.Template()
bsm_template.metadata = {"performative": "inform", "ontology": "bsm"}

def get_speed(vehicle):
    velocity = vehicle.get_velocity()
    speed = 3.6 * math.sqrt(velocity.x**2 + velocity.y**2 + velocity.z**2)
    # print(f"speed {speed}")
    return speed

class CarAgent(spade.agent.Agent):
    def __init__(self, jid, password, carla_vehicle):
        super().__init__(jid, password)
        self.carla_vehicle = carla_vehicle
        self.receivers = []
        self.dict_positions = {}
        self.dict_vehicle_speed_list = {}

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
            msg.body = f"{self.agent.name}*Location:{location.x},{location.y},{location.z}*Crash:{crash}*Speed:{get_speed(self.agent.carla_vehicle)}"
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
                # print(f"msg_spliited: {msg_splitted}")
                car_name = msg_splitted[0]
                car_location = msg_splitted[1].split(":")[1]
                x,y,z = car_location.split(",")
                car_speed = float(msg_splitted[3].split(":")[1])
                loc = carla.Location(x=float(x), y=float(y), z=float(z))
                if car_name in self.agent.dict_positions:
                    self.agent.dict_positions[car_name].append(loc)
                else:
                    self.agent.dict_positions[car_name] = deque(maxlen=5)
                    self.agent.dict_positions[car_name].append(loc)
                self.agent.dict_vehicle_speed_list[car_name] = car_speed
                # print(f"{self.agent.name} got message: {msg.body}")

    async def setup(self):
        self.add_behaviour(self.SendBSMBehaviour(period=0.5), None)
        self.add_behaviour(self.ParseBSM(), bsm_template)