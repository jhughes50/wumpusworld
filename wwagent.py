"""
Modified from wwagent.py written by Greg Scott

Modified to only do random motions so that this can be the base
for building various kinds of agent that work with the wwsim.py 
wumpus world simulation -----  dml Fordham 2019

# FACING KEY:
#    0 = up
#    1 = right
#    2 = down
#    3 = left

# Actions
# 'move' 'grab' 'shoot' 'left' right'

Modified by Jason Hughes
December 14 2020

Autonomous agent created using probabilistic model checking for the agents action
Note: An error is sometimes thrown after a large number of moves, it rarely happens,
just ignore and rerun.
"""

from random import randint
import math
import copy
import time

# This is the class that represents an agent

class WWAgent():

    def __init__(self):
        self.max=4 # number of cells in one side of square world
        self.stopTheAgent=False # set to true to stop th agent at end of episode
        self.position = (0, 3) # top is (0,0)
        self.directions=['up','right','down','left']
        self.facing = 'right'
        self.arrow = 1
        self.percepts = (None, None, None, None, None)
        self.map = [[ self.percepts for i in range(self.max) ] for j in range(self.max)]

        # my varaibles
        self.myMap = [] # my knowledge base (KB)
        self.models = [] # list to hold the models I create
        self.schema = [] # schema necesary to get to desired cell
        self.generateMap() # atomatically generate my blank KB
        
        print("New agent created")

    # Add the latest percepts to list of percepts received so far
    # This function is called by the wumpus simulation and will
    # update the sensory data. The sensor data is placed into a
    # map structured KB for later use
    
    def update(self, percept):
        self.percepts=percept
        #[stench, breeze, glitter, bump, scream]
        if self.position[0] in range(self.max) and self.position[1] in range(self.max):
            self.map[ self.position[0]][self.position[1]]=self.percepts
        # puts the percept at the spot in the map where sensed

    # Since there is no percept for location, the agent has to predict
    # what location it is in based on the direction it was facing
    # when it moved

    def calculateNextPosition(self,action):
       """
       Altered original function, I only calculate possible actions, meaning no bump
       """
       #pose[+1][same] = right
       #pose[-1][same] = left
       #pose[same][+1] = up
       #pose[same][-1] = down
       
       pose = self.position

       if action == 'right':
           self.position = (pose[0]+1,pose[1])
       elif action == 'left':
           self.position = (pose[0]-1,pose[1])
       elif action == 'up':
           self.position = (pose[0], pose[1]-1)
       elif action == 'down':
           self.position = (pose[0], pose[1]+1)  
           
        

    # and the same is true for the direction the agent is facing, it also
    # needs to be calculated based on whether the agent turned left/right
    # and what direction it was facing when it did
    
    def calculateNextDirection(self,action):
        """
        Altered Original Function: This function calculates which way the agent is facing
        """
        if action == 'right' and self.facing == 'up':
            self.facing = 'right'
        elif action == 'right' and self.facing == 'down':
            self.facing = 'left' #was right
        elif action == 'right' and self.facing =='left':
            self.facing = 'up'
        elif action == 'right' and self.facing == 'right':
            self.facing = 'down'
        elif action == 'left' and self.facing == 'up':
            self.facing = 'left'
        elif action == 'left' and self.facing == 'down':
            self.facing = 'right' #was left
        elif action == 'left' and self.facing == 'left':
            self.facing = 'down'
        elif action == 'left' and self.facing == 'right':
            self.facing = 'up'

       

    # this is the function that will pick the next action of
    # the agent. This is the main function that needs to be
    # modified when you design your new intelligent agent
    # right now it is just a random choice agent
    
    def action(self):
        """
        First we check for glitter, if so grab it
        Next I update myMap, which is my knowledge base
        Each action I create an action scheme, for example if im facing right and want to move up
        I need to pass left (to turn up), then move (to move to that square)
        take_action: direction of cell I want to move to
        schema: how agent can do the action in take_action, once I have a schema I execute it and do nothing else 
        until its done
        """
        # the cell I want to move to is different from the actions that get me there.
        # create an action schema to get there.
        # test for controlled exit at end of successful gui episode

        t = time.time()

        if self.stopTheAgent:
            print("Agent has won this episode.")
            return 'exit' # will cause the episide to end
            
        #reflect action -- get the gold!
        if 'glitter' in self.percepts:
            print("Agent will grab the gold!")
            self.stopTheAgent=True
            return 'grab'
        
        self.updateMyMap()
        
        if len(self.schema) != 0:
            self.calculateNextDirection(self.schema[0])
            return self.schema.pop(0)
        else:
           self.getSurroundingSafeCells()
           self.take_action = self.calculateAction()
           self.schema = self.checkAction(self.take_action)
           self.schema.append('move')
           self.calculateNextPosition(self.take_action)
           self.calculateNextDirection(self.schema[0])
           self.update(self.percepts)
           print('Time: ',time.time()-t)
           return self.schema.pop(0)
           
                              
    def generateMap(self):
        """
        This function gerates a 4x4 list of dictionaries. This is my knowledge base
        Using a dictionary makes it easier to work with.
        I can also keep track of which cells are safe and which cells i visited
        """
        perc_dic = {'safe': None, 'breeze': None, 'stench': None, 'pit': None, 'wumpus': None, 'visited' : False}

        l = []
        for j in range(4):
           l.clear()
           for i in range(4):
               l.append(copy.deepcopy(perc_dic))
           self.myMap.append(copy.copy(l))
           
    def updateMyMap(self):
        """
        This function updates the dictionary in myMap corresponding to the current cell
        with the current percepts
        """
        pose = self.position

        if 'breeze' in self.percepts:
            self.myMap[pose[0]][pose[1]]['breeze'] = True
        else:
            self.myMap[pose[0]][pose[1]]['breeze'] = False
        if 'stench' in self.percepts:
            self.myMap[pose[0]][pose[1]]['stench'] = True
        else:
            self.myMap[pose[0]][pose[1]]['stench'] = False

        self.myMap[pose[0]][pose[1]]['safe'] = True
        self.myMap[pose[0]][pose[1]]['visited'] = True
        

    def generateModels(self):
        """
        When the agent cant make a guarenteed safe move this function is called to generate models based on the KB
        First a generate a list of all the cells with breezes or stenches 
        Then I generate a model corresponding to each breeze/stench with a pit/wumpus in all adjacent cells
        I then 
        Models are only generated based onthe surrounding cells and added to previous models, 
        This is more efficient because I am adding at most 18 dictionaries to the model for one action.
        """

        self.updateMyMap()
        start = copy.deepcopy(self.myMap)
        pose = self.position
        
        cells = (4,4)
        
        breeze_list = []
        stench_list = []

        #pose[+1][same] = right
        #pose[-1][same] = left
        #pose[same][+1] = up
        #pose[same][-1] = down

        for i in range(cells[0]):
            count = 0
            for x in start[i]:
                if x['breeze'] == True:
                    breeze_list.append( (i,count) )
                if x['stench'] == True:
                    stench_list.append( (i,count) )
                count += 1
        print('bl: ',breeze_list)
        for pose in breeze_list:
            temp = copy.copy(start)
            if pose[1] == 3:
                if pose[0] == 0:
                    temp[pose[0]+1][pose[1]]['pit'] = True
                    temp[pose[0]][pose[1]-1]['pit'] = True
                elif pose[0] == 3:
                    temp[pose[0]-1][pose[1]]['pit'] = True
                    temp[pose[0]][pose[1]-1]['pit'] = True
                else:
                    temp[pose[0]+1][pose[1]]['pit'] = True
                    temp[pose[0]-1][pose[1]]['pit'] = True
                    temp[pose[0]][pose[1]-1]['pit'] = True
            elif pose[1] == 0:
                if pose[0] == 0:
                    temp[pose[0]+1][pose[1]]['pit'] = True
                    temp[pose[0]][pose[1]+1]['pit'] = True
                elif pose[0] == 3:
                    temp[pose[0]-1][pose[1]]['pit'] = True
                    temp[pose[0]][pose[1]+1]['pit'] = True
                else:
                    temp[pose[0]+1][pose[1]]['pit'] = True
                    temp[pose[0]-1][pose[1]]['pit'] = True
                    temp[pose[0]][pose[1]+1]['pit'] = True
            elif pose[0] == 0:
                temp[pose[0]+1][pose[1]]['pit'] = True
                temp[pose[0]][pose[1]-1]['pit'] = True
                temp[pose[0]][pose[1]+1]['pit'] = True
            elif pose[0] == 3:
                temp[pose[0]-1][pose[1]]['pit'] = True
                temp[pose[0]][pose[1]-1]['pit'] = True
                temp[pose[0]][pose[1]+1]['pit'] = True
            else:
                temp[pose[0]+1][pose[1]]['pit'] = True
                temp[pose[0]-1][pose[1]]['pit'] = True
                temp[pose[0]][pose[1]-1]['pit'] = True
                temp[pose[0]][pose[1]+1]['pit'] = True

            self.models.append(temp)

        for pose in stench_list:
            temp = copy.copy(start)
            if pose[1] == 3:
                if pose[0] == 0:
                    temp[pose[0]+1][pose[1]]['wumpus'] = True
                    temp[pose[0]][pose[1]-1]['wumpus'] = True
                elif pose[0] == 3:
                    temp[pose[0]-1][pose[1]]['wumpus'] = True
                    temp[pose[0]][pose[1]-1]['wumpus'] = True
                else:
                    temp[pose[0]+1][pose[1]]['wumpus'] = True
                    temp[pose[0]-1][pose[1]]['wumpus'] = True
                    temp[pose[0]][pose[1]-1]['wumpus'] = True
            elif pose[1] == 0:
                if pose[0] == 0:
                    temp[pose[0]+1][pose[1]]['wumpus'] = True
                    temp[pose[0]][pose[1]+1]['wumpus'] = True
                elif pose[0] == 3:
                    temp[pose[0]-1][pose[1]]['wumpus'] = True
                    temp[pose[0]][pose[1]+1]['wumpus'] = True
                else:
                    temp[pose[0]+1][pose[1]]['wumpus'] = True
                    temp[pose[0]-1][pose[1]]['wumpus'] = True
                    temp[pose[0]][pose[1]+1]['wumpus'] = True
            elif pose[0] == 0:
                temp[pose[0]+1][pose[1]]['wumpus'] = True
                temp[pose[0]][pose[1]-1]['wumpus'] = True
                temp[pose[0]][pose[1]+1]['wumpus'] = True
            elif pose[0] == 3:
                temp[pose[0]-1][pose[1]]['wumpus'] = True
                temp[pose[0]][pose[1]-1]['wumpus'] = True
                temp[pose[0]][pose[1]+1]['wumpus'] = True
            else:
                temp[pose[0]+1][pose[1]]['wumpus'] = True
                temp[pose[0]-1][pose[1]]['wumpus'] = True
                temp[pose[0]][pose[1]-1]['wumpus'] = True
                temp[pose[0]][pose[1]+1]['wumpus'] = True

            self.models.append(temp)
        return self.models
    

    def getSurroundingSafeCells(self):
        """
        This function makes surrounding cells safe, meaning if there is no/breeze or stench in the current cell
        all adjecnt cells are also safe, and therefore the agent can make a guarenteed safe move to them
        """

        pose = self.position

        current_cell = self.myMap[pose[0]][pose[1]]
        
        if current_cell['breeze'] != True and current_cell['stench'] != True:
        # this indicates the surrounding cells are safe
            
            if pose[1] == 3:
                if pose[0] == 0:
                    #print('heRe')
                    self.myMap[pose[0]+1][pose[1]]['safe'] = True
                    self.myMap[pose[0]][pose[1]-1]['safe'] = True
                elif pose[0] == 3:
                    self.myMap[pose[0]-1][pose[1]]['safe'] = True
                    self.myMap[pose[0]][pose[1]-1]['safe'] = True
                else:
                    self.myMap[pose[0]+1][pose[1]]['safe'] = True
                    self.myMap[pose[0]-1][pose[1]]['safe'] = True
                    self.myMap[pose[0]][pose[1]-1]['safe'] = True
                     
            elif pose[1] == 0:
                if pose[0] == 0:
                    self.myMap[pose[0]+1][pose[1]]['safe'] = True
                    self.myMap[pose[0]][pose[1]+1]['safe'] = True
                elif pose[0] == 3:
                    self.myMap[pose[0]-1][pose[1]]['safe'] = True
                    self.myMap[pose[0]][pose[1]+1]['safe'] = True
                else:
                    self.myMap[pose[0]+1][pose[1]]['safe'] = True
                    self.myMap[pose[0]-1][pose[1]]['safe'] = True
                    self.myMap[pose[0]][pose[1]+1]['safe'] = True
            elif pose[0] == 0:
                self.myMap[pose[0]+1][pose[1]]['safe'] = True
                self.myMap[pose[0]][pose[1]-1]['safe'] = True
                self.myMap[pose[0]][pose[1]+1]['safe'] = True
            elif pose[0] == 3:
                self.myMap[pose[0]-1][pose[1]]['safe'] = True
                self.myMap[pose[0]][pose[1]-1]['safe'] = True
                self.myMap[pose[0]][pose[1]+1]['safe'] = True
            else:
                self.myMap[pose[0]+1][pose[1]]['safe'] = True
                self.myMap[pose[0]-1][pose[1]]['safe'] = True
                self.myMap[pose[0]][pose[1]-1]['safe'] = True
                self.myMap[pose[0]][pose[1]+1]['safe'] = True
        #print(self.myMap)    
 

    def calculateAction(self):
        """
        This function is used to calculate the next move.
        If one of the adjecnt cells is knowbly safe and has not been visited the agent will go there. 
        If there is more than one adjacent safe cell, one is choosen at random
        If there are no adjacent safe cells hte function uncertainAction is called, which uses models to  
        pick a cell.
 
        """
        pose = self.position
        current_cell = self.myMap[pose[0]][pose[1]]

        possible_moves = []

        if pose[1] == 3:
            if pose[0] == 0:
                if self.myMap[pose[0]+1][pose[1]]['safe'] == True and self.myMap[pose[0]+1][pose[1]]['visited'] == False :
                    possible_moves.append('right')
                if self.myMap[pose[0]][pose[1]-1]['safe'] == True and self.myMap[pose[0]][pose[1]-1]['visited'] == False:
                    possible_moves.append('up')
            elif pose[0] == 3:
                if self.myMap[pose[0]-1][pose[1]]['safe'] == True and self.myMap[pose[0]-1][pose[1]]['visited'] == False:
                    possible_moves.append('left')
                if self.myMap[pose[0]][pose[1]-1]['safe'] == True and self.myMap[pose[0]][pose[1]-1]['visited'] == False:
                    possible_moves.append('up')
            else:
                if self.myMap[pose[0]+1][pose[1]]['safe'] == True and self.myMap[pose[0]+1][pose[1]]['visited'] == False:
                    possible_moves.append('right')
                if self.myMap[pose[0]-1][pose[1]]['safe'] == True and self.myMap[pose[0]-1][pose[1]]['visited'] == False:
                    possible_moves.append('left')
                if self.myMap[pose[0]][pose[1]-1]['safe'] == True and self.myMap[pose[0]][pose[1]-1]['visited'] == False:
                    possible_moves.append('up') 
        elif pose[1] == 0:
            if pose[0] == 0:
                if self.myMap[pose[0]+1][pose[1]]['safe'] == True and self.myMap[pose[0]+1][pose[1]]['visited'] == False:
                    possible_moves.append('right')
                if self.myMap[pose[0]][pose[1]+1]['safe'] == True and self.myMap[pose[0]][pose[1]+1]['visited'] == False:
                    possible_moves.append('down')
            elif pose[0] == 3:
                if self.myMap[pose[0]-1][pose[1]]['safe'] == True and self.myMap[pose[0]-1][pose[1]]['visited'] == False:
                    possible_moves.append('left')
                if self.myMap[pose[0]][pose[1]+1]['safe'] == True and self.myMap[pose[0]][pose[1]+1]['visited'] == False:
                    possible_moves.append('down')
            else:
                if self.myMap[pose[0]+1][pose[1]]['safe'] == True and self.myMap[pose[0]+1][pose[1]]['visited'] == False:
                    possible_moves.append('right')
                if self.myMap[pose[0]-1][pose[1]]['safe'] == True and self.myMap[pose[0]-1][pose[1]]['visited'] == False:
                    possible_moves.append('left')
                if self.myMap[pose[0]][pose[1]+1]['safe'] == True and self.myMap[pose[0]][pose[1]+1]['visited'] == False:
                    possible_moves.append('down')
        elif pose[0] == 0:
            if self.myMap[pose[0]+1][pose[1]]['safe'] == True and self.myMap[pose[0]+1][pose[1]]['visited'] == False:
                possible_moves.append('right')
            if self.myMap[pose[0]][pose[1]-1]['safe'] == True and self.myMap[pose[0]][pose[1]-1]['visited'] == False:
                possible_moves.append('up')
            if self.myMap[pose[0]][pose[1]+1]['safe'] == True and self.myMap[pose[0]][pose[1]+1]['visited'] == False:
                possible_moves.append('down')
        elif pose[0] == 3:
            if self.myMap[pose[0]-1][pose[1]]['safe'] == True and self.myMap[pose[0]-1][pose[1]]['visited'] == False:
                possible_moves.append('left')
            if self.myMap[pose[0]][pose[1]-1]['safe'] == True and self.myMap[pose[0]][pose[1]-1]['visited'] == False:
                possible_moves.append('up')
            if self.myMap[pose[0]][pose[1]+1]['safe'] == True and self.myMap[pose[0]][pose[1]+1]['visited'] == False:
                possible_moves.append('down')
        else:
            if self.myMap[pose[0]+1][pose[1]]['safe'] == True and self.myMap[pose[0]+1][pose[1]]['visited'] == False:
                possible_moves.append('right')
            if self.myMap[pose[0]-1][pose[1]]['safe'] == True and self.myMap[pose[0]-1][pose[1]]['visited'] == False:
                possible_moves.append('left')
            if self.myMap[pose[0]][pose[1]-1]['safe'] == True and self.myMap[pose[0]][pose[1]-1]['visited'] == False:
                possible_moves.append('up')
            if self.myMap[pose[0]][pose[1]+1]['safe'] == True and self.myMap[pose[0]][pose[1]+1]['visited'] == False:
                possible_moves.append('down')
        # this is turned off, this can be turned on and the agent will only move to safe cells 
        # even if they have been visted before
        if len(possible_moves) == math.inf: #currently turned off, set = 0 to turn on
            if pose[1] == 3:
                if pose[0] == 0:
                    if self.myMap[pose[0]+1][pose[1]]['visited'] == True:
                        possible_moves.append('right')
                    if self.myMap[pose[0]][pose[1]-1]['visited'] == True:
                        possible_moves.append('up')
                elif pose[0] == 3:
                    if self.myMap[pose[0]-1][pose[1]]['visited'] == True:
                        possible_moves.append('left')
                    if self.myMap[pose[0]][pose[1]-1]['visited'] == True:
                        possible_moves.append('up')
                else:
                    if self.myMap[pose[0]+1][pose[1]]['visited'] == True:
                        possible_moves.append('right')
                    if self.myMap[pose[0]-1][pose[1]]['visited'] == True:
                        possible_moves.append('left')
                    if self.myMap[pose[0]][pose[1]-1]['visited'] == True:
                        possible_moves.append('up') 
            elif pose[1] == 0:
                if pose[0] == 0:
                    if self.myMap[pose[0]+1][pose[1]]['visited'] == True:
                        possible_moves.append('right')
                    if self.myMap[pose[0]][pose[1]+1]['visited'] == True:
                        possible_moves.append('down')
                elif pose[0] == 3:
                    if self.myMap[pose[0]-1][pose[1]]['visited'] == True:
                        possible_moves.append('left')
                    if self.myMap[pose[0]][pose[1]+1]['visited'] == True:
                        possible_moves.append('down')
                else:
                    if self.myMap[pose[0]+1][pose[1]]['visited'] == True:
                        possible_moves.append('right')
                    if self.myMap[pose[0]-1][pose[1]]['visited'] == True:
                        possible_moves.append('left')
                    if self.myMap[pose[0]][pose[1]+1]['visited'] == True:
                        possible_moves.append('down')
            elif pose[0] == 0:
                if self.myMap[pose[0]+1][pose[1]]['visited'] == True:
                    possible_moves.append('right')
                if self.myMap[pose[0]][pose[1]-1]['visited'] == True:
                    possible_moves.append('up')
                if self.myMap[pose[0]][pose[1]+1]['visited'] == True:
                    possible_moves.append('down')

            elif pose[0] == 3:
                if self.myMap[pose[0]-1][pose[1]]['visited'] == True:
                    possible_moves.append('left')
                if self.myMap[pose[0]][pose[1]-1]['visited'] == True:
                    possible_moves.append('up')
                if self.myMap[pose[0]][pose[1]+1]['visited'] == True:
                    possible_moves.append('down')
            else:
                if self.myMap[pose[0]+1][pose[1]]['visited'] == True:
                    possible_moves.append('right')
                if self.myMap[pose[0]-1][pose[1]]['visited'] == True:
                    possible_moves.append('left')
                if self.myMap[pose[0]][pose[1]-1]['visited'] == True:
                    possible_moves.append('up')
                if self.myMap[pose[0]][pose[1]+1]['visited'] == True:
                    possible_moves.append('down')

        # if no guarneteed safe moves
        if len(possible_moves) == 0:
            model = self.generateModels()
            move = self.uncertainAction()
            possible_moves.append(move)

        # if there more than one possible move, choose one at random
        if len(possible_moves) != 0:
            x = randint(0,len(possible_moves)-1)
            return possible_moves[x]
        else:
            print('stuck')
            quit()

    def checkAction(self, action):
        """
        This function takes the desired action and calculates the action schema
        action: cell we want to move to: up, down, left, right
        self.facing: the way the agent is facing
        returns: a list of actions for agent to get to desired cell
        """
        print('facing: ',self.facing)
        print('action: ',action)
        if self.facing == action:
            return []
        elif action == 'left' and self.facing == 'right':
            return ['left','left']
        elif action == 'right' and self.facing == 'left':
            return ['right', 'right']
        elif action == 'up' and self.facing == 'down':
            return ['left','left']
        elif action == 'down' and self.facing == 'up':
            return ['right','right']
        elif action == 'right' and self.facing == 'up':
            return ['right']
        elif action == 'right' and self.facing == 'down':
            return ['left']
        elif action == 'left' and self.facing == 'up':
            return ['left'] 
        elif action == 'left' and self.facing == 'down':
            return ['right']
        elif action == 'up' and self.facing == 'left':
            return ['right']
        elif action == 'up' and self.facing == 'right':
            return ['left']
        elif action == 'down' and self.facing == 'right':
            return ['right']
        elif action == 'down' and self.facing == 'left':
            return ['left']


    def uncertainAction(self):
        """
        This function looks at the models and counts how many pits/wumpus are in adjecnt cells
        according to all the models created.
        We then choose the move that corresponds to the smallest number of pits/wumpus
        If there are an equal number, an action is choosen at random
        """

        pose = self.position
        #pose[+1][same] = right
        #pose[-1][same] = left
        #pose[same][-1] = up
        #pose[same][+1] = down

        #counter varaibles for each possible move
        counter_up = 0
        counter_down = 0
        counter_left = 0
        counter_right = 0

        model = self.models

        for i in range(len(model)):
            if pose[1] == 3:
                if pose[0] == 0:
                    if model[i][pose[0]+1][pose[1]]['pit'] == True:
                        counter_right += 1
                    if model[i][pose[0]][pose[1]-1]['pit'] == True:
                        counter_up += 1
                elif pose[0] == 3:
                    if model[i][pose[0]-1][pose[1]]['pit'] == True:
                        counter_left += 1
                    if model[i][pose[0]][pose[1]-1]['pit'] == True:
                        counter_up += 1
                else:
                    if model[i][pose[0]+1][pose[1]]['pit'] == True:
                        counter_right += 1
                    if model[i][pose[0]-1][pose[1]]['pit'] == True:
                        counter_left += 1
                    if model[i][pose[0]][pose[1]-1]['pit'] == True:
                        counter_up += 1
            elif pose[1] == 0:
                if pose[0] == 0:
                    if model[i][pose[0]+1][pose[1]]['pit'] == True:
                        counter_right += 1
                    if model[i][pose[0]][pose[1]+1]['pit'] == True:
                        counter_down += 1
                elif pose[0] == 3:
                    if model[i][pose[0]-1][pose[1]]['pit'] == True:
                        counter_left += 1
                    if model[i][pose[0]][pose[1]+1]['pit'] == True:
                        counter_down += 1
                else:
                    if model[i][pose[0]+1][pose[1]]['pit'] == True:
                        counter_right += 1
                    if model[i][pose[0]-1][pose[1]]['pit'] == True:
                        counter_left += 1
                    if model[i][pose[0]][pose[1]+1]['pit'] == True:
                        counter_down += 1
            elif pose[0] == 0:
                if model[i][pose[0]+1][pose[1]]['pit'] == True:
                    counter_right += 1
                if model[i][pose[0]][pose[1]-1]['pit'] == True:
                    counter_up += 1
                if model[i][pose[0]][pose[1]+1]['pit'] == True:
                    counter_down += 1
            elif pose[0] == 3:
                if model[i][pose[0]-1][pose[1]]['pit'] == True:
                    counter_left +=1
                if model[i][pose[0]][pose[1]-1]['pit'] == True:
                    counter_up += 1
                if model[i][pose[0]][pose[1]+1]['pit'] == True:
                    counter_down += 1
            else:
                if model[i][pose[0]+1][pose[1]]['pit'] == True:
                    counter_right += 1
                if model[i][pose[0]-1][pose[1]]['pit'] == True:
                    counter_left += 1
                if model[i][pose[0]][pose[1]-1]['pit'] == True:
                    counter_up += 1
                if model[i][pose[0]][pose[1]+1]['pit'] == True:
                    counter_down += 1

            if pose[1] == 3:
                if pose[0] == 0:
                    if model[i][pose[0]+1][pose[1]]['wumpus'] == True:
                        counter_right += 1
                    if model[i][pose[0]][pose[1]-1]['wumpus'] == True:
                        counter_up += 1
                elif pose[0] == 3:
                    if model[i][pose[0]-1][pose[1]]['wumpus'] == True:
                        counter_left += 1
                    if model[i][pose[0]][pose[1]-1]['wumpus'] == True:
                        counter_up += 1
                else:
                    if model[i][pose[0]+1][pose[1]]['wumpus'] == True:
                        counter_right += 1
                    if model[i][pose[0]-1][pose[1]]['wumpus'] == True:
                        counter_left += 1
                    if model[i][pose[0]][pose[1]-1]['wumpus'] == True:
                        counter_up += 1
            elif pose[1] == 0:
                if pose[0] == 0:
                    if model[i][pose[0]+1][pose[1]]['wumpus'] == True:
                        counter_right += 1
                    if model[i][pose[0]][pose[1]+1]['wumpus'] == True:
                        counter_down += 1
                elif pose[0] == 3:
                    if model[i][pose[0]-1][pose[1]]['wumpus'] == True:
                        counter_left += 1
                    if model[i][pose[0]][pose[1]+1]['wumpus'] == True:
                        counter_down += 1
                else:
                    if model[i][pose[0]+1][pose[1]]['wumpus'] == True:
                        counter_right += 1
                    if model[i][pose[0]-1][pose[1]]['wumpus'] == True:
                        counter_left += 1
                    if model[i][pose[0]][pose[1]+1]['wumpus'] == True:
                        counter_down += 1
            elif pose[0] == 0:
                if model[i][pose[0]+1][pose[1]]['wumpus'] == True:
                    counter_right += 1
                if model[i][pose[0]][pose[1]-1]['wumpus'] == True:
                    counter_up += 1
                if model[i][pose[0]][pose[1]+1]['wumpus'] == True:
                    counter_down += 1
            elif pose[0] == 3:
                if model[i][pose[0]-1][pose[1]]['wumpus'] == True:
                    counter_left +=1
                if model[i][pose[0]][pose[1]-1]['wumpus'] == True:
                    counter_up += 1
                if model[i][pose[0]][pose[1]+1]['wumpus'] == True:
                    counter_down += 1
            else:
                if model[i][pose[0]+1][pose[1]]['wumpus'] == True:
                    counter_right += 1
                if model[i][pose[0]-1][pose[1]]['wumpus'] == True:
                    counter_left += 1
                if model[i][pose[0]][pose[1]-1]['wumpus'] == True:
                    counter_up += 1
                if model[i][pose[0]][pose[1]+1]['wumpus'] == True:
                    counter_down += 1

        moves = []
        move_string = ['up','down','left','right']
        # save te counters in a list
        # if counter is 0 is not a viable action so we set it to infiity
        if counter_up != 0:
            moves.append(counter_up)
        else:
            moves.append(math.inf)
        if counter_down != 0:
            moves.append(counter_down)
        else:
            moves.append(math.inf)
        if counter_left != 0:
            moves.append(counter_left)
        else:
            moves.append(math.inf)
        if counter_right != 0:
            moves.append(counter_right)
        else:
            moves.append(math.inf)
        
        # take the min values of pits/ wummpus and get its corresponding action
        min_val = min(moves)
        possible_moves = []

        for i in range(4):
            if min_val == moves[i]:
                possible_moves.append(move_string[i]) 

        # choose a random action if mroe than one action is possible   
        x = randint(0,len(possible_moves)-1)
        return possible_moves[x]






