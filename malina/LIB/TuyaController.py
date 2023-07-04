import logging
import time

from malina.LIB.TuyaAuthorisation import TuyaAuthorisation
from malina.LIB.PondPumpAuto import PondPumpAuto
from malina.LIB.Device import Device


class TuyaController():
    def __init__(self, authorisation: TuyaAuthorisation):
        self.authorisation = authorisation
        self.pump_auto = PondPumpAuto(authorisation.device_manager)

    def switch_device(self, device: Device, value) -> bool:
        try:
            api_sw = device.get_api_sw
            commands = {"devId": device.get_id(), "commands": [{"code": api_sw, "value": value}]}
            resp = self.authorisation.device_manager.send_commands(commands["devId"], commands['commands'])
            return bool(resp['success'])
        except  Exception as ex:
            logging.error("---------Problem in switch_device method and class TuyaController ---------")
            logging.error(device)
            logging.error(ex)
            return False

    def _status(self, device_id):
        try:
            logging.debug(" ---------Getting device status for %s  ---------" % device_id)
            status = self.authorisation.device_manager.get_device_list_status([device_id])
            logging.debug(f" --------- device status is: {status}  ---------")
            if status["success"]:
                device_status = status['result'][0]['status']
                sw_status = {v['code']: v['value'] for v in device_status}
                if "Power" in sw_status:
                    sw_status.update({"switch_1": int(sw_status.get("Power"))})
                if "switch_1" not in sw_status and "switch" in sw_status:
                    sw_status.update({"switch_1": int(sw_status.get("switch")), "switch": int(sw_status.get("switch"))})
                extra_params = {
                    'status': int(sw_status['switch_1']), 't': int(status['t'] / 1000), 'device_id': device_id,
                    'success': status['success']}
                sw_status.update(extra_params)
                return sw_status
            else:
                raise Exception("Wasn't successfully executed command for device: %s" % device_id)

        except Exception as ex:
            logging.error("---------Problem in _status method and class TuyaController ---------")
            logging.error(ex)
            return {'success': False}

    def switch_on_device(self, device: Device):
        switched = self.switch_device(device, True)
        if switched:
            device.update_status({'switch_1': 1, "switch": 1})

        return switched

    def switch_off_device(self, device: Device):
        return self.switch_device(device, False)

    def update_status(self, device: Device):
        device_id = device.get_id()
        status = self._status(device_id)
        if status['success']:
            device.update_status(status)
        return status

    def switch_all_on_soft(self, devices):
        for device in devices:
            if device.is_device_ready_to_switch_on():
                logging.error(
                    f"Device is ready to switch ON dev name: {device.name} voltage: {device.voltage} last switch: {device.last_switched}")

                # self.switch_on_device(device)
                time.sleep(5)

    def switch_all_off_soft(self, devices):
        for device in devices:
            if device.is_device_ready_to_switch_off():
                logging.error(
                    f"Device is ready to switch OFF dev name: {device.name} voltage: {device.voltage} last switch: {device.last_switched}")

                # self.switch_off_device(device)
                time.sleep(5)

    def switch_all_on_hard(self, devices):
        for device in devices:
            self.switch_on_device(device)
            time.sleep(5)

    def switch_all_off_hard(self, devices):
        for device in devices:
            self.switch_off_device(device)
            time.sleep(5)

    def update_devices_status(self, devices):
        for device in devices:
            logging.debug(f"Updated device  status: {device.get_name()}")
            self.update_status(device)
            time.sleep(5)

    def switch_on_off_all_devices(self, devices):
        self.switch_all_on_soft(devices)
        self.switch_all_off_soft(devices)

    def adjust_devices_speed(self, devices):
        for device in devices:
            if not device.get_device_type == 'PUMP':
                continue
            is_device_ready = device.is_device_ready_to_switch_on() or device.is_device_ready_to_switch_off()
            if is_device_ready and int(device.get_status("mode")) == 6:
                logging.debug(f"Adjust device  speed: {device.get_name()}")
                self._adjust_pump_power(device)
            elif not int(device.get_status("mode")) == 6:
                logging.info(f"Pump working mode= {device.get_status('mode')}  so no adjustments could be done ")
                logging.debug(f"device {device.name} is not ready yet")

    def _adjust_pump_power(self, device):
        try:
            device_type = device.get_device_type
            speed = self.pump_auto.pond_pump_adj(device)
            pump_curr_speed = int(device.get_status("P"))
            if pump_curr_speed == speed:
                logging.info(" Pump's Speed is optimal : %d  -----so no adjustments needed !!!!!!!!!" % speed)
            if device_type == "PUMP":
                switch_device = self.switch_device(device, speed)
                if switch_device:
                    logging.info("!!!!!   Pump's Speed successfully adjusted to: %d !!!!!!!!!" % speed)
                    self._status(device.get_id())
                else:
                    time.sleep(10)
                    switch_device = self.switch_device(device, speed)
                    if not switch_device:
                        logging.error(
                            "!!!!   Pump's Speed has failed after SLEEP 10 SEC to adjust in speed to: %d !!!!" % speed)
                    else:
                        logging.info(
                            "!!!!!   Pump's Speed successfully adjusted AFTER SLEEP 10 SEC to: %d !!!!!!!!!" % speed)
        except Exception as e:
            logging.error(f"Something is wrong with adjustment type is wrong: {str(e)}. The device is {device}")
