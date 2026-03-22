'''
A snake game involving one snake, multiple monsters, and randomly generated numbers.
The player needs to use arrow keys to control the snake to eat the numbers while avoiding collisions with monsters.
The game is completed when all numbers have been eaten and the snake is fully extended.
'''
import turtle
import random
from functools import partial
import time

g_screen = None
g_snake = None     # snake's head
g_monster = None
num_monsters = 4
g_monsters_list = []
g_snake_sz = 5     # size of the snake's tail initial = 5
g_intro = None
g_key_pressed = None
g_status = None
g_numbers = []
count_consume = 0
g_start_time = None
seconds = 0

pre_key = 'Right'
pre_heading = 0
is_blocked= False        #the status being blocked by the boundaries
paused_by_space = False  #the status of the spaced being pressed


is_over = False

stamp_positions = []     #list storing the current stamps' positions 
count_contact = 0        #the number of contacts between snake and monsters


COLOR_BODY = ("blue", "black")
COLOR_HEAD = "red"
COLOR_MONSTER = "purple"
FONT_INTRO = ("Arial",16,"normal")
FONT_STATUS = ("Arial",17,"normal", "bold")
TIMER_SNAKE = 200   # refresh rate for snake
TIMER_MONSTER_BASE = TIMER_SNAKE 
SZ_SQUARE = 20      # square size in pixels

DIM_PLAY_AREA = 500
DIM_STAT_AREA = 40 # !!! multiple of 40
DIM_MARGIN = 30

KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT, KEY_SPACE = \
       "Up", "Down", "Left", "Right", "space"

HEADING_BY_KEY = {KEY_UP:90, KEY_DOWN:270, KEY_LEFT:180, KEY_RIGHT:0}

def create_turtle(x, y, color="red", border="black"):
    """
    Creates a new turtle object with the specified position, color, and border.
    
    Args:
        x (int): The x-coordinate of the turtle's initial position.
        y (int): The y-coordinate of the turtle's initial position.
        color (str, optional): The color of the turtle's body. Defaults to "red".
        border (str, optional): The color of the turtle's border. Defaults to "black".
    
    Returns:
        turtle.Turtle: The newly created turtle object.
    """
    t = turtle.Turtle("square")
    t.color(border, color)
    t.up()
    t.goto(x,y)
    return t



def create_numbers():
    """
    Creates the number turtles representing food items for the snake.
    The numbers 1 to 5 are generated at random coordinates and added 
    to the g_numbers list.
    """
    global g_numbers
    for i in range(1, 6):
        x = random.randint(-8,8)
        y = random.randint(-8,8)
        x = x * 20            
        y = y * 20                #ensure the numbers are aligned with the snake's head
        t = create_turtle(x,y-10)
        t.write(str(i), align="center",font=("Arial", 15, "normal"))
        t.goto(x,y)
        t.hideturtle()            
        g_numbers.append(t)

    return g_numbers
    

def create_monsters():
    """
    Initialize a specific number of monsters at random locations on the screen. 
    Also to put them into a list for future reference.
    """
    global g_monsters_list, num_monsters
    num_monsters = 4
    for i in range(num_monsters):
        while True:
            x = random.randint(-200,200)
            y = random.randint(-200,200)
            if abs(x) < 100 and abs(y) < 100:     #avoid the monsters are initialized near center
                continue
            
            monster = create_turtle(x,y, COLOR_MONSTER)
            g_monsters_list.append(monster)       #add monster to the list for future reference
            break


