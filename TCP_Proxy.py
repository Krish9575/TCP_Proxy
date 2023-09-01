import sys
import socket
import threading


def server_loop(local_host, local_port, remote_host, remote_port, receive_first):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        server.bind((local_host, local_port))
    except:
        print(f"[!!] Failed to listen on ( {local_host, local_port} )")
        print(f'[!!] Check for other listen sockets or connect permission')
        sys.exit(0)

    print(f'[*] Listening on {local_host, local_port}')

    server.listen(5)

    while True:
        client_socket, addr = server.accept()

        # print out the local connection information

        print(f'[==>] Received incoming connection from {addr[0], addr[1]}')

        # start a thread to talk to remote host
        proxy_thread = threading.Thread(target=proxy_handler,
                                        args=(client_socket, remote_host, remote_port, receive_first))
        proxy_thread.start()


def main():
    # no fancy command-line parsing here
    if len(sys.argv[1:]) != 5:
        print("Usage: ./TCP_proxy.py [local_host] [local_port] [remote_host] [remote_port] [receive_first]")
        print('Example : ./TCP_Proxy.py 127.0.0.1 8888 10.12.132.1 9000 True')
        sys.exit(0)

    # setup local listening parameter
    local_host = sys.argv[1]
    local_port = int(sys.argv[2])

    # setup remote parameter
    remote_host = sys.argv[3]
    remote_port = int(sys.argv[4])

    # this tell pur proxy to connect or receive the data
    # before sending the remote host

    receive_first = sys.argv[5]

    if "True" in receive_first:
        receive_first = True
    else:
        receive_first = False

    # now spin up our listening socket

    server_loop(local_host, local_port, remote_host, remote_port, receive_first)


def proxy_handler(client_socket, remote_host, remote_port, receive_first):
    # connect to the remote host
    remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    remote_socket.connect((remote_host, remote_port))

    # receive data from the remote end if necessary

    if receive_first:

        remote_buffer = receive_from(remote_socket)
        hexdump(remote_buffer)

        # send it to our response handler

        remote_buffer = response_handler(remote_buffer)

        # if we have data to send to our local client, send it
        if len(remote_buffer):
            print(f"[<==] Sending bytes to localhost.{len(remote_buffer)}")
            client_socket.send(remote_buffer.encode('utf-8'))

        # now lets loop and read from local ,send to remote,send to local
        # rinse , wash, repeat

        while True:
            # read from local host
            local_buffer = receive_from(client_socket)

            if len(local_buffer):
                print(f'[==>] Received bytes from localhost. {len(local_buffer)}')

                hexdump(local_buffer)

                # send it to our request handler

                local_buffer = request_handler(local_buffer)

                # send off the data to remote host
                remote_socket.send(local_buffer.encode('utf-8'))

                print('[==>] Sent ot remote')

            # receive back the response

            remote_buffer = receive_from(remote_socket)

            if len(remote_buffer):
                print(f'[==>] Received bytes from remote host. {len(remote_buffer)}')

                hexdump(remote_buffer)

                # send it to our response handler

                remote_buffer = response_handler(remote_buffer)

                # send off the data to remote host
                client_socket.send(remote_buffer.encode('utf-8'))

                print('[<==] Sent ot localhost')

            # if no more data on either side , close the connections

            if not len(remote_buffer) or not len(local_buffer):
                remote_socket.close()
                client_socket.close()

                print('[*] No more data. Closing connections.')

                break


# modify any requests destined for the remote host
def request_handler(buffer):
    # perform packet modifications
    return buffer


def receive_from(connection):
    buffer = ""

    # we set a 2 second timeout ; depending on your
    # target, this may need to be adjusted
    connection.settimeout(2)

    try:
        # keep reading into the buffer until there's no more data
        # or we time out

        while True:
            data = connection.recv(4096)
            if not data:
                break
            else:
                buffer += data
    except:
        pass

    return buffer


# this is a pretty hex dumping function directly taken from
# the comments here:
# http://code.activestate.com/recipes/142812-hex-dumper/
# but modified according to python 3.x
def hexdump(src, length=8):
    result = []
    digits = 4 if isinstance(src, str) else 2
    for i in range(0, len(src), length):
        s = src[i:i + length]
        hexa = ' '.join(["%0*X" % (digits, ord(x)) for x in s])
        text = ''.join([x if 0x20 <= ord(x) < 0x7F else '.' for x in s])
        result.append(f"{i:04X}   {hexa:<{length * (digits + 1)}s}   {text}")
    print('\n'.join(result))


# modify any response destined for the localhost

def response_handler(buffer):
    # perfrom packet modifications
    return buffer


main()
