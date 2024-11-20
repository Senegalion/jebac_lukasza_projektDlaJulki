import time

def go_around(self):
        global _running
        "--direction initialization--"
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
        "--avoidance loop--"
        print(chosen_direction)

        while _running:
            self.rotate(chosen_direction, 90)
            self.motor_mov("w")

            while not self.lidar_thread.check_safety(opposite_direction) and _running:
                time.sleep(0.1)
                pass
            
            self.motor_mov("x")
            self.rotate(opposite_direction, 90)
            self.motor_mov("w")

            while self.lidar_thread.check_safety("w") and _running:
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
            if _running:
                print("Go around recursive")
                go_around()