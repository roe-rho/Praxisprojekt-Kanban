import time
import threading
import random
import datetime
import json
import os

# NEW: Thread lock for safe access to shared board data
lock = threading.Lock()

running = False
config_updated = False
initial_gen = False
tick_interval = 1  # Initialize tick_interval globally
#backlog = column[0]
#done = column[num_columns - 1]

######################################################################################################################################################################################################################################
#Classes
class Column:
    def __init__(self, id, name, max_tasks, workers_column, processing_time):
        self.id = id #Column ID
        self.name = name #Column name
        self.tasks = [] #List of tasks currently in the column
        self.max_tasks = max_tasks #Maximum number of tasks that can be in the column at once (WIP limit)
        self.workers = workers_column #Number of workers assigned to the column (Unused)
        self.processing_time = processing_time #Time it takes to process a task in the column
    
    def __repr__(self):
        return f"Column(id={self.id}, name='{self.name}', tasks={len(self.tasks)}/{self.max_tasks}, workers={self.workers}), processing_time={self.processing_time})"

class Task:
    def __init__(self, id, name, created_at, done_at=None, worker_task=None, status=None, processing_duration=None):
        self.id = id #Task ID
        self.name = name #Task name
        self.created_at = created_at #Time the task was created
        self.done_at = done_at #Time the task was completed
        self.worker_task = worker_task #Worker assigned to the task
        self.status = status #Current status of the task
        self.processing_duration = processing_duration #start from when the task starts processing until it reaches the end column.
    
    def __repr__(self):
        return f"Task(id={self.id}, name='{self.name}', created_at='{self.created_at}', done_at='{self.done_at}', worker_task='{self.worker_task}', status='{self.status}', processing_duration='{self.processing_duration}')"

class Board:
    def __init__(self, total_columns):
        self.columns = []   #List of columns in the board
        self.total_columns = total_columns  #Total number of columns in the board

########################################################################################################################################################################################################################################

def tick_manager():
    global tick
    global tick_interval
    global running
    global clock
    global day

    #Time and tick management
    tick = tick + 1 #Every tick interval, the tick count increases by 1
    clock = clock + 0.10 #Every tick adds 10 minutes to the clock

    #If the minutes exceed 60, we add 40 minutes to the clock to move to the next hour
    if clock%1 >= 0.50:
        clock = clock + 0.40

    #If the clock exceeds 5 PM, we reset it to 9 AM and move to the next day (assuming a 9-5 workday)
    if clock >= 17.00:
        clock = 9.00
        day = day + 1


def generate_columns(n):
    global num_columns
    global board_1
    global tick_interval
    num_columns = n

    #backend_dir = os.path.dirname(os.path.abspath(__file__))
    #config_path = os.path.join(backend_dir, 'config.json')

    #if not os.path.exists(config_path):
        #print(f"Config file not found at {config_path}. Using default configuration.")
        #return
    
    #try:
        #with open(config_path, 'r') as f:
            #new_config = json.load(f)
        
        #print(f"DEBUG update_column_config - Loaded config: {new_config}")
    #except Exception as e:
        #print(f"Error loading config: {e}. Using default configuration.")

    #Generate n number of columns (Unused, default = 3)
    board_1 = Board(total_columns=n)
    
    #Assign column attributes (i = number ie. Column 0, 1, 2, etc)
    for i in range(n):
        
        col = Column(
            id=i,
            name=f"Column {i}",
            max_tasks=5,  # Get WIP limit from config.json
            workers_column=2,   #Unused, default = 2 workers per column
            processing_time=10*tick_interval    #Default processing time is 10 ticks (10 seconds if tick_interval is 1 second)
        )

        #if config_updated == True:
            #col.max_tasks = int(new_config.get(f"column_{i}", col.max_tasks))  # Update max_tasks if config has been updated
            


        
        board_1.columns.append(col)
    



def update_WIP_limit():
     
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(backend_dir, 'config.json')

    if not os.path.exists(config_path):
        print(f"Config file not found at {config_path}. Using default configuration.")
        return
    
    try:
        with open(config_path, 'r') as f:
            new_config = json.load(f)
        
        print(f"DEBUG update_column_config - Loaded config: {new_config}")
    except Exception as e:
        print(f"Error loading config: {e}. Using default configuration.")
    
    for i in range(num_columns):       
        board_1.columns[i].max_tasks = int(new_config.get(f"column_{i}"))
        

