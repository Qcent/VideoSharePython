import socket
import struct

CHUNK_SIZE = 4096
PAYLOAD_SIZE = struct.calcsize("Q")


class TCPConnection:
    def __init__(self, host_address='127.0.0.1', port='5000', listen_address='0.0.0.0'):
        self.host_address = host_address
        self.listen_address = listen_address
        self.port = port
        self.server_socket = None
        self.client_socket = None
        self.recv_buf = b""

    def establish_connection(self):
        self.client_socket = socket.socket(socket.AF_INET, self.protocol)
        self.client_socket.connect((self.host_address, self.port))

    def start_server(self):
        self.server_socket = socket.socket(socket.AF_INET, self.protocol)
        self.server_socket.bind((self.listen_address, self.port))
        self.server_socket.listen(1)
        print(f'Server listening on: {self.listen_address}:{self.port} : {self.protocol}')

    def await_connection(self):
        client_socket, client_address = self.server_socket.accept()
        self.client_socket = client_socket
        print(f'Connection from {client_address} established')
        return client_socket, client_address

    # Modified send_data function to include a dynamic header
    '''
    example usage:
    network.send_data(data, header={
        name: value,
        name2, value2
    })
    '''
    def send_data_with_header(self, data, header=None):
        if header is None:
            header = {}

        header_data = self.pack_header(header)
        message = struct.pack("Q", len(header_data)) + header_data + struct.pack("Q", len(data)) + data

        self.client_socket.sendall(message)

    # Modified the receive_data function to retrieve a dynamic header and data
    def receive_data_with_header(self):
        while len(self.recv_buf) < PAYLOAD_SIZE:
            packet = self.client_socket.recv(CHUNK_SIZE)
            if not packet:
                return None
            self.recv_buf += packet

        header_size = struct.unpack("Q", self.recv_buf[:PAYLOAD_SIZE])[0]
        self.recv_buf = self.recv_buf[PAYLOAD_SIZE:]
        header_data = self.recv_buf[:header_size]
        self.recv_buf = self.recv_buf[header_size:]

        header = self.unpack_header(header_data)

        data_size = struct.unpack("Q", self.recv_buf[:PAYLOAD_SIZE])[0]
        self.recv_buf = self.recv_buf[PAYLOAD_SIZE:]

        while len(self.recv_buf) < data_size:
            if self.protocol == socket.SOCK_STREAM:
                self.recv_buf += self.client_socket.recv(CHUNK_SIZE)

        received_data = self.recv_buf[:data_size]
        self.recv_buf = self.recv_buf[data_size:]

        return header, received_data

    def send_data(self, data):
        message = struct.pack("Q", len(data)) + data
        self.client_socket.sendall(message)

    def receive_data(self):
        while len(self.recv_buf) < PAYLOAD_SIZE:
            packet = self.client_socket.recv(CHUNK_SIZE)
            if not packet:
                return None
            self.recv_buf += packet

        packed_msg_size = self.recv_buf[:PAYLOAD_SIZE]
        self.recv_buf = self.recv_buf[PAYLOAD_SIZE:]
        msg_size = struct.unpack("Q", packed_msg_size)[0]

        while len(self.recv_buf) < msg_size:
            self.recv_buf += self.client_socket.recv(CHUNK_SIZE)

        received_data = self.recv_buf[:msg_size]
        self.recv_buf = self.recv_buf[msg_size:]

        return received_data

    def close_connection(self):
        if self.server_socket:
            self.server_socket.close()
        if self.client_socket:
            self.client_socket.close()

