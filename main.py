import time
import tkinter as tk
import numpy as np
import pandas as pd
from PIL import Image, ImageTk, ImageDraw
import PythonClient

ACCEPTABLE_TIME = 1
THRESHOLD_ANGLE_CHANGE = 1
THRESHOLD_CURVATURE_CHANGE = 1
THRESHOLD_DELTA_H_CHANGE = 2
THRESHOLD_DISTANCE_CHANGE = 5

last_alert_times = [time.time()] * 6
alert_states = [''] * 6
last_angles = [None] * 6
last_points = None
use_simulated_data = True

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

points = [
    [0, 0, 95],  # neck
    [0, 0, 85],  # shoulder
    [10, 0, 60],  # elbow
    [50, 0, 65],  # hand
    [0, 0, 40],  # hips
    [50, 0, 40],  # knee
    [50, 0, 0],  # heel
    [75, 0, 56],  # toes
    [30, 0, 60]  # table
]

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
    if value < acceptable_range[0] or value > acceptable_range[1]:
        if current_time - last_alert_times[index] >= ACCEPTABLE_TIME:
            last_alert_times[index] = current_time
            alert_states[index] = '●'
        return alert_states[index]
    else:
        alert_states[index] = ''
        return ''


def calculate_alpha1(points_of_the_body):
    shoulder = np.array(points_of_the_body[1])
    elbow = np.array(points_of_the_body[2])
    hand = np.array(points_of_the_body[3])

    vector_elbow_shoulder = shoulder - elbow
    vector_elbow_hand = hand - elbow

    cosine_alpha1 = np.dot(vector_elbow_shoulder, vector_elbow_hand) / (
            np.linalg.norm(vector_elbow_shoulder) * np.linalg.norm(vector_elbow_hand))

    alpha1 = np.arccos(cosine_alpha1) * (180 / np.pi)

    return round(alpha1, 2)


def calculate_alpha2(points_of_the_body):
    heel = np.array(points_of_the_body[6])
    knee = np.array(points_of_the_body[5])
    hips = np.array(points_of_the_body[4])

    vector_knee_heel = heel - knee
    vector_knee_hips = hips - knee

    cosine_alpha2 = np.dot(vector_knee_heel, vector_knee_hips) / (
            np.linalg.norm(vector_knee_heel) * np.linalg.norm(vector_knee_hips))

    alpha2 = np.arccos(cosine_alpha2) * (180 / np.pi)

    return round(alpha2, 2)


def calculate_alpha3(points_of_the_body):
    knee = np.array(points_of_the_body[5])
    heel = np.array(points_of_the_body[6])
    toes = np.array(points_of_the_body[7])

    vector_heel_knee = knee - heel
    vector_heel_toes = toes - heel

    cosine_alpha3 = np.dot(vector_heel_knee, vector_heel_toes) / (
            np.linalg.norm(vector_heel_knee) * np.linalg.norm(vector_heel_toes))

    alpha3 = np.arccos(cosine_alpha3) * (180 / np.pi)

    return round(alpha3, 2)


def calculate_alpha4(points_of_the_body):
    shoulder = np.array(points_of_the_body[1])
    hips = np.array(points_of_the_body[4])
    knee = np.array(points_of_the_body[5])

    vector_hips_shoulder = shoulder - hips
    vector_hips_knee = knee - hips

    cosine_alpha4 = np.dot(vector_hips_shoulder, vector_hips_knee) / (
            np.linalg.norm(vector_hips_shoulder) * np.linalg.norm(vector_hips_knee))

    alpha4 = np.arccos(cosine_alpha4) * (180 / np.pi)

    return round(alpha4, 2)


def calculate_curvature(points_of_the_body):
    neck = np.array(points_of_the_body[0])
    shoulder = np.array(points_of_the_body[1])
    hips = np.array(points_of_the_body[4])

    vector_shoulder_neck = neck - shoulder
    vector_shoulder_hips = hips - shoulder

    cosine_curvature = np.dot(vector_shoulder_neck, vector_shoulder_hips) / (
            np.linalg.norm(vector_shoulder_neck) * np.linalg.norm(vector_shoulder_hips))

    curvature = np.arccos(cosine_curvature) * (180 / np.pi)

    return round(curvature, 2)


def calculate_angles(points_of_the_body):
    angles = [
        calculate_alpha1(points_of_the_body),
        calculate_alpha2(points_of_the_body),
        calculate_alpha3(points_of_the_body),
        calculate_alpha4(points_of_the_body),
        points_of_the_body[8][2] - points_of_the_body[2][2],  # Δh in cm
        calculate_curvature(points_of_the_body)
    ]
    return angles


def filter_angles(angles, last_angles):
    filtered_angles = []
    for new, last in zip(angles, last_angles):
        if abs(new - last) > THRESHOLD_ANGLE_CHANGE:
            filtered_angles.append(new)
        else:
            filtered_angles.append(last)
    return filtered_angles


def filter_delta_h_and_curvature(angles, last_angles):
    filtered_angles = []
    for i, (new, last) in enumerate(zip(angles, last_angles)):
        if i == 4:  # Δh
            if abs(new - last) > THRESHOLD_DELTA_H_CHANGE:
                filtered_angles.append(new)
            else:
                filtered_angles.append(last)
        elif i == 5:  # Curvature
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


def fetch_optitrack_data():
    # collected_points = optitrack_api.get_points()
    # return np.array(collected_points)
    pass


def simulate_optitrack_data():
    new_points = np.array(points) + np.random.normal(0, 1, np.array(points).shape)
    visualize_table(new_points, acceptable_ranges)
    image_window.after(50, simulate_optitrack_data)


def update_from_optitrack():
    new_points = fetch_optitrack_data()
    visualize_table(new_points, acceptable_ranges)
    image_window.after(50, update_from_optitrack)


def visualize_table(points_used_to_calculate_angles, acceptable_ranges_of_the_points):
    global last_angles, THRESHOLD_ANGLE_CHANGE

    filtered_points = filter_data(points_used_to_calculate_angles)
    angles = calculate_angles(filtered_points)

    if last_angles is None or None in last_angles:
        last_angles = angles

    # Filter angles to only show significant changes
    filtered_angles = filter_angles(angles, last_angles)
    filtered_angles = filter_delta_h_and_curvature(filtered_angles, last_angles)

    data = {
        'Nazwa': ['α1', 'α2', 'α3', 'α4', 'Δh', 'krzywizna'],
        'Wartości': filtered_angles,
        'Akceptowalny zakres': acceptable_ranges_of_the_points,
        'Alert': [get_alert(value, range_, i) for i, (value, range_) in
                  enumerate(zip(filtered_angles, acceptable_ranges_of_the_points))]
    }

    last_angles = angles

    df = pd.DataFrame(data)

    text_widget.delete('1.0', tk.END)
    text_widget.insert(tk.END, df.to_string(index=False))

    update_image(filtered_points, alert_states)


text_widget = tk.Text(table_window, height=30, width=50)
text_widget.pack(padx=20, pady=20)

if use_simulated_data:
    simulate_optitrack_data()
else:
    update_from_optitrack()

image_window.mainloop()
