import socket
import time
import re

class Marker:
    def __init__(self, id, x, y, z, model_name, is_front):
        self.id = id
        self.is_front = is_front
        self.x = x
        self.y = y
        self.z = z
        self.model_name = model_name
    
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
        slope1 = (markers_list[0].y - markers_list[1].y) * (markers_list[0].x - markers_list[2].x)
        slope2 = (markers_list[0].y - markers_list[2].y) * (markers_list[0].x - markers_list[1].x)

        return slope1 == slope2

    def print(self):
        print("Model_name: {} | Marker id: {} | Points xyz: [{},{},{}]".format(self.model_name, self.id, self.x, self.y, self.z))

    def __str__(self):
        return "Model_name: {} | Marker id: {} | Points xyz: [{},{},{}]".format(self.model_name, self.id, self.x, self.y, self.z)


def parse_marker_string(marker_string):
    model_name = marker_string.split('$')[0].lstrip('#')
    marker_list = marker_string.split('#')[1:]  # Split the string by '#' and remove the empty first element
    markers = []
    for marker in marker_list:
        marker_info = marker.split('$')[1].split('[')
        id = int(marker_info[0])
        coords = marker_info[1].strip(']').split(',')
        x, y, z = map(float, coords)
        markers.append(Marker(id, x, y, z, model_name, False))

    if(markers[0].model_name == "Platform"):    
        markers.remove(min(markers, key = lambda x : x.z))
    
    return markers

def set_socket_server():
    HOST = '192.168.31.103'   
    PORT = 9999
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    return s

def recv_data(socket_server):
    header = socket_server.recv(10).decode()
    message_length = int(header)
    data = socket_server.recv(message_length).decode()
    #return data
    markers_list = parse_marker_string(data)
    return markers_list

def main():    
    platfrom_markers = []
    target_markers = []
    server = set_socket_server()
    while True:
        print("___________________________")
        markers_list = recv_data(server)

        if markers_list[0].model_name == "Platform":
            platfrom_markers = markers_list
        else:
            target_markers = markers_list

        for marker in markers_list:
            print(marker)
        print("___________________________")
        
    # markers_list = [Marker(0, -1.0, 0.41, 0.93, "Targer", False), Marker(1, 1.0, -0.41, -0.93, "Targer", False),
    #                 Marker(2, 0, 1, 0, "Targer", False)]
    
    # print(Marker.colinear(markers_list))


if __name__ == "__main__":
    main()