import socket
import time
import re

class Marker:
    def __init__(self, id, x, y, z, model_name):
        self.id = id
        self.x = x
        self.y = y
        self.z = z
        self.model_name = model_name
    
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
        markers.append(Marker(id, x, y, z, model_name))
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
    markers_list = parse_marker_string(data)
    return markers_list

def main():    
    platfrom_markers = []
    target_markers = []
    server = set_socket_server()
    while True:
        print("___________________________")
        markers_list = recv_data(server)
        if len(markers_list) == 3:
            platfrom_markers = markers_list
        else:
            target_markers = markers_list
        for marker in markers_list:
            print(marker)
        print("___________________________")

if __name__ == "__main__":
    main()