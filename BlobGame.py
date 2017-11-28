import pygame
import random, socket, _thread, logging, copy, math
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
    def __init__(self, color, type):
        self.x = random.randrange(0, WIDTH)
        self.y = random.randrange(0, HEIGHT)
        self.size = random.randrange(1, 10)
        self.color = color
        self.type = type ## 0 is player, 1 is food,

    def __eq__(self, other):
        ##Only used to check if self has changed, so okay to perform only these basic checks.
        ##Do not use in multiplayer checking
        if (self.x == other.x) and (self.y == other.y) and (self.size == other.size):
            return True
        else:
            return False

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

def draw_ui(blob, mouse_x, mouse_y, dist = 20, size=3):
    angle_mouse_player = ( math.atan2((mouse_y-blob.y), (mouse_x-blob.y)) )
    print(math.degrees(angle_mouse_player))
    x, y = (dist*math.cos((-angle_mouse_player)))+blob.x, (dist*math.sin((-angle_mouse_player)))+blob.y
    pygame.draw.polygon(game_display, BLACK, [(x, y), (x-size, y+size), (x+size, y+size)])


def threaded_recv(conn):
    while True:
        try:
            data_encoded = conn.recv(4096)
            with blob_map_lock:
                global blob_map ##I'm pretty sure this is bad practice too but oh well
                data = pickle.loads(data_encoded)
                new_map = dict(data)
                blob_map = new_map
            logging.debug ('Recieved {} from server'.format(data))
        except:
            pass

def blob_to_text(blob):
    x = blob.x
    y = blob.y
    color = blob.color
    size = blob.size
    type = blob.type

    newlst = [x, y, color, size, type]
    return newlst

def text_to_blob(text):
    x = (text[0])
    y = (text[1])
    color = (text[2])
    size = (text[3])
    type = (text[4])

    new_blob = Blob(color, type)
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
    personal_player = Blob(BLACK, 0)
    x_change = 0
    y_change = 0
    last_update = Blob(BLACK, 0) ##Make this different to ensure the first update is done
    cursor_x = 0
    cursor_y = 0
    ##END ONE TIME SETUP CODE


    ##BEGIN GAME LOOP
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                ##Introduce some signalling for telling the server to shutdown and del the user
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
            if event.type == pygame.MOUSEMOTION:
                cursor_x, cursor_y = pygame.mouse.get_pos()

        personal_player.move(x_change, y_change)
        if last_update != personal_player:
            update_player(personal_player, s)
            last_update = copy.copy(personal_player)
        draw_environment()
        draw_ui(personal_player, cursor_x, cursor_y)
        pygame.display.update()
        clock.tick(60)

if __name__ == '__main__':
    main()