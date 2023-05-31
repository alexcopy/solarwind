import logging
import time

from malina.LIB.Device import Device


class TuyaController():
    def __init__(self, authorisation):
        self.authorisation = authorisation

    def switch_device(self, device: Device, state):
        api_sw = device.get_api_sw
        commands = {"devId": device.get_id(), "commands": [{"code": api_sw, "value": state}]}
        success = self.authorisation.device_manager.send_commands(commands["devId"], commands['commands'])
        if success:
            return True
        else:
            return False

    def _status(self, device_id):
        try:
            status = self.authorisation.device_manager.get_device_list_status([device_id])
            device_status = status['result'][0]['status']
            sw_status = {v['code']: v['value'] for v in device_status}
            if "switch_1" not in sw_status and "switch" in sw_status:
                sw_status.update({"switch_1": int(sw_status.get("switch")), "switch": int(sw_status.get("switch"))})
            extra_params = {
                'status': int(sw_status['switch_1']), 't': int(status['t'] / 1000), 'device_id': device_id}
            sw_status.update(extra_params)
            return sw_status

        except Exception as ex:
            logging.error("---------Problem in update_status---------")
            logging.error(ex)

    def switch_on_device(self, device):
        device_id = device.get_id()
        self.switch_device(device, True)
        status = self._status(device_id)
        return status

    def switch_off_device(self, device):
        device_id = device.get_id()
        self.switch_device(device, False)
        return self._status(device_id)

    def switch_all_on(self):
        devices = self.authorisation.device_manager.get_all_devices()
        for device in devices:
            if device.is_device_ready():
                self.switch_on_device(device.id)

    def switch_all_off(self):
        devices = self.authorisation.device_manager.get_all_devices()
        for device in devices:
            if device.is_device_ready():
                self.switch_off_device(device.id)
