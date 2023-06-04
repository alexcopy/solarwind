import logging
import time

from malina.LIB.Device import Device


class TuyaController():
    def __init__(self, authorisation):
        self.authorisation = authorisation

    def switch_device(self, device: Device, state):
        try:
            api_sw = device.get_api_sw
            commands = {"devId": device.get_id(), "commands": [{"code": api_sw, "value": state}]}
            resp = self.authorisation.device_manager.send_commands(commands["devId"], commands['commands'])
            return bool(resp['success'])
        except  Exception as ex:
            logging.error("---------Problem in switch_device method and class TuyaController ---------")
            logging.error(ex)
            return False

    def _status(self, device_id):
        try:
            status = self.authorisation.device_manager.get_device_list_status([device_id])
            logging.debug(" ---------Getting device status for %s  ---------" % device_id)
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

    def switch_on_device(self, device):
        switched = self.switch_device(device, True)
        if switched:
            device.update_status({'switch_1': 1, "switch": 1})
        return switched

    def switch_off_device(self, device):
        return self.switch_device(device, False)

    def update_status(self, device):
        device_id = device.get_id()
        status = self._status(device_id)
        if status['success']:
            device.update_status({'switch_1': 0, "switch": 0})
        return status

    def switch_all_on_soft(self, devices):
        for device in devices:
            if device.is_device_ready_to_switch_on():
                self.switch_on_device(device.id)
                time.sleep(5)

    def switch_all_off_soft(self, devices):
        for device in devices:
            if device.is_device_ready():
                self.switch_off_device(device.id)
                time.sleep(5)

    def switch_all_on_hard(self, devices):
        for device in devices:
            self.switch_on_device(device.id)
            time.sleep(5)

    def switch_all_off_hard(self, devices):
        for device in devices:
            self.switch_off_device(device.id)
            time.sleep(5)

    def update_devices_status(self, devices):
        for device in devices:
            self.update_status(device)
            time.sleep(5)

    def switch_on_off_all_devices(self, devices):
        self.switch_all_on_soft(devices)
        self.switch_all_off_soft(devices)
