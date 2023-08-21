import asyncio
import spade
import carla
from exceptions.carla_related_exceptions import VehicleDestroyed

bsm_template = spade.template.Template()
bsm_template.metadata = {"performative": "inform", "ontology": "bsm"}

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

    async def setup(self):
        self.add_behaviour(self.SendBSMBehaviour(period=0.5), None)
        self.add_behaviour(self.ParseBSM(), bsm_template)