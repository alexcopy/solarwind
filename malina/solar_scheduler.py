import sched
import time


class MyClass:
    def __init__(self):
        self.scheduler = sched.scheduler(time.time, time.sleep)

    def run_read_vals(self):
        self.send_avg_data()
        self.update_devs_stats()
        self.send_stats_api()
        self.load_checks()

    def schedule_task(self, task, interval):
        self.scheduler.enter(interval, 1, task)

    def start_scheduler(self):
        while True:
            self.scheduler.run()
            self.scheduler = sched.scheduler(time.time, time.sleep)

    def send_avg_data(self):
        inv_status = self.new_devices.get_devices_by_name("inverter")[0].get_status('switch_1')
        self.send_data.send_avg_data(self.filo_fifo, inv_status)
        # self.send_data.send_weather(self.automation.local_weather)

    def update_devs_stats(self):
        # Your code for updating devices statistics
        pass

    def send_stats_api(self):
        # Your code for sending statistics to API
        pass

    def load_checks(self):
        # Your code for loading checks
        pass

# Usage example
# my_obj = MyClass()
# my_obj.schedule_task(my_obj.send_avg_data, interval=1200)
# my_obj.schedule_task(my_obj.update_devs_stats, interval=300)
# my_obj.schedule_task(my_obj.send_stats_api, interval=360)
# my_obj.schedule_task(my_obj.load_checks, interval=30)
#
# my_obj.start_scheduler()
