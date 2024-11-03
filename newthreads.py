import threading
import time
import serial
import time
from rplidar import RPLidar
import math
import PythonClient as PC
import copy
import logging
import numpy as np

logging.getLogger("rplidar").setLevel(logging.ERROR)


class LidarThread(threading.Thread):
    def __init__(self):
        super().__init__()

        self.safe_areas_ins = {
            "w" : True,
            "a" : True,
            "s" : True,
            "d" : True
        }

        self.safe_areas_out = {
            "w" : True,
            "a" : True,
            "s" : True,
            "d" : True
        }

        self.last_region = "w"

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
    
    def set_safety_flags(self, x, y):
        SAFEDST = 400

        if y >= -170 and y <= 170 and x < 0:
            if self.last_region != "w":
                self.safe_areas_out["d"] = self.safe_areas_ins["d"]
                self.safe_areas_ins["d"] = True
                self.last_region = "w"
            if not (x < -225 - SAFEDST):
                self.safe_areas_ins["w"] = False

        if x >= -240 and x <= 240 and y > 0:
            if self.last_region != "d":
                self.safe_areas_out["s"] = self.safe_areas_ins["s"]
                self.safe_areas_ins["s"] = True
                self.last_region = "d"
            if not (y > 158 + SAFEDST):
                self.safe_areas_ins["d"] = False

        if y >= -170 and y <= 170 and x > 0:
            if self.last_region != "s":
                self.safe_areas_out["a"] = self.safe_areas_ins["a"]
                self.safe_areas_ins["a"] = True
                self.last_region = "s"
            if not (x > 228 + SAFEDST):
                self.safe_areas_ins["s"] = False

        if x >= -240 and x <= 240 and y < 0:
            if self.last_region != "a":
                self.safe_areas_out["w"] = self.safe_areas_ins["w"]
                self.safe_areas_ins["w"] = True
                self.last_region = "a"
            if not (y < -158 - SAFEDST):
                self.safe_areas_ins["a"] = False

    def run(self):
        SAFEDST = 400
        iterator = self.lidar.iter_scans()

        while self.running:
            scan = next(iterator)
            for item in scan:
                angle = item[1]
                if not self.usefull_angle(angle):
                    continue
                r = item[2]
                y = -r*math.sin(math.radians(angle))
                x = r*math.cos(math.radians(angle))
                
                self.set_safety_flags(x, y)

                # if y >= -170 and y <= 170 and x < 0:
                #     self.safe_w = (x < -225 - SAFEDST)
                # if x >= -240 and x <= 240 and y > 0:
                #     self.safe_d =  (y > 158 + SAFEDST)
                # if y >= -170 and y <= 170 and x > 0:
                #     self.safe_s = (x > 228 + SAFEDST)
                # if x >= -240 and x <= 240 and y < 0:
                #     self.safe_a = (y < -158 - SAFEDST)
                # print(self.safe_w, self.safe_d, self.safe_s, self.safe_a)
                
        self.lidar.stop()
        self.lidar.disconnect()
        print("lidar_stop")

    def check_safety(self, direction):
        if direction in ["w", "s", "a", "d"]:
            return self.safe_areas_out[direction]
        return True
    
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
            if markers_list is None:
                continue
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
            if self.lidar_thread.check_safety(direction = direction) == False:
                direction = "x"
                self.input_thread.command = "x"
                self.motor_mov(direction)

            if command == "x" and direction != "x":
                direction = "x"
                self.input_thread.command = "x"
                self.motor_mov("x")
            if command == "b":
                print('finished')
                break
            if command == "t":
                self.goto_target()
                direction = "x"
                self.input_thread.command = "x"
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
            print("command x")
        time.sleep(1)  # 2?

    def go_around(self):
        print("is in go_around")
        saw = False
        if self.lidar_thread.check_safety("a"):
            chosen_direction = "a"
            opposite_direction = "d"
        elif self.lidar_thread.check_safety("d"):
            chosen_direction = "d"
            opposite_direction = "a"
        else:
            print("HELP")
            return
        print(chosen_direction)
        while self.lidar_thread.check_safety(chosen_direction):
            self.motor_mov(chosen_direction)
            while not self.lidar_thread.check_safety("w"):
                time.sleep(0.1)
                pass
            self.motor_mov("x")
            print("x")
            time.sleep(1)
            self.motor_mov("w")
            print("w")
            while self.lidar_thread.check_safety("w"):
                
                if not self.lidar_thread.check_safety(opposite_direction):
                    saw = True
                    print(f"saw + {saw}")
                if self.lidar_thread.check_safety(opposite_direction) and saw == True:
                    self.motor_mov("x")
                    print("x")
                    print("goto_target again")
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
                if not self.lidar_thread.check_safety("w"):
                    self.go_around()
                    return
                print("colinear at start: going forward")
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
        
        print(command)
        while not PC.Marker.colinear([front, back, target]):
            if not self.lidar_thread.check_safety("w"):
                self.go_around()
                return
            front, back = self.front_back()
            time.sleep(0.1)
            

        self.motor_mov("x")
        time.sleep(0.3)
        self.motor_mov("w")
        print("w")
        while front.distanceSquared(target) > 0.04:
            front, back = self.front_back()
            if not self.lidar_thread.check_safety("w"):
                self.go_around()
                return
            time.sleep(0.1)
        self.motor_mov("x")
        print("finished goto_target")

    def goto_target_vector(self):
        if len(self.optitrack_thread.target_markers) == 0:
            print("no target ye")
            return
        target_list = PC.Marker.center(self.optitrack_thread.target_markers)
        target = PC.Marker(0, target_list[0], target_list[1], target_list[2], "Target", False)
        
        front, back = self.front_back()
        
        t_vector = np.array([target.x - front.x, target.y - front.y])
        p_vector = np.array([front.x - back.x, front.y - back.y])

        go_left = PC.Marker.target_to_left(p_vector, t_vector)
        ANGLE = 10  # degrees
        while(PC.Marker.angle(p_vector, t_vector) > ANGLE) and self.input_thread.command != "b":
            if go_left:
                self.motor_mov("q")
                print(f"go q")
            else:
                self.motor_mov("e")
                print("go e")
        print("angle corrected")

        tmp = False
        while PC.Marker.distanceSquared > 0.04 and self.input_thread.command != "b":
            if not self.check_safety("w"):
                self.motor_mov("x")
                time.sleep(1)
                self.go_around()
                return
            if not tmp:
                self.motor_mov("w")
                print("going forward")
        self.motor_mov("x")
        print("finished goto_target")




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
