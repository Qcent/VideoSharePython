import argparse


def get_parsed_args():
    # Create an argument parser
    parser = argparse.ArgumentParser(description='Send video data to a computer over tcp/ip')

    # Add arguments to the parser
    parser.add_argument('-n', '--host', type=str, help='IP address of host/server')
    parser.add_argument('-p', '--port', type=str, help='Port to run on')
    parser.add_argument('-m', '--mode', type=int, help='Operational Mode: 1: Server/TX, 2: Client/RX, 3: Server/RX, 4: Client/TX, 5: Server/TX&RX, 6: Client/TX&RX')
    parser.add_argument('-c', '--codec', type=int, help='Compression algorithim to use: 1: Jpeg, 2: WebP')
    parser.add_argument('-s', '--size', type=int, help='Output image size: (0-9)')
    parser.add_argument('-q', '--quality', type=int, help='Output image quality: (1-100)')
    parser.add_argument('-w', '--window', type=str, help='Name of window to capture')

    # Parse and return the arguments
    return parser.parse_args()


class AppSettings:
    def __init__(self):
        self.args = get_parsed_args()
        self.KILLED = False


app_settings = AppSettings()
