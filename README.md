# VideoSharePython
Demo "Video" streaming app for windows written in python. will continually screenshot your desktop, web cam, and *some* windows programs naitively. compress and send the images in a stream over a tcp connection to a single machine.

## Usage
`python Qvid.py [-n HOST] [-p PORT] [-m MODE]`
### Arguments

The script accepts the following arguments:

    -n HOST, --host HOST: The IP address of the host/server. As a Client you conect to host address.

    -p PORT, --port PORT: The port to run on. Client and Server must run on same port.

    -m MODE, --mode MODE: The operational mode. Choose one of the following modes:

        1 or --mode 1: Server/TX mode. This mode enables the script to act as a server and transmit video data.

        2 or --mode 2: Client/RX mode. This mode allows the script to act as a client and receive video data.

        3 or --mode 3: Server/RX mode. This mode allows the script to act as a server and receive video data.

        4 or --mode 4: Client/TX mode. This mode enables the script to act as a client and transmit video data.
  
###  Examples
#### Mode 1
To run the script as a Server and transmit video data to a client on a specific port:

    python Qvid.py -p 8000 -m 1
#### Mode 2
To run the script as a Client and receive video data from a specific host(in mode 1) and port:

    python Qvid.py -n 192.168.0.100 -p 8000 -m2 

## Notes
 *Default port is 5000 \
 *Default host is 127.0.0.1 \
 *Default mode is 2, Client that reveives video \
 *Client/Server modes must be matched for sucsessful connection. modes(1-2) and modes(3-4) for Server and Client respectivly
 
 ## Apologies
 Some sections of this code have been directly pulled from some online examples, with no credit given.  ); \
 As atonement I offer up this code for anyone to use as they like, no attribution nessacery.
