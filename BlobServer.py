import socket, logging, _thread, copy
import pickle
from BlobGame import *

### CONFIGURABLES
logging.basicConfig(level=logging.DEBUG)
port = 8888
max_connections = 10
### END CONFIGURABLES

### BEGIN SOCKET BOILERPLATE
active_connections = []
active_connections_lock = _thread.allocate_lock()

master_blob_map = {}
master_blob_map_lock = _thread.allocate_lock()

print_lock = _thread.allocate_lock()

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setblocking(False) ##The key, turns off locks! Unsafe but useful with GIL

bound = False
host = ''
while bound == False:
    try:
        server.bind((host, port))
        logging.info( 'Successfully Bound to {}:{}'.format(host, port) )
        bound = True
    except socket.error as e:
        logging.error('Error binding: {}, attempting next port'.format(str(e)))
        port += 1

server.listen(max_connections)
### END SOCKET BOILERPLATE

def threaded_client(conn, ipaddr, port):
    ip_plus_port = str(ipaddr)+str(port)
    last_sent = {}
    with active_connections_lock:
        active_connections.append(ip_plus_port)

    while True:
        try:
            data_encoded = conn.recv(2048)
            data = pickle.loads(data_encoded)
            if not data_encoded == b'':
                #print(data)
                with master_blob_map_lock:
                    master_blob_map[ip_plus_port] = data
        except:
            pass ##SHHH, ... I know this is bad
        try:
            if (master_blob_map != last_sent): ##Make sure they are getting new info
                with master_blob_map_lock:
                    logging.debug("Sending {} to {}".format(master_blob_map, ip_plus_port))
                    encoded_map = pickle.dumps(master_blob_map)
                    conn.sendall(encoded_map)
                    last_sent = copy.copy(master_blob_map)
                with print_lock:
                    logging.debug('Sent map to {}'.format(conn))
        except Exception as e:
            if str(e) == 'Error sending: [Errno 32] Broken pipe':
                ##User has disconnected, proceeding is clean up code to remove them from game
                logging.info("User {} has disconnected".format(ip_plus_port))
                with active_connections_lock:
                    active_connections.remove(ip_plus_port)
                with master_blob_map_lock:
                    del master_blob_map[ip_plus_port]
                _thread.exit()
            else:
                logging.error("Error '{}' sending to {}".format(str(e)), ip_plus_port)

def main():
    ##Main thread handles listening for connections and passing them to their own personal threaded_client thread
    logging.info('Beginning listening for clients')
    while True:
        try:
            conn, addr = server.accept()
            logging.info('Connected to {}:{}'.format(addr[0],addr[1]))
            _thread.start_new(threaded_client, (conn, addr[0], addr[1]))
        except:
            pass

if __name__ == '__main__':
    main()