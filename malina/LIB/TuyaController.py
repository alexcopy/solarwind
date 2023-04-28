import time


class TuyaController():
    def __init__(self, authorisation):
        self.authorisation = authorisation

    def is_device_ready(self, device_id):
        device = self.authorisation.device_manager.get_device_by_id(device_id)
        if device is None:
            return False
        if device.status.get('online') != 'True':
            return False
        if device.status.get('switch') is None:
            return False
        if device.status.get('switch') == 'false' and time.time() - device.last_control_time < 300:
            return False
        if device.status.get('switch') == 'true' and time.time() - device.last_control_time < 300:
            return False
        return True

    def switch_device(self, device_id, state):
        if not self.is_device_ready(device_id):
            return False
        device = self.authorisation.device_manager.get_device_by_id(device_id)
        if device is None:
            return False
        device.status.update({'switch': str(state)})
        success = self.authorisation.device_manager.send_commands([device])
        if success:
            return True
        else:
            return False

    def switch_on_device(self, device_id):
        return self.switch_device(device_id, True)

    def switch_off_device(self, device_id):
        return self.switch_device(device_id, False)

    def switch_all_on(self):
        devices = self.authorisation.device_manager.get_all_devices()
        for device in devices:
            if self.is_device_ready(device.id):
                self.switch_on_device(device.id)

    def switch_all_off(self):
        devices = self.authorisation.device_manager.get_all_devices()
        for device in devices:
            if self.is_device_ready(device.id):
                self.switch_off_device(device.id)