def generate_task(): #In Backlog (Column 0)
    global id

    #If the backlog (column 0) has space for more tasks, generate a new task and add it to the backlog
    if len(board_1.columns[0].tasks) < board_1.columns[0].max_tasks:
        id = id+1
        task = Task(
            id=id,
            name=f"Task {id}",
            created_at=f"Day: {day}, Time: {round(clock, 3)}"
        )
        board_1.columns[0].tasks.append(task)
        

def process_tasks(col): # For columns 1 to n-2, process tasks and move them to the next column if they are done

#If the previous column has tasks and the current column has space, move a task from the previous column to the current column

    if len(board_1.columns[col - 1].tasks) > 0 and len(board_1.columns[col].tasks) < board_1.columns[col].max_tasks:
        task = board_1.columns[col - 1].tasks.pop(0)    #Remove the first task from the previous column
        board_1.columns[col].tasks.append(task)     #Add the task to the current column

            
    if len(board_1.columns[col].tasks) > 0:
        # Iterate backwards to safely remove items during iteration
        for i in range(len(board_1.columns[col].tasks) - 1, -1, -1):
            task = board_1.columns[col].tasks[i]

            #If the task has just been moved to the column and has no status, set its status to the processing time of the column
            if task.status is None:
                task.status = board_1.columns[col].processing_time
            

            task.status = task.status - tick_interval   #Decrease the task's status by the tick interval to simulate processing time
    
            #If task is done (status <= 0) and it's not the last column, move it to the next column if there is space
            if task.status <= 0 and i == 0:
                if col + 2 < num_columns and  len(board_1.columns[col + 1].tasks) < board_1.columns[col + 1].max_tasks:
                    board_1.columns[col].tasks.remove(task)
                    board_1.columns[col + 1].tasks.append(task)
                    task.status = None
                
                elif col + 2 >= num_columns: #Potential redundancy, but ensures that tasks in the second to last column can move to the last column even if the last column is full.
                    board_1.columns[col].tasks.remove(task)
                    board_1.columns[col + 1].tasks.append(task)
                    task.status = None



            

def done_tasks():
    #If the last column has tasks and the first task in the last column is done, remove it from the board and set its done_at time
    if num_columns%2 != 0:
        if len(board_1.columns[num_columns - 1].tasks) >= board_1.columns[num_columns - 1].max_tasks + 1:
             
            task = board_1.columns[num_columns - 1].tasks.pop(0)
            task.done_at = f"Day: {day}, Time: {round(clock, 3)}"

            


    


        

def main():
    global num_columns
    global running
    global board_1
    global tick_interval
    global tick
    global id
    global clock
    global day
    global config_updated
    global initial_gen
    #running = True
    tick_interval = 1  # 1 second per tick default
    tick = 0
    id = 0
    clock = 9.00
    day = 1
    initial_gen = False

    num_columns = 3

    
    if running == True:
        print("Running...")
    
    generate_columns(num_columns)

    
    if config_updated == True:
        update_WIP_limit()
        config_updated = False


    

    while running:
        if config_updated == True:
            update_WIP_limit()
            config_updated = False
        tick_manager()
        generate_task()
        for i in range(num_columns):
            if i%2 != 0 and i < num_columns - 1:
                process_tasks(i)
        done_tasks()
        if running == False:
            #print("Stopped.")
            break
        time.sleep(tick_interval)




