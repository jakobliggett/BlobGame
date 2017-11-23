import pygame
import random, socket, _thread, logging, copy
import pickle

if __name__ == '__main__':
    ##TODO FIX THIS
    ip = input('Enter IP: ')
    port = int(input('Enter Port: '))
    ## END TODO

    ### BEGIN CONFIGUREABLES
    logging.basicConfig(level=logging.DEBUG)
    WIDTH = 800
    HEIGHT = 600

    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    ###END CONFIGURABLES


    pygame.init()
    game_display = pygame.display.set_mode((800,600))
    clock = pygame.time.Clock()
    blob_map = {}
    blob_map_lock = _thread.allocate_lock()

class Blob:
    def __init__(self, color):
        self.x = random.randrange(0, WIDTH)
        self.y = random.randrange(0, HEIGHT)
        self.size = random.randrange(1, 10)
        self.color = color

    def check_bounds(self):
        if self.x < 0:
            self.x = 0
        elif self.x > WIDTH:
            self.x = WIDTH

        if self.y < 0:
            self.y = 0
        elif self.y > HEIGHT:
            self.y = HEIGHT

    def move(self, rel_x, rel_y):
        self.x = self.x + rel_x
        self.y = self.y + rel_y
        self.check_bounds()

    def set_attributes(self, x, y, size):
        self.x = x
        self.y = y
        self.size = size

class Player(Blob):
    pass


def draw_environment():
    game_display.fill(WHITE)
    for player_ip in blob_map:
        other_blob_representation = blob_map[player_ip] ##Get data for each blob in map
        #print('other_rep: ', other_blob_representation)
        other_blob = text_to_blob(other_blob_representation)
        draw_blob(other_blob)
    pygame.display.update()

def update_player(player, conn):
    to_send = blob_to_text(player) ##Encoding step
    to_send_pickled = pickle.dumps(to_send)
    conn.sendall(to_send_pickled)
    logging.debug('Sent updated player info to host')

def draw_blob(blob):
    try:
        pygame.draw.circle(game_display, blob.color, [blob.x, blob.y], blob.size)
    except Exception as e:
        logging.error('Error drawing blob: {}'.format(str(e)))

def threaded_recv(conn):
    while True:
        try:
            data_encoded = conn.recv(4096)
            with blob_map_lock:
                global blob_map ##I'm pretty sure this is bad practice too but oh well
                data = pickle.loads(data_encoded)
                new_map = dict(data)
                blob_map = new_map
            print ('tst', data)
        except:
            pass

def blob_to_text(blob):
    x = blob.x
    y = blob.y
    color = blob.color
    size = blob.size

    newlst = [x, y, color, size]
    return newlst

def text_to_blob(text):
    x = (text[0])
    y = (text[1])
    color = (text[2])
    size = (text[3])

    new_blob = Blob(color)
    new_blob.set_attributes(x, y, size)
    return new_blob

def main():
    ### SOCKET BOILERPLATE
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #s.setblocking(0)  # Testing
    try:
        s.connect((ip, port))
        logging.info('Successfully connected to server')
        _thread.start_new(threaded_recv, (s,))
    except socket.error as e:
        logging.error("Trouble Connecting to Host, error: '{}' ".format(str(e)))

    ### END SOCKET BOILERPLATE


    ##BEGIN ONE-TIME SETUP CODE
    personal_player = Blob(BLACK)
    #blob_map.append(personal_player) ##BAD, use lock?
    x_change = 0
    y_change = 0
    last_update = []
    ##END ONE TIME SETUP CODE


    ##BEGIN GAME LOOP
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    x_change = -5
                elif event.key == pygame.K_RIGHT:
                    x_change = 5
                if event.key == pygame.K_UP:
                    y_change = -5
                elif event.key == pygame.K_DOWN:
                    y_change = 5
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                    x_change = 0
                if event.key == pygame.K_DOWN or event.key == pygame.K_UP:
                    y_change = 0

            #print(event)
        personal_player.move(x_change, y_change)
        if last_update != personal_player:
            update_player(personal_player, s)
            last_update = copy.copy(personal_player)
        draw_environment()
        pygame.display.update()
        clock.tick(60)
        #print(blob_map)

if __name__ == '__main__':
    main()