import threading
import time
import serial
import time
from rplidar import RPLidar
import math
import PythonClient as PC
import copy
import logging

logging.getLogger("rplidar").setLevel(logging.ERROR)



class LidarThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.safe_w = True
        self.safe_s = True
        self.safe_a = True
        self.safe_d = True

        self.running = True
        self.PORT_NAME = 'COM7'
        self.lidar = RPLidar(self.PORT_NAME)
        
    # angles aligning with table legs return False.
    # all done experimentally!!! If table configuration changes, the function should too.
    def usefull_angle(self, angle):
        if angle >= 36 and angle <= 147 or \
            angle >= 156 and angle <= 207 or \
                angle >= 217 and angle <= 326 or \
                    angle >= 336 or angle <= 26:
            return True
        return False


    def run(self):
        SAFEDST = 400
        iterator = self.lidar.iter_scans(max_buf_meas=800)
        while self.running:
            scan = next(iterator)
            for item in scan:
                angle = item[1]
                if not self.usefull_angle(angle):
                    continue
                r = item[2]
                y = -r*math.sin(math.radians(angle))
                x = r*math.cos(math.radians(angle))
                
                if y >= -170 and y <= 170 and x < 0:
                    self.safe_w = (x < -225 - SAFEDST)
                if x >= -240 and x <= 240 and y > 0:
                    self.safe_d =  (y < 158 + SAFEDST)
                if y >= -170 and y <= 170 and x > 0:
                    self.safe_s = (x > 228 + SAFEDST)
                if x >= -240 and x <= 240 and y < 0:
                    self.safe_a = (y < -158 - SAFEDST)
        self.lidar.stop()
        self.lidar.disconnect()
        print("lidar_stop")

    
    
    def stop(self):
        self.running = False

class InputThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.running = True 
        self.command = "x"

    def run(self):
        while self.running:
            inp = input("Enter input> ")
            if inp in ["x", "w", "s", "a", "d", "q", "e", "t","b"]:
                self.command = inp
            else:
                print("Unknown command")
        print("input_stop")

    def stop(self):
        self.running = False

class OptTrackThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.running = True 
        self.target_markers = []
        self.platform_markers = []

    def run(self):
        server = PC.set_socket_server()
        while self.running:
            markers_list = PC.recv_data(server)
            
            if markers_list[0].model_name == "Platform":
                self.platform_markers = markers_list
            # elif (markers_list[0].model_name == "Target"):
            else:
                self.target_markers = markers_list
        print("optitrack_stop")



    def stop(self):
        self.running = False

class MainThread(threading.Thread):
    def __init__(self, lidar_thread, optitrack_thread, input_thread):
        super().__init__()
        self.lidar_thread = lidar_thread
        self.optitrack_thread = optitrack_thread
        self.input_thread = input_thread
        self.command = ""
        self.serialcomm = serial.Serial('COM5', 19200) # architecture based

    def run(self):
        direction = "x"
        self.serialcomm.timeout = 0  # 1?
        while True:
            command = self.input_thread.command
            if self.check_safety(direction) == False:
                direction = "x"
                self.motor_mov(direction)

            if command == "x" and direction != "x":
                direction = "x"
                self.motor_mov("x")
            if command == "b":
                print('finished')
                break
            if command == "t":
                self.goto_target()
                direction = "x"
                continue
            if command in ["w", "s", "a", "d", "e", "q"] and direction == "x" and self.check_safety(command):
                direction = command            
                self.motor_mov(direction)
            
        time.sleep(1)
        self.motor_mov("x")
        self.lidar_thread.stop()
        self.optitrack_thread.stop()
        self.input_thread.stop()
        self.serialcomm.close()
        print("main_stop")
        

    def check_safety(self, direction):
        if direction == "w":
            return self.lidar_thread.safe_w
        if direction == "s":
            return self.lidar_thread.safe_s
        if direction == "a":
            return self.lidar_thread.safe_a
        if direction == "d":
            return self.lidar_thread.safe_d
        return True
        

    def front_back(self):
        if self.optitrack_thread.platform_markers[0].is_front:
            front = copy.copy(self.optitrack_thread.platform_markers[0])
            back = copy.copy(self.optitrack_thread.platform_markers[1])
        else:
            front = copy.copy(self.optitrack_thread.platform_markers[1])
            back = copy.copy(self.optitrack_thread.platform_markers[0])
        return front, back

    def motor_mov(self, i):
        i.strip()
        self.serialcomm.write(i.encode())
        if i == 'x':
            print("stopped")
        time.sleep(1)  # 2?

    def go_around(self):
        saw = False
        if self.check_safety("a"):
            chosen_direction = "a"
            opposite_direction = "d"
        elif self.check_safety("d"):
            chosen_direction = "d"
            opposite_direction = "a"
        else:
            print("HELP")
            return
        while self.check_safety(chosen_direction):
            self.motor_mov(chosen_direction)
            while not self.check_safety("w"):
                time.sleep(0.1)
                pass
            self.motor_mov("x")
            time.sleep(1)
            self.motor_mov("w")
            while self.check_safety("w"):
                if not self.check_safety(opposite_direction):
                    saw = True
                if self.check_safety(opposite_direction) and saw == True:
                    self.motor_mov("x")
                    self.goto_target()
                    return
            self.motor_mov("x")
            saw = False

    def goto_target(self):
        if len(self.optitrack_thread.target_markers) == 0:
            print("no target ye")
            return
        target_list = PC.Marker.center(self.optitrack_thread.target_markers)
        target = PC.Marker(0, target_list[0], target_list[1], target_list[2], "Target", False)
        front, back = self.front_back()
        slope = (front.y - back.y) * (front.x - back.x)
        b = front.y - slope * front.x

        if PC.Marker.colinear([front, back, target]) and front.distanceSquared(target) < back.distanceSquared(target):
            self.motor_mov("w")
            while front.distanceSquared(target) > 0.04 and self.input_thread.command == "t":
                if not self.check_safety("w"):
                    self.go_around()
                    return
                print("going forward")
                front, back = self.front_back()
            self.motor_mov("x")
            return
        command = ""
        if front.x >= back.x:
            if target.z > slope * target.x + b:
                self.motor_mov("q")
                command = "going q"
            else:
                self.motor_mov("e")
                command = "going e"
        else:
            if target.z > slope * target.x + b:
                self.motor_mov("e")
                command = "going e"
            else:
                self.motor_mov("q")
                command = "going q"
        
        while not PC.Marker.colinear([front, back, target]):
            if not self.check_safety("w"):
                self.go_around()
                return
            front, back = self.front_back()
            print(command)
            time.sleep(0.1)
            

        self.motor_mov("x")
        time.sleep(0.3)
        self.motor_mov("w")
        while front.distanceSquared(target) > 0.04:
            front, back = self.front_back()
            print("going forward")
            time.sleep(0.1)
        self.motor_mov("x")
     


def main():
    lidar_thread = LidarThread()
    optitrack_thread = OptTrackThread()
    input_thread = InputThread()
    main_thread = MainThread(lidar_thread, optitrack_thread, input_thread)

    lidar_thread.start()
    optitrack_thread.start()
    input_thread.start()
    main_thread.start()

    lidar_thread.join()
    optitrack_thread.join()
    input_thread.join()
    main_thread.join()

if __name__ == "__main__":
    main()
