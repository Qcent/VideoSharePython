# Qvid - Video Streaming Application
Qvid is a demo video streaming application for Windows (MacOs support limited and currently broken), written in Python. It allows you to capture screenshots of your ~~desktop~~, webcam, and selected windows programs. The captured images are compressed and sent as a continuous stream over a TCP connection to a single machine.

## Features
- **Low latency, high framerate, peer to peer connectivity**: Qvid aims to provide high quality, realtime images with as little latency as possible.
- **Desktop, Webcam, and Window Capture**: Qvid enables you to capture screenshots of your desktop, webcam feed, and specific windows programs directly from your Windows operating system.
- **Real-time Compression**: The captured images are efficiently compressed in real-time to optimize the data transmission and reduce bandwidth usage.
- **TCP Streaming**: Qvid establishes a TCP connection between the client and server, enabling the seamless transfer of the compressed image stream to a single machine.

## Usage
`python Qvid.py [-n HOST] [-p PORT] [-m MODE] [-c CODEC] [-s SIZE] [-q QUALITY] [-w WINDOW]`

### Arguments
The script accepts the following arguments:

    -n HOST, --host HOST: The IP address of the host/server. As a Client you conect to host address.

    -p PORT, --port PORT: The port to run on. Client and Server must run on same port.

    -m MODE, --mode MODE: The operational mode. Choose one of the following modes:

        1 or --mode 1: Server/TX mode. This mode enables the script to act as a server and transmit video data.

        2 or --mode 2: Client/RX mode. This mode allows the script to act as a client and receive video data.

        3 or --mode 3: Server/RX mode. This mode allows the script to act as a server and receive video data.

        4 or --mode 4: Client/TX mode. This mode enables the script to act as a client and transmit video data.

        5 or --mode 3: Server/TX&RX mode. This mode allows the script to act as a server then send and receive video data.

        6 or --mode 4: Client/TX&RX mode. This mode enables the script to act as a client then send and receive video data.

    -c CODEC, --codec CODEC: The compression algorithim to use: 1: Jpeg, 2: WebP

    -s SIZE, --size SIZE: The output image size. Provide a value from 0-9.

    -s QUALITY, --quality QUALITY: The output image quality. Provide a value from 1-100.

    -w WINDOW, --window WINDOW: The full or partial name of the window to capture.


###  Examples
#### Mode 1
To run the script as a Server and transmit video data to a client on a specific port:

    python Qvid.py -p 8000 -m 1
#### Mode 2
To run the script as a Client and receive video data from a specific host(in mode 1) and port:

    python Qvid.py -n 192.168.0.100 -p 8000 -m 2 

## Server Hotkeys
  - Alt+page up: Increase the output video size.
  - Alt+page down: Decrease the output video size.
  - Alt+plus: Increase the output video quality.
  - Alt+minus: Decrease the output video quality.
  - Alt+home: Pause output for a brief moment (to reduce lag).
  - Alt+S: Open select window dialog to select a new capture source.

## Client Hotkeys
  - Alt+O: Resize video stream window to received image's original size (fastest performance).
  - Alt+S: Resize video stream window to match image's aspect ratio (remove black borders from window).
  - Alt+T: Toggle video stream window to always on top. 
  - Alt+M: Toggle video stream window to minimal (no title bar, no borders)
  - Alt+Enter: Toggle video stream window fullscreeen mode (usually slow).


## Notes
 *Default port is 5000 \
 *Default host is 127.0.0.1 \
 *Default mode is 1, Server that sends video \
 *Client/Server modes must be matched for sucsessful connection. modes(1-2) and modes(3-4), (5-6) for Server and Client respectivly
 
 ## Apologies
 Some sections of this code have been directly pulled from some online examples, with no credit given.  ); \
 As atonement I offer up this code for anyone to use as they like, no attribution nessacery.
