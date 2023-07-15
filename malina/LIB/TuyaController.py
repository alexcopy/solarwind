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
        except Exception as ex:
            logging.error("---------Problem in switch_device method and class TuyaController ---------")
            logging.error(device)
            logging.error(ex)
            return False

    def _status(self, device: Device):
        try:
            device_id = device.get_id()
            logging.debug(" ---------Getting device status for %s  ---------" % device_id)
            status = self.authorisation.device_manager.get_device_list_status([device_id])['result'][0]['status']
            logging.debug(f" --------- device status is: {status}  ---------")
            if status["success"]:
                sw_status = device.extract_status_params(status)
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
            api_sw = device.get_api_sw
            device.update_status({api_sw: True})
            device.device_switched()
        return switched

    def switch_off_device(self, device: Device):
        switch = self.switch_device(device, False)
        api_sw = device.get_api_sw
        if switch:
            device.update_status({api_sw: False})
            device.device_switched()

    def update_status(self, device: Device):
        status = self._status(device)
        if status['success']:
            device.update_status(status)
        return status

    def switch_all_on_soft(self, devices):
        for device in devices:
            if device.is_device_ready_to_switch_on():
                logging.error(
                    f"Device is ready to switch ON dev name: {device.name} voltage: {device.voltage} last switch: {device.last_switched}")
                self.switch_on_device(device)
                time.sleep(5)

    def switch_all_off_soft(self, devices):
        for device in devices:
            if device.is_device_ready_to_switch_off():
                logging.error(
                    f"Device is ready to switch OFF dev name: {device.name} voltage: {device.voltage} last switch: {device.last_switched}")
                self.switch_off_device(device)
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
        device_ids = [device.get_id() for device in devices]
        statuses = self.authorisation.device_manager.get_device_list_status(device_ids)['result']

        for status in statuses:
            dev_id = status["id"]
            device = self.select_dev_by_id(devices, dev_id)
            if device is None:
                logging.error(f"Device is missing from the list with id {dev_id}")
                continue
            if "status" in status:
                status_params = device.extract_status_params(status["status"])
                device.update_status(status_params)

    def select_dev_by_id(self, devices, lookup_id):
        for device in devices:
            dev_id = device.get_id()
            if lookup_id == dev_id:
                return device
        return None

    def switch_on_off_all_devices(self, devices):
        self.switch_all_on_soft(devices)
        self.switch_all_off_soft(devices)

    def adjust_devices_speed(self, devices, inv_status):
        for device in devices:
            if not device.get_device_type == 'PUMP':
                continue

            if int(device.get_status("mode")) == 6:
                logging.debug(f"Adjust device  speed: {device.get_name()}")
                self._adjust_pump_power(device=device, inv_status=inv_status)
            elif not int(device.get_status("mode")) == 6:
                logging.info(f"Pump working mode= {device.get_status('mode')}  so no adjustments could be done ")
            else:
                logging.debug(
                    f"device {device.name} is not ready yet the status is: {device.is_device_ready_to_switch_on()}")

    def _adjust_pump_power(self, device: Device, inv_status):
        try:
            speed = self.pump_auto.pond_pump_adj(device, inv_status)
            logging.error(
                f"The calculated speed is:{speed} and device {device.get_name()} speed_cur: {device.get_status('P')}")
            pump_curr_speed = device.get_status("P")
            chk_pump_speed = self.pump_auto.check_pump_speed(device)

            if not chk_pump_speed == pump_curr_speed:
                logging.error(
                    f" Pump's Speed is needs to round up existing speed which is {pump_curr_speed} to a new speed is: {chk_pump_speed}")
                self.switch_device(device, chk_pump_speed)
                device.update_status({"P": chk_pump_speed})
                return True

            if pump_curr_speed == speed:
                logging.error(" Pump's Speed is optimal : %d  -----so no adjustments needed !!!!!!!!!" % speed)
                return True

            switch_device = self.switch_device(device, speed)
            if switch_device:
                device.update_status({"P": speed})
                logging.error(
                    f"!!!!!   Pump's Speed successfully adjusted to: {speed} the new speed is: {device.get_status('P')}!!!!!!!!! ")
            else:
                time.sleep(10)
                switch_device = self.switch_device(device, speed)
                if not switch_device:
                    logging.error(
                        "!!!!   Pump's Speed has failed after SLEEP 10 SEC to adjust in speed to: %d !!!!" % speed)
                else:
                    logging.error(
                        "!!!!!   Pump's Speed successfully adjusted AFTER SLEEP 10 SEC to: %d !!!!!!!!!" % speed)

        except Exception as e:
            logging.error(f"Something is wrong with adjustment type is wrong: {str(e)}. The device is {device}")

    def adjust_min_pump_speed(self, pumps):
        for device in pumps:
            if not device.get_device_type == 'PUMP':
                continue
            device.update_extra("min_speed", self.pump_auto.setup_minimum_pump_speed(device))
