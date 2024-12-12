import socket
import time
import re
import string


class Marker:
    def __init__(self, id, x, y, z):
        self.id = id
        self.x = x
        self.y = y
        self.z = z

    def distanceSquared(self, marker):
        return (self.x - marker.x) ** 2 + (self.z - marker.z) ** 2

    def center(markers_list):
        center_coordinates = [0, 0, 0]
        for markers in markers_list:
            center_coordinates[0] = center_coordinates[0] + markers.x
            center_coordinates[1] = center_coordinates[1] + markers.y
            center_coordinates[2] = center_coordinates[2] + markers.z

        for i in range(len(center_coordinates)):
            center_coordinates[i] = center_coordinates[i] / len(markers_list)

        return center_coordinates

    def colinear(markers_list):
        slope1 = (markers_list[0].z - markers_list[1].z) * (markers_list[0].x - markers_list[2].x)
        slope2 = (markers_list[0].z - markers_list[2].z) * (markers_list[0].x - markers_list[1].x)
        print(slope1)
        print(slope2)

        return abs(slope1 - slope2) < 0.01

    def print(self):
        print("Model_name: | Marker id: {} | Points xyz: [{},{},{}] | Is front: {}".format(self.id, self.x, self.y,
                                                                                           self.z))

    def __str__(self):
        return "Model_name: | Marker id: {} | Points xyz: [{},{},{}] | Is front: {}".format(self.id, self.x, self.y,
                                                                                            self.z)


def get_static_marker_data():
    static_data = [
        (10, 0.1, 1.5, 0.3), (9, 0.2, 1.6, 0.4), (11, 0.3, 1.4, 0.2),
        (19, 0.5, 1.2, 0.5), (5, 0.1, 1.1, 0.1), (12, 0.3, 1.3, 0.6),
        (20, 0.4, 1.2, 0.7), (8, 0.2, 1.0, 0.8), (15, 0.4, 1.0, 0.9),
        (21, 0.6, 1.1, 1.0), (6, 0.7, 1.0, 0.3), (13, 0.3, 0.9, 0.4),
        (14, 0.2, 0.8, 0.5), (22, 0.8, 0.7, 0.6), (7, 0.9, 1.0, 0.7),
        (3, 0.5, 0.9, 0.2), (4, 0.6, 0.9, 0.4), (2, 0.7, 1.2, 0.8),
        (1, 0.8, 1.1, 0.9), (24, 0.9, 1.3, 1.0), (17, 0.8, 1.4, 1.1),
        (23, 0.9, 1.5, 1.2), (16, 0.7, 1.5, 1.3), (25, 0.6, 1.6, 1.4),
        (18, 0.5, 1.7, 1.5), (26, 0.4, 1.8, 1.6), (34, 0.3, 1.9, 1.7),
        (35, 0.2, 2.0, 1.8), (27, 0.1, 2.1, 1.9), (36, 0.0, 2.2, 2.0),
        (28, -0.1, 2.3, 2.1), (40, -0.2, 2.4, 2.2), (37, -0.3, 2.5, 2.3),
        (41, -0.4, 2.6, 2.4), (38, -0.5, 2.7, 2.5), (39, -0.6, 2.8, 2.6),
        (31, -0.7, 2.9, 2.7), (33, -0.8, 3.0, 2.8), (30, -0.9, 3.1, 2.9),
        (29, -1.0, 3.2, 3.0), (32, -1.1, 3.3, 3.1)
    ]
    markers = [Marker(id, x, y, z) for id, x, y, z in static_data]
    return markers


def parse_marker_string(marker_string):
    marker_list = marker_string.split('#')[1:]  # Split the string by '#' and remove the empty first element
    markers = []
    for marker in marker_list:
        marker_info = marker.split('$')[1].split('[')
        try:
            id = int(marker_info[0])
            coords = marker_info[1][:-1].strip(']').split(',')
            x, y, z = map(float, coords)
        except:
            print("Error parsing marker string: {}".format(marker))
            continue
        markers.append(Marker(id, x, y, z))

    return markers


def set_socket_server():
    HOST = '192.168.31.2'  # The server's hostname or IP address
    PORT = 9999

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    return s


def recv_data(socket_server):
    header = socket_server.recv(10).decode()
    # print("cos")
    # print(header)
    message_length = int(header)
    data = socket_server.recv(message_length).decode()
    #print(data)
    markers_list = parse_marker_string(data)
    return markers_list


def main():
    server = set_socket_server()
    while True:
        markers_list = recv_data(server)
        marker_number = 1

        # Create a list of tuples with marker data and corresponding marker_number
        marker_data = [
            (marker.x, marker.y, marker.z, marker_number)
            for marker_number, marker in enumerate(markers_list, start=1)
        ]

        # Sort the list by marker.y in descending order
        sorted_marker_data = sorted(marker_data, key=lambda m: m[1], reverse=True)

        # Group and sort markers within the 0.03 margin
        grouped_sorted_markers = []
        visited = [False] * len(sorted_marker_data)  # Keep track of visited markers

        for i, current_marker in enumerate(sorted_marker_data):
            if visited[i]:
                continue

            group = [current_marker]
            visited[i] = True

            for j, other_marker in enumerate(sorted_marker_data):
                if i != j and not visited[j]:
                    if abs(current_marker[1] - other_marker[1]) <= 0.03:
                        group.append(other_marker)
                        visited[j] = True

            # Sort the group by x in descending order
            group.sort(key=lambda m: m[0], reverse=True)
            grouped_sorted_markers.extend(group)

        # Print the final grouped and sorted markers
        for data in grouped_sorted_markers:
            print(f"Marker Number: {data[3]} - x: {data[0]}, y: {data[1]}, z: {data[2]}")


if __name__ == "__main__":
    main()
