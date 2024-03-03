import socket

class UDPConnection:
    def __init__(self):
        self.host_address = "127.0.0.1"  # Default to localhost
        self.socklen = None
        self.addrlen = None
        self.udp_socket = None
        self.servaddr = None
        self.cliaddr = None
        self.other = None  # Simplifies 1 server/1 client communication
        self.port = None
        self.silent = False
        self.server = False

    def __del__(self):
        if self.udp_socket:
            self.udp_socket.close()

    def start_as_server(self, port):
        self.port = port
        self.server = True

        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.servaddr = ("", self.port)  # listen address

        # Bind the socket with the server address
        self.udp_socket.bind(self.servaddr)
        self.other = self.cliaddr

    def start_as_client(self, serv_address, port):
        self.host_address = serv_address
        self.port = port

        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Filling server information
        self.servaddr = (self.host_address, self.port)
        self.udp_socket.connect(self.servaddr)
        self.other = self.servaddr

    def set_silence(self, setting=True):
        self.silent = setting

    def send_data(self, data):
        bytes_sent = self.udp_socket.sendto(data, self.other)
        if bytes_sent == 0:
            print("Failed to send data")
        return bytes_sent

    def receive_data(self, buffer_size):
        data, addr = self.udp_socket.recvfrom(buffer_size)
        if not data:
            print("Failed to receive data")
        return data

# Example usage:
# udp_conn = UDPConnection()
# udp_conn.start_as_server(5005)  # Start as server on port 5005
# udp_conn.start_as_client("127.0.0.1", 5005)  # Start as client, connecting to server at 127.0.0.1:5005
# udp_conn.send_data(b"Hello, server!")
# received_data = udp_conn.receive_data(1024)
# print("Received data:", received_data)