def configure_play_area():
    """
    Configures the play area for the snake game, 
    including the motion border, status border, 
    introduction text, and status text.
    The motion border and status border are based on square shape
    resized according to the specified dimensions.

    Returns:
        tuples: A tuple containing the introduction text turtle and 
        the status text turtle.
    """

    # motion border
    m = create_turtle(0,0,"","black")
    sz = DIM_PLAY_AREA//SZ_SQUARE
    
    m.shapesize(sz, sz, 3)
    
    m.goto(0,-DIM_STAT_AREA//2)  # shift down half the status

    # status border
    s = create_turtle(0,0,"","black")
    sz_w, sz_h = DIM_STAT_AREA//SZ_SQUARE, DIM_PLAY_AREA//SZ_SQUARE
    s.shapesize(sz_w, sz_h, 3)
    s.goto(0,DIM_PLAY_AREA//2)  # shift up half the motion

    # turtle to write introduction
    intro = create_turtle(-200,0)
    intro.hideturtle()
    intro.write("Snake game by cyl.\n\nClick anywhere to start the game .....\n\n" ,  \
                font=FONT_INTRO)

    # turtle to write status
    status = create_turtle(0,0,"","black")
    status.hideturtle()
    status.goto(-200,s.ycor()-10)

    return intro, status

def configure_screen():
    """
    Configures the Turtle screen for the snake game,
    the screen width and height are calculated based 
    on the play area, status bar and margin.
    
    Returns:
        turtle.Screen: The configured Turtle screen.
    """
    s = turtle.Screen()
    s.tracer(0)    # disable auto screen refresh, 0=disable, 1=enable
    s.title("Snake by CYL")
    w = DIM_PLAY_AREA + DIM_MARGIN*2
    h = DIM_PLAY_AREA + DIM_MARGIN*2 + DIM_STAT_AREA
    s.setup(w, h)
    s.mode("standard")
    return s

def update_status():
    """
    Updates the status display on the screen with 
    the current key press and snake tail length.
    """
    g_status.clear()
    
    now = time.time()
    seconds = int(now - g_start_time)  #update the time on the status board

    if not paused_by_space:
        if g_key_pressed == 'space':
            status = f'Contact-{count_contact}    Time-{seconds}    Motion-{pre_key}'
        else:
            status = f'Contact-{count_contact}    Time-{seconds}    Motion-{g_key_pressed}'
    else: #showcase the special "Paused" status
        status = f'Contact-{count_contact}    Time-{seconds}    Motion-Paused'
    
    g_status.write(status, font=FONT_STATUS, align='left')
    g_screen.update()

def on_arrow_key_pressed(key):
    """
    Handles the user's arrow key press event and 
    updates the global `g_key_pressed` variable with the pressed key. 
    It then calls the `update_status()` function to update 
    the status display on the screen.
    
    Args:
        key (str): The key that was pressed, one of 'Up', 'Down', 'Left', or 'Right'.
    """
    global g_key_pressed, pre_heading, paused_by_space, pre_key, is_blocked

    g_key_pressed = key
    
    
    # unblock the snake when pressing the key other than the obstructive key
    if g_key_pressed != pre_key:
        is_blocked = False
    
    #record the previous arrow key    
    if key != 'space':
        paused_by_space = False
        pre_key = key
        pre_heading = HEADING_BY_KEY[key]
    
    #change the status of paused_by_space by pressing the space key
    if key == 'space':
        paused_by_space = not paused_by_space
        # print('paused_by_space:')
        # print(paused_by_space)

    update_status()




def on_timer_snake():
    """
    Advances the snake's movement on a timer. This function is called repeatedly 
    by the Turtle screen's `ontimer` method to update the snake's position.
    
    If no key has been pressed, the function simply schedules itself to be called 
    again after the `TIMER_SNAKE` interval. Otherwise, it performs the following steps:
    
    1. Clones the snake's head as a new body segment by setting the color to `COLOR_BODY` 
        and stamping it on the screen.
    2. Sets the snake's color back to `COLOR_HEAD`.
    3. Advances the snake's position by setting the heading based 
        on the last key pressed (`g_key_pressed`) and 
        moving the snake forward by `SZ_SQUARE` units.
    4. If the number of stamped segments exceeds the current snake size (`g_snake_sz`), 
        removes the last segment by clearing the oldest stamp.
    5. Updates the Turtle screen to reflect the changes.
    6. Schedules the function to be called again after the `TIMER_SNAKE` interval.
    """
    
    global TIMER_SNAKE, g_snake, is_blocked, paused_by_space, g_key_pressed
    
    #return if game over == True
    if is_over:
        return
    
    update_status()
    
    #check the hit by the monster
    is_hit()
    
    #stop the snake when paused or blocked
    if g_key_pressed is None or paused_by_space or is_blocked:
        g_screen.ontimer(on_timer_snake, TIMER_SNAKE)
        return
    
    
    x, y = g_snake.pos()[0], g_snake.pos()[1]
    
    if g_key_pressed == 'space':
        g_key_pressed = pre_key
    
    # print(g_key_pressed)
    
    #check if the snake is blocked by the boundaries
    if (g_key_pressed == "Up" and y >= 220) or \
        (g_key_pressed == "Down" and y <= -260) or \
        (g_key_pressed == "Left" and x <= -230) or \
        (g_key_pressed == "Right" and x >= 230):
        is_blocked = True
        g_screen.ontimer(on_timer_snake, TIMER_SNAKE)
        return
    
    TIMER_SNAKE = 200
    
    # Clone the head as body
    g_snake.color(*COLOR_BODY)
    g_snake.stamp()
    stamp_pos= g_snake.pos()
    stamp_positions.append(stamp_pos)
    
    g_snake.color(COLOR_HEAD)

    # Advance snake
    if g_key_pressed != KEY_SPACE:
        g_snake.setheading( HEADING_BY_KEY[g_key_pressed] )
        g_snake.forward(SZ_SQUARE)
        
    
    if g_key_pressed == KEY_SPACE:
        g_snake.setheading(pre_heading)
        g_snake.forward(SZ_SQUARE)
    # Shifting or extending the tail.
    # Remove the last square on Shifting.
    if len(g_snake.stampItems) > g_snake_sz:
        g_snake.clearstamps(1)
        stamp_positions.pop(0)
        TIMER_SNAKE = 200
    else:
        TIMER_SNAKE = 400
    
    #deal with the food item consumption
    for number in g_numbers:
        if number:
            is_consumed(number)
    
    #count the contact of the monsters and the snake's body
    for monster in g_monsters_list:
        global count_contact
        for (x,y) in stamp_positions:
            dx = abs(monster.xcor() - x)
            dy = abs(monster.ycor() - y)
            if dx < 20 and dy < 20:
                count_contact += 1
    
    
    
    #check the size of the snake to judge the winning of the game
    winner()
    
    g_screen.update()

    g_screen.ontimer(on_timer_snake, TIMER_SNAKE)


def on_timer_monster(monster):
    """
    Advances the monster's movement on a timer. 
    This function is called repeatedly 
    by the Turtle screen's `ontimer` method to update the monster's position.
    
    The function performs the following steps:
    
    1. Calculates the heading for the monster to move towards the snake, 
        snapping to the nearest 45-degree angle.
    2. Sets the monster's heading to the calculated value.
    3. Moves the monster forward by `SZ_SQUARE` units.
    4. Updates the Turtle screen to reflect the changes.
    5. Schedules the function to be called again after a random delay 
        between `TIMER_SNAKE-50` and `TIMER_SNAKE+200` milliseconds.
    """
    if is_over:
        return
        
    # for monster in g_monsters_list:
    angle = monster.towards(g_snake)
    qtr = angle//45 # (0,1,2,3,4,5,6,7)
    heading = qtr * 45 if qtr % 2 == 0 else (qtr+1) * 45

    monster.setheading(heading)
    monster.forward(SZ_SQUARE)

    g_screen.update()
    delay = random.randint(TIMER_MONSTER_BASE-50, TIMER_MONSTER_BASE+500)
    g_screen.ontimer(partial(on_timer_monster,monster),delay)
    


def on_timer_numbers():
    """
    Moves the number turtles randomly on a timer.
    This function is called repeatedly by the screen's 
    ontimer method. It moves each number turtle in a random
    direction by a fixed amount.
    new timer is set with a random interval between
    5-10 seconds for the next call.
    """
    if is_over:
        return
    
    for number in g_numbers:
        if number == None:
            continue
        #random directions of the number turtle
        directions = [0, 90, 180, 270]  
        heading = random.choice(directions)
        number.setheading(heading)
        #randomly shift the position of the numbers
        distances = [0,0,40]
        distance = random.choice(distances)
        if distance != 0:
            number.clear()
            number.forward(distance)
            i = g_numbers.index(number)
            number.setheading(270)
            number.forward(10)
            number.write(str(i+1), align="center",font=("Arial", 15, "normal"))
            number.forward(-10)
    
    #set shifting time at a random rate   
    delay = random.randint(5000, 10000) 
    g_screen.ontimer(on_timer_numbers, delay)





def is_consumed(number):
    """
    Checks if a number turtle is consumed by the snake.

    If the snake overlaps with the number turtle, this function
    hides the turtle, removes it from g_numbers, and returns True.
    Otherwise it returns False.

    Args:
        number: The turtle object to check for consumption
    """
    #check if the food items are consumed
    distance = g_snake.distance(number)
    if distance < 15:
        number_id = g_numbers.index(number)
        number.clear()
        g_numbers[number_id] = None      
        global count_consume
        count_consume += 1
        number.goto(100000,100000)
        consume_food(number_id + 1)
        return number_id
    else:
        return None

def is_hit():
    """
    Checks if the snake hits any of the monsters.

    This function calculates the distance between the snake and 
    each monster. If the distance is less than 20 pixels, it 
    sets the is_over flag to True to end the game.

    It also stops the snake and monster movements by clearing
    their timers.
    """
    global is_over
    for monster in g_monsters_list:
        distance = g_snake.distance(monster)
        if distance < 20:
            is_over = True
            #use turtle to write the words "Game Over"
            turtle.color('red')
            turtle.goto(0, 0) 
            turtle.write("Game Over!", align="center", font=("Arial", 60))
            turtle.hideturtle()
            # Stop the snake and monster movements
            g_screen.ontimer(None, TIMER_SNAKE) 
        
        

    
def consume_food(num):
    """
    Simulate the action when the snake consumes the given food item num.
    Increase the length of the snake's tail by the given num value.
    
    Args:
        num (int): The value of food item being consumed by the snake
    
    Modifies:
        g_snake_sz (int): Increments the size of the snake's body by the specified number.
        update_status(): Updates the game status display to reflect the new snake size.
    """

    global g_snake_sz
    if g_snake_sz < 100:
        g_snake_sz += num
        
        update_status()
    
    global TIMER_SNAKE
    TIMER_SNAKE = 600  #slow down the movement of the snake
    if len(g_snake.stampItems) > g_snake_sz:
        TIMER_SNAKE = 300
        update_status()

    

def winner():
    """
    Checks if the snake has grown long enough to win.

    If the number of snake segments exceeds the winning
    length, it sets is_over to True, displays a "Winner!" 
    message, and stops the game.
    """
    global is_over
    # print(len(g_snake.stampItems))
    #check if the snake length reaches the winning length
    # when 4monsters and 5numbers: the whole size(after fully extended) should be 5 + 15 = 20
    if len(g_snake.stampItems) >= 5 + (1 + 5) * 5 / 2: 
        is_over = True
        turtle.color('red')
        turtle.goto(0, 0) 
        turtle.write("Winner!", align="center", font=("Arial", 60))
        turtle.hideturtle()





def cb_start_game(x, y):
    """
    Starts the game by setting up the initial game state and event handlers.
    
    This function is called when the user clicks on the screen to start the game.
    It performs the following steps:
    
    1. Clears the on-screen click handler to prevent further clicks from starting the game.
    2. Clears the introductory message.
    3. Registers key event handlers for the arrow keys to handle player movement.
    4. Starts the timer-based updates for the snake and monster movements.
    5. Registers key event handlers for consuming food items 1 through 5.
    """
    g_screen.onscreenclick(None)
    g_intro.clear()
    
    global g_start_time
    g_start_time = time.time()   #record the starting time
    
    numbers = create_numbers()   #create and display the number turtles
    
    
    for key in (KEY_UP, KEY_DOWN, KEY_RIGHT, KEY_LEFT, KEY_SPACE):
        g_screen.onkey(partial(on_arrow_key_pressed,key), key)


    on_timer_snake()
    for monster in g_monsters_list:
        on_timer_monster(monster)
    on_timer_numbers()

if __name__ == "__main__":
    """
    A small demo illustrating the main processing logic 
    for a Snake game using Python Turtle graphics.
    """
    g_screen = configure_screen()
    g_intro, g_status = configure_play_area()

    g_snake = create_turtle(0,0, COLOR_HEAD, "black")
    
    create_monsters()
    
    g_screen.onscreenclick(cb_start_game) # set up a mouse-click call back
    
    
    
    g_screen.update()
    g_screen.listen()
    g_screen.mainloop()