def test_board():
    global num_columns
    global running
    global board_1
    global tick_interval
    global tick
    global id
    global clock
    global day
    running = True
    tick_interval = 1  # 1 second per tick for testing
    tick = 0
    id = 0
    clock = 9.00
    day = 1



    test = 0
    while test == 0:
        test = int(input("Enter test number (1: column generation, 2: task generation, 3: task processing, 4: tick manager, 5: bottleneck test, 10: all tests): "))

    #Test tick manager
    if test == 4 or test == 10:
        if running == False:
            running = True
        
        while running:
            tick_manager()
            time.sleep(tick_interval)
        
        


    # Test column generation
    if test == 1 or test == 10:
        num_columns = random.randint(3,6)
        generate_columns(num_columns)
        print(f"num_columns: {num_columns}")
        print(board_1.columns)
        if len(board_1.columns) == num_columns:
            print("\nTest passed: Correct number of columns generated.\n")
    
    # Test task generation
    if test == 2 or test == 10:
        generate_columns(1)

        while running:
            tick_manager()
            generate_task()
            if len(board_1.columns[0].tasks) > 0:
                print("\nTest passed: Tasks generated in backlog.\n")
            
            
            if len(board_1.columns[0].tasks) < board_1.columns[0].max_tasks:
                print("\nTest passed: Backlog does not exceed max tasks.\n")
                
            if len(board_1.columns[0].tasks) >= board_1.columns[0].max_tasks:
                print("\nBacklog full\n")
                running = False
                break
                    
            
            time.sleep(tick_interval)
    
    #Test task processing
    if test == 3 or test == 10:
        num_columns = 5
        generate_columns(num_columns)

        while running:
            tick_manager()
            x = random.randint(1,2)
            if x == 1:
                generate_task()
            for i in range(num_columns):
                if i%2 != 0 and i < num_columns - 1:
                    process_tasks(i)
            for i in range(num_columns):
                tasks_display = [f"{task.name} (status: {task.status})" for task in board_1.columns[i].tasks]
                print(f"\nColumn {i}: {tasks_display}\n")
            done_tasks()
            time.sleep(tick_interval)
    
    #Bottleneck test
    if test == 5:
        num_columns = 5
        generate_columns(num_columns)
        for i in range(num_columns - 1 ):
                board_1.columns[i + 1].max_tasks = board_1.columns[i].max_tasks - 2  # Set low max tasks to create bottleneck
                if board_1.columns[i + 1].max_tasks < 1:
                    board_1.columns[i + 1].max_tasks = 1  # Ensure at least 1 task can be held
                board_1.columns[i + 1].processing_time = board_1.columns[i].processing_time + 2*tick_interval  # Increase processing time to create bottleneck
                print(f"Column {i} processing time set to {board_1.columns[i].processing_time}")
                print(f"Column {i} max tasks set to {board_1.columns[i].max_tasks}")

        while running:
            tick_manager()
            generate_task()
            for i in range(num_columns):
                if i%2 != 0 and i < num_columns - 1:
                    process_tasks(i)
                # Display only task name and status
                
            for i in range(num_columns):
                tasks_display = [f"{task.name} (status: {task.status})" for task in board_1.columns[i].tasks]
                tasks_processing = [f"{task.name} (processing duration: {task.processing_duration})" for task in board_1.columns[i].tasks if task.status is not None and task.status < board_1.columns[i].processing_time]
                print(f"\nColumn {i}: {tasks_display}\n")
                print(f"Column {i} processing tasks: {tasks_processing}\n")
            done_tasks()
            time.sleep(tick_interval)

    #WIP Limit Test
    if test==6:
        x = 0
        num_columns = 3
        generate_columns(num_columns)
        while running:
            if x == 5:
                update_WIP_limit()
                for i in range(num_columns):
                    print(f"Updated config : Column{i} = {board_1.columns[i].max_tasks}")
                x = 0
            tick_manager()
            generate_task()
            for i in range(num_columns):
                if i%2 != 0 and i < num_columns - 1:
                    process_tasks(i)
            for i in range(num_columns):
                tasks_display = [f"{task.name} (status: {task.status})" for task in board_1.columns[i].tasks]
                print(f"\nColumn {i}: {tasks_display}\n")
            done_tasks()
            time.sleep(tick_interval)
            x=x+1


    #Test all
    if test == 7 or test == 10:
        num_columns = 3
        generate_columns(num_columns)
        while running:
            tick_manager()
            generate_task()
            for i in range(num_columns):
                if i%2 != 0 and i < num_columns - 1:
                    process_tasks(i)
            for i in range(num_columns):
                tasks_display = [f"{task.name} (status: {task.status})" for task in board_1.columns[i].tasks]
                print(f"\nColumn {i}: {tasks_display}\n")
            done_tasks()
            time.sleep(tick_interval)
        

 

    
    
    



if __name__ == "__main__":
    #main()
    test_board()
