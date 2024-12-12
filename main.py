import math
import time
import tkinter as tk
import numpy as np
import pandas as pd
from PIL import Image, ImageTk, ImageDraw
from PythonClient import set_socket_server, recv_data, Marker

ACCEPTABLE_TIME = 1
THRESHOLD_ANGLE_CHANGE = 1
THRESHOLD_CURVATURE_CHANGE = 1
THRESHOLD_DISTANCE_CHANGE = 5

last_alert_times = [time.time()] * 6
alert_states = [''] * 6
last_angles = [None] * 6
last_points = None

marker_mapping = {
    1: "Left Elbow", 2: "Left Front Hip", 3: "Right Back Hip", 4: "Left Back Hip",
    5: "Back Top", 6: "Back Right", 7: "Right Front Hip", 8: "Chest", 9: "Head Top",
    10: "Head Front", 11: "Head Side", 12: "Left Shoulder Top", 13: "Back Left",
    14: "Left Upper Arm High", 15: "Left Shoulder Back", 16: "Left Upper Back",
    17: "Left Upper Front", 18: "Left Lower Back", 19: "Right Shoulder Top",
    20: "Right Shoulder Back", 21: "Right Upper Arm High", 22: "Right Elbow",
    23: "Right Upper Back", 24: "Right Upper Front", 25: "Right Lower Back",
    26: "Left Front Knee", 27: "Left Side Knee", 28: "Left Shin", 29: "Left Foot Back Left",
    30: "Left Foot Back Right", 31: "Left Foot Front Right", 32: "Left Foot Front Left",
    33: "Left Foot Top", 34: "Right Front Knee", 35: "Right Side Knee", 36: "Right Shin",
    37: "Right Foot Back Right", 38: "Right Foot Back Left", 39: "Right Foot Front Left",
    40: "Right Foot Front Right", 41: "Right Foot Top"
}


image_window = tk.Tk()
image_window.title("Angle Monitoring System - Image")
image_window.geometry("500x500+100+100")

table_window = tk.Toplevel()
table_window.title("Angle Monitoring System - Table")
table_window.geometry("500x500+610+100")

image_path = "image.webp"
person_image = Image.open(image_path)
person_image = person_image.resize((400, 400))
person_photo = ImageTk.PhotoImage(person_image)
image_label = tk.Label(image_window, image=person_photo)
image_label.pack(padx=20, pady=20)

mapping_matrix = {
    "neck": [200, 60],
    "shoulder": [68, 134],
    "elbow": [105, 193],
    "hand": [173, 194],
    "hips": [82, 249],
    "knee": [209, 251],
    "heel": [186, 387],
    "toes": [245, 387],
    "table": [230, 180]
}

acceptable_ranges = [[90, 105], [90, 105], [75, 90], [90, 105], [0, 5], [60, 95]]


def highlight_points(image, points, color):
    draw = ImageDraw.Draw(image)
    for point in points:
        x, y = mapping_matrix[point]
        draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill=color)
    return image


def update_image(points_of_the_body, alert_states):
    global person_image, person_photo, image_label
    person_image = Image.open(image_path)
    person_image = person_image.resize((400, 400))

    if alert_states[0]:
        person_image = highlight_points(person_image, ["shoulder", "elbow", "hand"], 'red')
    if alert_states[1]:
        person_image = highlight_points(person_image, ["heel", "knee", "hips"], 'red')
    if alert_states[2]:
        person_image = highlight_points(person_image, ["toes", "heel", "knee"], 'red')
    if alert_states[3]:
        person_image = highlight_points(person_image, ["shoulder", "hips", "knee"], 'red')
    if alert_states[4]:
        draw = ImageDraw.Draw(person_image)
        draw.line((180, 190, 180, 230), fill='red', width=4)
    if alert_states[5]:
        draw = ImageDraw.Draw(person_image)
        draw.line((50, 100, 50, 280), fill='red', width=4)

    person_photo = ImageTk.PhotoImage(person_image)
    image_label.configure(image=person_photo)
    image_label.image = person_photo


