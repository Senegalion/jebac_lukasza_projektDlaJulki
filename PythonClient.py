import socket
import time
import re

def parseValue(stringReceived):
    pattern = re.compile(r'M  (\d+)\[([-0-9.]+,[-0-9.]+)\]')

    matches = pattern.findall(stringReceived)

    parsed_data = []
    for match in matches[0:3]:
        index = int(match[0])
        coordinates = tuple(map(float, match[1].split(',')))
        parsed_data.append({'index': index, 'coordinates': coordinates})

    # for item in parsed_data:
    #     print(f'M{item["index"]}: Coordinates {item["coordinates"]}')
    print(parsed_data)
    return parsed_data

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
    return repr(data)

def main():    
    server = set_socket_server()
    while True:
        print("___________________________")
        print(recv_data(server))
        print("___________________________")

if __name__ == "__main__":
    main()