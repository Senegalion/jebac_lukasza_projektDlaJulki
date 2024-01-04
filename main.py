import serial
import time
from threading import Thread
from rplidar import RPLidar
import math
import PythonClient as PC
import copy

run = True
direction = "x"

serialcomm = serial.Serial('COM5', 19200)
serialcomm.timeout = 0  # 1

PORT_NAME = 'COM7'
SAFEDST = 400  # mm
target_markers = []
platform_markers = []

def front_back():
    global platform_markers

    if platform_markers[0].is_front:
        front = copy.copy(platform_markers[0])
        back = copy.copy(platform_markers[1])
    else:
        front = copy.copy(platform_markers[1])
        back = copy.copy(platform_markers[0])
    return front, back

def motor_mov(i):
    global direction
    i.strip()
    serialcomm.write(i.encode())
    if i == 'x':
        print("stopped")
    if i in ["x", "w", "s", "a", "d", "q", "e", "t"]:
        direction = i
    time.sleep(1)  # 2

def get_position():
    global target_markers,  platform_markers

    server = PC.set_socket_server()
    while True:
        markers_list = PC.recv_data(server)
        
        if markers_list[0].model_name == "Platform":
            platform_markers = markers_list
        else:
            target_markers = markers_list

def goto_target():
    global target_markers, platform_markers
    if len(target_markers) == 0:
        print("no target ye")
        return
    target_list = PC.Marker.center(target_markers)
    target = PC.Marker(0, target_list[0], target_list[1], target_list[2], "Target", False)
    
    # if abs(target - PC.Marker.center(platform_markers)) < 0.6:
    #     motor_mov("x")
    #     return

    front, back = front_back()

    slope = (front.y - back.y) * (front.x - back.x)
    b = front.y - slope * front.x

    if PC.Marker.colinear([front, back, target]) and front.distanceSquared(target) < back.distanceSquared(target):
        motor_mov("w")
        while front.distanceSquared(target) > 0.04:
            print("going forward")
            front, back = front_back()
        motor_mov("x")
        return
    command = ""
    if front.x >= back.x:
        if target.z > slope * target.x + b:
            motor_mov("q")
            command = "going q"
        else:
            motor_mov("e")
            command = "going e"
    else:
        if target.z > slope * target.x + b:
            motor_mov("e")
            command = "going e"
        else:
            motor_mov("q")
            command = "going q"
    
    while not PC.Marker.colinear([front, back, target]):
        front, back = front_back()
        print(command)
        time.sleep(0.1)
        

    motor_mov("x")
    time.sleep(0.3)
    motor_mov("w")
    while front.distanceSquared(target) > 0.04:
        front, back = front_back()
        print("going forward")
        time.sleep(0.1)
    motor_mov("x")
    return

    # while 
        # if front.x >= back.x and not PC.Marker.colinear([front, back, target]):
        #     if target[1] > slope * target[0] + b:
        #         motor_mov("q")
        #     else:
        #         motor_mov("e")
        # elif front.x < back.x and not PC.Marker.colinear([front, back, target]):
        #     if target[1] > slope * target[0] + b:
        #         motor_mov("e")
        #     else:
        #         motor_mov("q")
        # else:
        #     motor_mov("w")        



def input_movement():
    global run, target_markers, platform_markers

    while run:

        print("___________________________")
        i = input("Enter Input: ")
        if i == "b":
            run = False
            print('finished')
            break
        if i == "t":
            goto_target()
            continue


        motor_mov(i)
    time.sleep(2)
    motor_mov("x")
    serialcomm.close()

# angles aligning with table legs return False
def usefull_angle(angle):
    if angle >= 36 and angle <= 147 or \
        angle >= 156 and angle <= 207 or \
            angle >= 217 and angle <= 326 or \
                angle >= 336 or angle <= 26:
        return True
    return False

def check_surroundings():
    global run, directions
    lidar = RPLidar(PORT_NAME)
    iterator = lidar.iter_scans()
    while(run):
        scan = next(iterator)    
        for item in scan:
            angle = item[1]
            if not usefull_angle(angle):
                continue
            r = item[2]
            y = -r*math.sin(math.radians(angle))
            x = r*math.cos(math.radians(angle))
            # if y >= -170 and y <= 170 and x < 0:
                # print(r, time.time())
            if x >= -240 and x <= 240 and y < 0 and direction == "a":
                if y > -158 - SAFEDST:
                    print("stop a", y)
                    motor_mov("x")
                    break
            if y >= -170 and y <= 170 and x < 0 and direction == "w":
                if x > -225 - SAFEDST:
                    print("stop w", x)
                    motor_mov("x")
                    break
            if x >= -240 and x <= 240 and y > 0 and direction == "d":
                if y < 158 + SAFEDST:
                    print("stop d", y)
                    motor_mov("x")
                    break
            if y >= -170 and y <= 170 and x > 0 and direction == "s":
                if x < 228 + SAFEDST:
                    print("stop s", x)
                    motor_mov("x")
                    break
    lidar.stop()
    lidar.disconnect()

if __name__ == '__main__':

    t1 = Thread(target=check_surroundings)
    t2 = Thread(target=input_movement)
    t3 = Thread(target=get_position)

    t1.start()
    t2.start()
    t3.start()
    