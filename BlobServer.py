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

'''
def threaded_send(conn):
    #last_sent = []
    while True:
        try:
            #if (master_blob_map != last_sent) or True: ##Make sure they are getting new info
                #with master_blob_map_lock:
            encoded_map = pickle.dumps(master_blob_map)
            print ('sending', master_blob_map, encoded_map)
            conn.sendall(encoded_map)
            #last_sent = master_blob_map
            #with print_lock:
                #logging.debug('Sent map to {}'.format(conn))
        except Exception as e:
            print('Error sending: {}'.format(str(e)))
'''

def threaded_client(conn, ipaddr):
    last_sent = {}
    with active_connections_lock:
        active_connections.append(str(ipaddr))

    while True:
        try:
            data_encoded = conn.recv(2048)
            data = pickle.loads(data_encoded)
            if not data_encoded == b'':
                print(data)
                with master_blob_map_lock:
                    master_blob_map[str(ipaddr)] = data
        except:
            pass ##SHHH, ... I know this is bad
        try:
            if (master_blob_map != last_sent): ##Make sure they are getting new info
                with master_blob_map_lock:
                    print ('sending', master_blob_map)
                    encoded_map = pickle.dumps(master_blob_map)
                    conn.sendall(encoded_map)
                    last_sent = copy.copy(master_blob_map)
                with print_lock:
                    logging.debug('Sent map to {}'.format(conn))
        except Exception as e:
            print('Error sending: {}'.format(str(e)))

def main():
    ##Main thread handles listening for connections and passing them to their own personal threaded_client thread
    logging.info('Beginning listening for clients')
    while True:
        try:
            conn, addr = server.accept()
            logging.info('Connected to {}:{}'.format(addr[0],addr[1]))
            _thread.start_new(threaded_client, (conn, addr[0]))
            #_thread.start_new(threaded_send, (conn,))
        except:
            pass

if __name__ == '__main__':
    main()