def get_alert(value, acceptable_range, index):
    global last_alert_times, alert_states
    current_time = time.time()

    # curvature left
    if index == 4:
        if value < acceptable_range[0] or value > acceptable_range[1]:
            if current_time - last_alert_times[index] >= ACCEPTABLE_TIME:
                last_alert_times[index] = current_time
                alert_states[index] = '●'
            return alert_states[index]

    # curvature right
    elif index == 5:
        if value < acceptable_range[0] or value > acceptable_range[1]:
            if current_time - last_alert_times[index] >= ACCEPTABLE_TIME:
                last_alert_times[index] = current_time
                alert_states[index] = '●'
            return alert_states[index]

    if value < acceptable_range[0] or value > acceptable_range[1]:
        if current_time - last_alert_times[index] >= ACCEPTABLE_TIME:
            last_alert_times[index] = current_time
            alert_states[index] = '●'
        return alert_states[index]
    else:
        alert_states[index] = ''
        return ''


def calculate_angle(a, b, c):
    AB = np.array([b.x - a.x, b.y - a.y, b.z - a.z])
    BC = np.array([c.x - b.x, c.y - b.y, c.z - b.z])

    dot_product = np.dot(AB, BC)
    mag_AB = np.linalg.norm(AB)
    mag_BC = np.linalg.norm(BC)

    cos_angle = dot_product / (mag_AB * mag_BC)

    cos_angle = max(-1, min(1, cos_angle))

    angle_rad = np.arccos(cos_angle)
    angle_deg = math.degrees(angle_rad)

    return angle_deg


def compute_elbow_angles(markers_list):
    left_shoulder_top_marker = markers_list[12 - 1]
    left_upper_arm_high_marker = markers_list[14 - 1]
    left_elbow_marker = markers_list[1 - 1]

    right_shoulder_top_marker = markers_list[19 - 1]
    right_upper_arm_high_marker = markers_list[21 - 1]
    right_elbow_marker = markers_list[22 - 1]

    left_elbow_angle = calculate_angle(left_shoulder_top_marker, left_upper_arm_high_marker, left_elbow_marker)
    right_elbow_angle = calculate_angle(right_shoulder_top_marker, right_upper_arm_high_marker, right_elbow_marker)

    return left_elbow_angle, right_elbow_angle


def compute_hip_angles(markers_list):
    left_shoulder_top_marker = markers_list[12 - 1]
    left_front_hip_marker = markers_list[2 - 1]
    left_front_knee_marker = markers_list[26 - 1]

    right_shoulder_top_marker = markers_list[19 - 1]
    right_front_hip_marker = markers_list[7 - 1]
    right_front_knee_marker = markers_list[34 - 1]

    left_hip_angle = calculate_angle(left_shoulder_top_marker, left_front_hip_marker, left_front_knee_marker)
    right_hip_angle = calculate_angle(right_shoulder_top_marker, right_front_hip_marker, right_front_knee_marker)

    return left_hip_angle, right_hip_angle


def compute_knee_angles(markers_list):
    left_front_hip_marker = markers_list[2 - 1]
    left_front_knee_marker = markers_list[26 - 1]
    left_foot_back_right = markers_list[30 - 1]

    right_front_hip_marker = markers_list[7 - 1]
    right_front_knee_marker = markers_list[34 - 1]
    right_foot_back_left = markers_list[38 - 1]

    left_knee_angle = calculate_angle(left_front_hip_marker, left_front_knee_marker, left_foot_back_right)

    right_knee_angle = calculate_angle(right_front_hip_marker, right_front_knee_marker, right_foot_back_left)

    return left_knee_angle, right_knee_angle


def compute_ankle_angles(markers_list):
    left_front_knee_marker = markers_list[26 - 1]
    left_foot_back_right_marker = markers_list[30 - 1]
    left_foot_top_marker = markers_list[33 - 1]

    right_front_knee_marker = markers_list[34 - 1]
    right_foot_back_left_marker = markers_list[38 - 1]
    right_foot_top_marker = markers_list[41 - 1]

    left_ankle_angle = calculate_angle(left_front_knee_marker, left_foot_back_right_marker, left_foot_top_marker)
    right_ankle_angle = calculate_angle(right_front_knee_marker, right_foot_back_left_marker, right_foot_top_marker)

    return left_ankle_angle, right_ankle_angle


