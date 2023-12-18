import logging

from colorama import Style, Fore

from malina.LIB.PowerDevice import PowerDevice


class PowerDeviceManager:
    def __init__(self, device_names):
        if len(device_names):
            for name in device_names:
                self.add_device(name)
        else:
            self.devices = []  # Список устройств, управляемых менеджером

    def add_device(self, device_name):
        self.devices.append(PowerDevice(name=device_name))

    def find_device_by_name(self, device_name):
        return [device for device in self.devices if device.name == device_name]

    def sort_devices_by_power(self):
        return sorted(self.devices, key=lambda device: device.get_mean_total(), reverse=True)

    def display_all_devices(self):
        sorted_devices = self.sort_devices_by_power()
        print("All Devices:")
        for index, device in enumerate(sorted_devices, start=1):
            device_string = f"{index}. Name: {device.name}, Mean Power: {device.get_mean_total()} kW"
            print(device_string)
            logging.info(device_string)

    def send_data_to_servers(self):
        for device in self.devices:
            device.send_data_to_server()

    def update_ten_min_power_value(self, device_name, power_value):
        for device in self.devices:
            if device.name == device_name:
                device.add_power_value(power_value)
                return True
        return False  # Device not found with the given name

    def remove_device_by_name(self, device_name):
        devices_to_remove = [device for device in self.devices if device.name == device_name]
        for device in devices_to_remove:
            self.devices.remove(device)

    def print_all_devices_logs(self):
        print(f"{Fore.CYAN}Logs for all Power Devices{Style.RESET_ALL}")
        for device in self.devices:
            device.print_device_logs()
