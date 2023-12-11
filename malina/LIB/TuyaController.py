import datetime
import logging
import time

from colorama import Fore, Style

from malina.LIB.FiloFifo import FiloFifo
from malina.LIB.TuyaAuthorisation import TuyaAuthorisation
from malina.LIB.PondPumpAuto import PondPumpAuto
from malina.LIB.Device import Device
from malina.LIB.SendApiData import SendApiData


class TuyaController():
    def __init__(self, authorisation: TuyaAuthorisation):
        self.authorisation = authorisation
        self.pump_auto = PondPumpAuto()

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

    def switch_all_on_soft(self, devices, inver_volts):
        inverter = next((d for d in devices if d.get_name() == "inverter"), None)
        inv_is_ready = inverter.is_device_ready_to_switch_on(inver_volts)

        if inverter is None:
            logging.info("!!!!!  Inverter not found in the Devices LIST  !!!!!!!!")
            return

        if not inverter.is_device_on and not inv_is_ready:
            logging.info("Inverter is not switched on AND Not Ready so continue....")
            logging.info(" ------ Inverter is not ready to be switched ON at the provided voltage.")
            return

        # this code is done to prevent devices to be started right after INV switched on:
        if inv_is_ready and not inverter.is_device_on:
            inv_sw_on = self.switch_on_device(inverter)
            if inv_sw_on:
                for device in devices:
                    logging.info(f"{Fore.CYAN} Device needs to be postponed with it's DELTA: {device.get_name()}{Style.RESET_ALL}")
                    device.device_switched()
            else:
                logging.info(f"{Fore.CYAN} CANNOT SWITCH INVERTER ON, PLS CHECK {Style.RESET_ALL}")

        for device in devices:
            if device.is_device_ready_to_switch_on(inver_volts):
                logging.info(
                    f"Device is ready to switch ON dev name: {device.get_name()} is_device_on: {device.is_device_on} last switch: {device.switched_delta} secs ago")
                self.switch_on_device(device)
                time.sleep(2)

    def switch_all_off_soft(self, devices, inver_volts):
        inverter = next((d for d in devices if d.get_name() == "inverter"), None)
        if inverter is None:
            logging.info("!!!!!   Inverter not found in the Devices LIST    !!!!!!!!")
            return

        for device in devices:
            if device.get_name() == "inverter":
                # if device is inverter we should be going through the normal process
                to_switch_off = device.is_device_ready_to_switch_off(inver_volts, True)
            else:
                to_switch_off = device.is_device_ready_to_switch_off(inver_volts, inverter.is_device_on)

            if to_switch_off:
                logging.info(
                    f"Device is ready to switch OFF dev name: {device.name} voltage: {device.voltage} last switch: {device.switched_delta} secs ago")
                self.switch_off_device(device)
                time.sleep(2)

    def switch_all_on_hard(self, devices):
        for device in devices:
            if device.is_device_on:
                logging.info(
                    f"switch_all_on_hard: The {device.get_name()} is already ON: no actions is required status {device.is_device_on}")
                continue
            self.switch_on_device(device)
            time.sleep(5)

    def switch_all_off_hard(self, devices):
        for device in devices:
            self.switch_off_device(device)
            time.sleep(5)

    def update_devices_status(self, devices):
        device_ids = [device.get_id() for device in devices]
        try:
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
        except ConnectionError as ce:
            logging.error(f" Fail to get statuses for devices {str(ce)}")
        except Exception as e:
            logging.error(f" General Exception with get statuses {str(e)}")

    def select_dev_by_id(self, devices, lookup_id):
        for device in devices:
            dev_id = device.get_id()
            if lookup_id == dev_id:
                return device
        return None

    # minimum should be inverter and pump as params for devices
    def switch_on_off_all_devices(self, filo_fifo: FiloFifo, devices):
        pump_mode = next((int(d.get_status("mode")) for d in devices if d.get_device_type == "PUMP"), 6)
        inver_volts = filo_fifo.get_inverter_voltage()
        inverter = next((d for d in devices if d.get_name() == "inverter"), None)

        if inverter is None:
            logging.info("!!!!! in switch_on_off_all_devices the Inverter not found in the Devices LIST  !!!!!!!!")
            return

        if not pump_mode == 6:
            logging.error(f"Cannot SWITCH ALL ON/OFF ALL DEVICES as PUMP mode is in predefined mode: {pump_mode}")
            # only inverter could be switched off in mode not 6
            return self.switch_all_off_soft([inverter], inver_volts)

        # switching ON only before 18:30 no sense to do it after 18:30
        elif TuyaController.is_before_1830:
            self.switch_all_on_soft(devices, inver_volts)

        elif not TuyaController.is_before_1830:
            logging.info("----- switch_on of all_devices including Inverter isn't possible after 18:30 ")

        self.switch_all_off_soft(devices, inver_volts)

    def adjust_devices_speed(self, device, inv_status, filo_fifo):
        if int(device.get_status("mode")) == 6:
            logging.debug(f"Adjust device  speed: {device.get_name()}")
            self._adjust_pump_power(device=device, inv_status=inv_status, filo_fifo=filo_fifo)
        elif not int(device.get_status("mode")) == 6:
            logging.info(f"Pump working mode= {device.get_status('mode')}  so no adjustments could be done ")
        else:
            logging.debug(
                f"device {device.name} is not ready yet the status is: {device.get_status()}")

    def _adjust_pump_power(self, device: Device, inv_status, filo_fifo):
        try:
            inver_volts = filo_fifo.get_inverter_voltage()
            pump_curr_speed = device.get_status("P")
            chk_pump_speed = self.pump_auto.check_pump_speed(device)

            if not chk_pump_speed == pump_curr_speed:
                logging.debug(
                    f" Pump's Speed is needs to round up existing speed which is {pump_curr_speed} to a new speed is: {chk_pump_speed}")
                self.switch_device(device, chk_pump_speed)
                device.update_status({"P": chk_pump_speed})
                return True

            speed = self.pump_auto.pond_pump_adj(device, inv_status, inver_volts)
            logging.debug(
                f"The calculated speed is:{speed} and device {device.get_name()} speed_cur: {device.get_status('P')}")

            if pump_curr_speed == speed:
                logging.debug(" Pump's Speed is optimal : %d  -----so no adjustments needed !!!!!!!!!" % speed)
                return True

            switch_device = self.switch_device(device, speed)

            if switch_device:
                device.update_status({"P": speed})
                SendApiData().send_pump_stats(device, inv_status)
                logging.debug(
                    f"!!!!!   Pump's Speed successfully adjusted to: {speed} the new speed is: {device.get_status('P')}!!!!!!!!! ")
            else:
                time.sleep(10)
                switch_device = self.switch_device(device, speed)
                SendApiData().send_pump_stats(device, inv_status)
                if not switch_device:
                    logging.error(
                        "!!!!   Pump's Speed has failed after SLEEP 10 SEC to adjust in speed to: %d !!!!" % speed)
                else:
                    logging.debug(
                        "!!!!!   Pump's Speed successfully adjusted AFTER SLEEP 10 SEC to: %d !!!!!!!!!" % speed)

        except Exception as e:
            logging.error(f"Something is wrong with adjustment type is wrong: {str(e)}. The device is {device}")

    def adjust_min_pump_speed(self, pumps):
        for device in pumps:
            if not device.get_device_type == 'PUMP':
                continue
            device.update_extra("min_speed", self.pump_auto.setup_minimum_pump_speed(device))

    @staticmethod
    def is_before_1830():
        # Get the current time
        current_time = datetime.datetime.now().time()
        # Create a time object representing 18:30 (6:30 PM)
        time_1830 = datetime.time(18, 30)
        # Compare the current time with 18:30
        return current_time <= time_1830