def calculate_curvature(left_shoulder, left_hip, right_shoulder, right_hip):
    left_vector = np.array([left_shoulder.x, left_shoulder.y, left_shoulder.z]) - np.array(
        [left_hip.x, left_hip.y, left_hip.z])
    left_curvature = np.linalg.norm(left_vector)

    right_vector = np.array([right_shoulder.x, right_shoulder.y, right_shoulder.z]) - np.array(
        [right_hip.x, right_hip.y, right_hip.z])
    right_curvature = np.linalg.norm(right_vector)

    return left_curvature, right_curvature


def calculate_angles(markers_list):
    angles = [
        compute_elbow_angles(markers_list),
        compute_knee_angles(markers_list),
        compute_ankle_angles(markers_list),
        compute_hip_angles(markers_list)
    ]

    left_shoulder = markers_list[12 - 1]
    left_hip = markers_list[2 - 1]
    right_shoulder = markers_list[19 - 1]
    right_hip = markers_list[7 - 1]

    left_curvature, right_curvature = calculate_curvature(left_shoulder, left_hip, right_shoulder, right_hip)

    angles.append(left_curvature)
    angles.append(right_curvature)

    return angles


def filter_angles(angles, last_angles):
    filtered_angles = []
    for new, last in zip(angles, last_angles):
        if abs(new - last) > THRESHOLD_ANGLE_CHANGE:
            filtered_angles.append(new)
        else:
            filtered_angles.append(last)
    return filtered_angles


def filter_curvature(angles, last_angles):
    filtered_angles = []
    for i, (new, last) in enumerate(zip(angles, last_angles)):
        if i == 8 or i == 9:  # Curvature
            if abs(new - last) > THRESHOLD_CURVATURE_CHANGE:
                filtered_angles.append(new)
            else:
                filtered_angles.append(last)
        else:
            filtered_angles.append(new)
    return filtered_angles


def filter_data(new_points):
    global last_points, THRESHOLD_DISTANCE_CHANGE
    if last_points is None:
        last_points = new_points
        return new_points

    filtered_points = []
    for last, new in zip(last_points, new_points):
        if np.linalg.norm(np.array(new) - np.array(last)) > THRESHOLD_DISTANCE_CHANGE:
            filtered_points.append(new)
        else:
            filtered_points.append(last)

    last_points = filtered_points
    return filtered_points


def visualize_table(points_used_to_calculate_angles, acceptable_ranges_of_the_points):
    global last_angles, THRESHOLD_ANGLE_CHANGE

    filtered_points = filter_data(points_used_to_calculate_angles)
    angles = calculate_angles(filtered_points)

    if last_angles is None or None in last_angles:
        last_angles = angles

    # Filter angles to only show significant changes
    filtered_angles = filter_angles(angles, last_angles)
    filtered_angles = filter_curvature(filtered_angles, last_angles)

    data = {
        'Nazwa': ['Left Elbow Angle',
                  'Right Elbow Angle',
                  'Left Hip Angle',
                  'Right Hip Angle',
                  'Left Knee Angle',
                  'Right Knee Angle',
                  'Left Ankle Angle',
                  'Right Ankle Angle',
                  'Left Curvature',
                  'Right Curvature'],
        'Values': filtered_angles,
        'Acceptable range': acceptable_ranges_of_the_points,
        'Alert': [get_alert(value, range_, i) for i, (value, range_) in
                  enumerate(zip(filtered_angles, acceptable_ranges_of_the_points))]
    }

    last_angles = angles

    df = pd.DataFrame(data)

    text_widget.delete('1.0', tk.END)
    text_widget.insert(tk.END, df.to_string(index=False))

    update_image(filtered_points, alert_states)


def update_from_optitrack():
    markers = recv_data(server)
    new_markers = [Marker(marker.id, marker.x, marker.y, marker.z) for marker in markers]
    visualize_table(new_markers, acceptable_ranges)
    image_window.after(50, update_from_optitrack)


if __name__ == '__main__':
    server = set_socket_server()

    text_widget = tk.Text(table_window, height=30, width=50)
    text_widget.pack(padx=20, pady=20)

    update_from_optitrack()

    image_window.mainloop()