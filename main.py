import serial
import time
from threading import Thread
from rplidar import RPLidar
import math

run = True
direction = "x"

serialcomm = serial.Serial('COM5', 19200)
serialcomm.timeout = 0  # 1

PORT_NAME = 'COM7'
SAFEDST = 600  # mm

def motor_mov(i):
    global direction
    i.strip()
    serialcomm.write(i.encode())
    if i == 'x':
        print("stopped")
    if i in ["x", "w", "s", "a", "d", "q", "e"]:
        direction = i
    time.sleep(1)  # 2


def input_movement():
    global run
    while run:
        i = input("Enter Input: ")
        if i == "b":
            run = False
            print('finished')
            break

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

    t1.start()
    t2.start()
    