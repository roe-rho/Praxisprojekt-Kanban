import time
import threading
import random
import datetime
import json
import os

# NEW: Thread lock for safe access to shared board data
lock = threading.Lock()
start_event = threading.Event()
paused_event = threading.Event()

running = False
paused = False
config_updated = False
initial_gen = False
tick_interval = 1  # Initialize tick_interval globally

# Initialize global variables at module level to prevent AttributeErrors
clock = 9.00
day = 1
tick = 0
id = 0
num_columns = 3
board_1 = None

#backlog = column[0]
#done = column[num_columns - 1]

######################################################################################################################################################################################################################################
#Classes
class Column:
    def __init__(self, id, name, max_tasks, workers_column, initial_workers_column, processing_time, average_cycle_time_column=0):
        self.id = id #Column ID
        self.name = name #Column name
        self.tasks = [] #Tasks in Column
        self.max_tasks = max_tasks #WIP limit
        self.workers = workers_column #Number of column workers
        self.initial_workers = initial_workers_column #Initial number of column workers (NEW NEW!)
        self.processing_time = processing_time #Time it takes to process a task in the column
        self.average_cycle_time_column = average_cycle_time_column  # Unused

    def __repr__(self):
        return f"Column(id={self.id}, name='{self.name}', tasks={len(self.tasks)}/{self.max_tasks}, workers={self.workers}),initial_workers={self.initial_workers}, processing_time={self.processing_time}, average_cycle_time={self.average_cycle_time_column})"

class Task:
    def __init__(self, id, name, created_at, created_tick=None, done_at=None, done_tick=None, worker_task=None, status=None, cycle_time=None, current_column=None):
        self.id = id #Task ID
        self.name = name #Task name
        self.created_at = created_at #Time the task was created
        self.created_tick = created_tick  # Tick at which the task was created
        self.done_at = done_at #Time the task was completed
        self.done_tick = done_tick  # Tick at which the task was completed
        self.worker_task = worker_task #Worker assigned to the task
        self.status = status #Current status of the task
        self.cycle_time = cycle_time #Time it takes for the task to go from start to finish
        self.lead_time = None  # Time from task creation to completion (calculated when task is done)
        self.current_column = current_column  # Track the current column of the task for progress calculation (NEW NEW!)
        self.cycle_time_column = []  # List to track cycle time spent in each column for the task (NEW NEW!)
        self.column_history = []  # Dictionary to track cycle time spent in each column for the task (NEW NEW!)
        self.column_entry_time = []  # List to track the tick at which the task entered each column (NEW NEW!)
        self.column_exit_time = []  # List to track the tick at which the task exited each column (NEW NEW!)
        self.column_entry_tick = []  # Tick at which the task entered the current column (NEW NEW!)

    
    def __repr__(self):
        return f"Task(id={self.id}, name='{self.name}', created_at='{self.created_at}', done_at='{self.done_at}', worker_task='{self.worker_task}', status='{self.status}', cycle_time='{self.cycle_time}', current_column='{self.current_column}'), lead_time='{self.lead_time}'), cycle_time_column='{self.cycle_time_column}'), column_entry_time='{self.column_entry_time}'), column_exit_time='{self.column_exit_time}')"

class Board:
    def __init__(self, total_columns):
        self.columns = []   #List of columns in the board
        self.total_columns = total_columns  #Total number of columns in the board
        self.total_wip = 0  #Total WIP limit for the board
        self.average_cycle_time = 0  #Average cycle time for completed tasks
        self.average_lead_time = 0  #Average lead time for completed tasks
        self.completed_tasks = []  #Total number of completed tasks
        self.completed_tasks_count = 0  #Total number of completed tasks (counter)
        self.throughput = 0  #Throughput of the board (tasks completed per week)
        self.configs = []  #List of configuration changes made to the board (NEW NEW!)

########################################################################################################################################################################################################################################

def tick_manager():
    global tick
    global tick_interval
    global running
    global clock
    global day

    #Time and tick management
    tick = tick + 1 #Every tick interval, the tick count increases by 1
    clock = clock + 0.10 #Every tick adds 10 minutes to the clock #ronaz`n's comment 9.00 -> 9.10 -> 9.20 -> 9.30 -> 9.40 -> 9.50

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

    #Generate n number of columns (Unused, default = 3)
    board_1 = Board(total_columns=n)
    
    #Assign column attributes
    for i in range(n):
        
        col = Column(
            id=i,
            name=f"Column {i}",
            max_tasks=5,  # Initial WIP Limit
            initial_workers_column=2,  # Initial worker count
            workers_column=2,   # Current worker count
            processing_time=10    #Default processing time (10 minutes per tick)
        )

        if col.id == 0 or col.id == n-1:
            col.processing_time = 0  # Set processing time to 0 for the first and last columns
            col.workers = 0  # Set workers to 0 for the first and last columns since they don't process tasks
        
        
        board_1.columns.append(col)
        #Initial column config (NEW NEW!)
        board_1.configs.append({
            'Column id': col.id,
            'Column name': col.name,
            'Initial WIP Limit': col.max_tasks,
            'Initial Total Workers': col.initial_workers
        })

def generate_task(): #In Backlog (Column 0)
    global id

    with lock:
        #If the backlog (column 0) has space for more tasks, generate a new task and add it to the backlog
        if len(board_1.columns[0].tasks) < board_1.columns[0].max_tasks:
            id = id+1
            task = Task(
                id=id,
                name=f"Task {id}",
                created_at=f"Day: {day}, Time: {round(clock, 3)}",
                created_tick = tick,
                worker_task = 0,
                cycle_time = 0,
                current_column = 0
            )
            board_1.columns[0].tasks.append(task)
            task.column_entry_time.append(f"{clock:.2f}")  # Record the time the task entered the backlog
            

def process_tasks(col):

#If the previous column has tasks and the current column has space, move a task from the previous column to the current column
    with lock:
        if col == 0 and len(board_1.columns[col].tasks) > 0 and len(board_1.columns[col + 1].tasks) < board_1.columns[col + 1].max_tasks:
            task = board_1.columns[col].tasks.pop(0)    #Remove the first task from the previous column
            board_1.columns[col + 1].tasks.append(task)     #Add the task to the current column
            task.column_entry_tick.append(tick)  # Record the tick at which the task entered the new column
            task.column_entry_time.append(f"{clock:.2f}")  # Record the time the task entered the new column
            task.column_exit_time.append(f"{clock:.2f}")  # Record the time the task exited the previous column
            backlog_cycle_time = tick - task.created_tick  # Calculate cycle time in ticks for the backlog
            task.cycle_time_column.append(backlog_cycle_time)  # Record the cycle time for the backlog

        if len(board_1.columns[col].tasks) > 0 and col != 0 and col != num_columns - 1:

            # Iterate backwards to safely remove items during iteration
            for i in range(len(board_1.columns[col].tasks) -1, -1, -1):
                task = board_1.columns[col].tasks[i]

                #If the task has just been moved to the column and has no status, set its status to the processing time of the column
                if task.status is None:
                    task.status = board_1.columns[col].processing_time

                if task.worker_task > 0:
                    task.status = task.status - 1   #Decrease the task's status by the tick interval to simulate processing time
                
                task.current_column = col  # Update the task's current column for progress calculation
        
                #If task is done (status <= 0) and it's not the last column, move it to the next column if there is space
                if col + 2 < num_columns and  len(board_1.columns[col + 1].tasks) < board_1.columns[col + 1].max_tasks and task.status <= 0 and task.worker_task <= 0 and i == 0:
                    board_1.columns[col].tasks.remove(task)
                    board_1.columns[col + 1].tasks.append(task)
                    task.status = None
                    task.column_entry_tick.append(tick)  # Record the tick at which the task entered the new column
                    task.column_entry_time.append(f"{clock:.2f}")  # Record the time the task entered the new column
                    task.column_exit_time.append(f"{clock:.2f}")  # Record the time the task exited the previous column
                    col_cycle_time = tick - task.column_entry_tick[-2]  # Calculate cycle time in ticks for the current column
                    task.cycle_time_column.append(col_cycle_time*10)  # Record the cycle time for the current column
                    
                #Handles the second last column (before done column)
                elif col + 2 >= num_columns and col == num_columns - 2 and col != 0 and task.status <= 0 and task.worker_task <= 0 and i == 0:
                    board_1.columns[col].tasks.remove(task)
                    board_1.columns[col + 1].tasks.append(task)
                    task.status = 'Completed'
                    task.column_entry_tick.append(tick)
                    task.column_exit_time.append(f"{clock:.2f}")  # Record the time the task exited the previous column
                    col_cycle_time = tick - task.column_entry_tick[-2]  # Calculate cycle time in ticks for the current column
                    task.cycle_time_column.append(col_cycle_time*10)  # Record the cycle time for the current column
                    
                    task.done_at = f"Day: {day}, Time: {round(clock, 3)}"
                    task.done_tick = tick
                    task.lead_time = (task.done_tick - task.created_tick)*10  # Calculate lead time in ticks

        
                
                

            #Worker assignment logic
            for j in range(len(board_1.columns[col].tasks)):
                task = board_1.columns[col].tasks[j]
                if task.worker_task == 0 and board_1.columns[col].workers > 0 and task.status > 0:
                    task.worker_task = 1
                    board_1.columns[col].workers -= 1  
                
                elif task.worker_task > 0 and task.status <= 0:
                    task.worker_task = 0 
                    board_1.columns[col].workers += 1 
            

#Move tasks from done column to invisible column
def done_tasks():
    with lock:
        if len(board_1.columns[num_columns - 1].tasks) >= board_1.columns[num_columns - 1].max_tasks + 1:
            task = board_1.columns[num_columns - 1].tasks.pop(0)
            board_1.completed_tasks.append(task)
            task.status = "Completed"
    


def update_config():
    global tick_interval
     
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
        if i != 0 and i != num_columns - 1:
            for j in range(len(board_1.columns[i].tasks)-1, -1, -1):
                task = board_1.columns[i].tasks[j]
                if task.worker_task > 0:
                    task.worker_task = 0
            board_1.columns[i].workers = int(new_config.get(f"workers_{i}", board_1.columns[i].workers))  # Update workers if specified in config, otherwise keep current value
            board_1.columns[i].initial_workers = int(new_config.get(f"workers_{i}", board_1.columns[i].initial_workers))  # Update initial workers if specified in config, otherwise keep current value

    if "tick_interval" in new_config and new_config["tick_interval"] != tick_interval:
        tick_interval =  float(new_config.get("tick_interval", tick_interval))  # Update tick interval if specified in config, otherwise keep current value
        print(f"Tick interval updated to {tick_interval} seconds.")
    
        #Add config change to board_1.configs for export (NEW NEW!)
        board_1.configs.append({
            '[CONFIG]': '[UPDATED]',
            'Update Time [Day, Time]': f"Day: {day}, Time: {f'{clock:.2f}'}",
            'Updated WIP Limits': {f"column_{i}": board_1.columns[i].max_tasks for i in range(num_columns)},
            'Updated Total Workers': {f"column_{i}": board_1.columns[i].initial_workers for i in range(num_columns)},
        })

def metrics_management(col):

    with lock:
        #Cycle Time Management
        if col != 0 and col != num_columns - 1:
            for task in board_1.columns[col].tasks:
                task.cycle_time += 10  #Increase cycle time by 10 minutes for every tick the task is being processed
                task.cycle_time = round(task.cycle_time, 2)  # Round cycle time to 2 decimal places for cleaner display
        
        
        #Calculate average cycle time for completed tasks
        cycle_times = []
        for task in board_1.columns[col].tasks:
            if task.cycle_time is not None:
                cycle_times.append(task.cycle_time)
                
        for task in board_1.completed_tasks:
            if task.cycle_time is not None:
                cycle_times.append(task.cycle_time)

        average_cycle_time = round(sum(cycle_times) / len(cycle_times), 2) if cycle_times else 0
        board_1.average_cycle_time = average_cycle_time


        #Calculate average lead time
        lead_times = []
        for task in board_1.completed_tasks:
            if task.lead_time is not None:
                lead_times.append(task.lead_time)
        
        for task in board_1.columns[num_columns - 1].tasks:
            if task.lead_time is not None:
                lead_times.append(task.lead_time)

        average_lead_time = round(sum(lead_times) / len(lead_times), 2) if lead_times else 0
        board_1.average_lead_time = round(average_lead_time, 2) if average_lead_time else 0

        #throughput calculation
        throughput = (len(board_1.completed_tasks) + len(board_1.columns[num_columns - 1].tasks)) / day if day > 0 else 0  # Throughput is the sum of completed tasks and tasks in the done column
        board_1.throughput = round(throughput, 2)

        #Completed Task Calculation
        board_1.completed_tasks_count = len(board_1.completed_tasks) + len(board_1.columns[num_columns - 1].tasks)  #Total completed tasks is the sum of tasks in the done column and the completed tasks list
        

                
        #Total WIP
        board_1.total_wip = sum(len(board_1.columns[i].tasks) for i in range(1, num_columns - 1))  # Total WIP is the sum of tasks in all columns except backlog and done
    

            


    


        

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
    tick = 0
    id = 0
    clock = 9.00
    day = 1
    initial_gen = False
    tick_interval = 1  # 1 second per tick
    x=tick_interval

    num_columns = 6

    
    if start_event.is_set():
        print("Running...")
    
    generate_columns(num_columns)

    
    if config_updated == True:
        update_config()
        config_updated = False


    

    while start_event.is_set():
        while paused_event.is_set():
            time.sleep(0.1)  # Sleep briefly to reduce CPU usage while paused
            continue  # Skip the rest of the loop and stay in the paused state
        if config_updated == True:
            update_config()
            config_updated = False
        tick_manager()
        generate_task()
        for i in range(num_columns):
            process_tasks(i)
            metrics_management(i)
        done_tasks()
        if start_event.is_set() == False:
            #print("Stopped.")
            break

        while x > 0:
            time.sleep(0.1)
            x = x - 0.1
            while paused_event.is_set():
                time.sleep(0.1)
            if config_updated == True:
                update_config()
                config_updated = False
            continue
        x = tick_interval  # Reset x to the current tick interval for the next loop iteration



##################################################################################################################################################################################################################

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
    if test == 1:
        print("Please input the number of columns for the board:")
        num_columns = int(input())
        generate_columns(num_columns)
        print(f"num_columns: {num_columns}")
        print(board_1.columns)
        if len(board_1.columns) == num_columns:
            print("\nTest passed: Correct number of columns generated.\n")
    
    # Test task generation
    if test == 2:
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
    if test == 3:
        print("Please input number of columns:")
        num_columns = int(input())
        generate_columns(num_columns)
        running = True

        while running:
            tick_manager()
            #x = random.randint(1,2)
            #if x == 1:
            generate_task()
            for i in range(num_columns):
                if i != 0 and i < num_columns - 1:
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
                update_config()
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

    #Worker assignment test
    if test==7:
        num_columns = 4
        z= 0
        generate_columns(num_columns)

        for i in range(num_columns):
            if i != 0 and i != num_columns - 1:
                board_1.columns[i].workers = 2  # Set 2 workers for middle columns
                print(f"Initial workers for Column {i}: {board_1.columns[i].workers}")
        while running:
            tick_manager()
            generate_task()
            for i in range(num_columns):
                if i != 0 and i < num_columns - 1:
                    if z == 10:
                            for j in range(num_columns):
                                if j != 0 and j != num_columns - 1:
                                    update_config()    # Randomize workers every 10 ticks
                                    print(f"Updated workers for Column {j}: {board_1.columns[j].workers}")
                            z = 0
                process_tasks(i)

            for i in range(num_columns):
                tasks_display = [f"{task.name} (status: {task.status})" for task in board_1.columns[i].tasks]
                task_workers = [f"{task.name} (worker assigned: {task.worker_task})" for task in board_1.columns[i].tasks]
                print(f"\nColumn {i}: {tasks_display}\n")
                print(f"Column {i} workers ({board_1.columns[i].workers}): {task_workers}\n")
            done_tasks()
            z=z+1
            time.sleep(tick_interval)

    #Metrics test
    if test == 8:
        num_columns = 6
        tick_interval = 0.5  # Faster ticks for testing
        generate_columns(num_columns)
        update_config()
        while running:
            tick_manager()
            generate_task()
            for i in range(num_columns):
                process_tasks(i)
                metrics_management(i)
                task_display = [f"{task.name} (status: {task.status}, cycle time: {task.cycle_time})" for task in board_1.columns[i].tasks]
                print(f"\nColumn {i}: {task_display}\n")
            print(f"Average Cycle Time: {board_1.average_cycle_time}")
            print(f"Completed Tasks Count: {board_1.completed_tasks_count}")
            print(f"Total WIP: {board_1.total_wip}")
            done_tasks()
            time.sleep(tick_interval)
    
    #Tick Speed Change Test
    if test == 9:
        num_columns = 6
        tick_interval = 1  # Start with 1 second per tick
        generate_columns(num_columns)
        while running:
            tick_manager()
            generate_task()
            for i in range(num_columns):
                process_tasks(i)
                task_display = [f"{task.name} (status: {task.status})" for task in board_1.columns[i].tasks]
                print(f"\nColumn {i}: {task_display}\n")
            if tick == 10:
                tick_interval = 0.5  # Speed up ticks after 10 ticks
                print("\nTick interval changed to 0.5 seconds.\n")
            if tick >= 20:
                tick_interval = 0.1  # Speed up ticks after 20 ticks
                print("\nTick interval changed to 0.1 seconds.\n")
            if tick >= 50:
                tick_interval = 1  # Reset tick interval after 50 ticks
                print("\nTick interval reset to 1 second.\n")
                tick = 0  # Reset tick count
            done_tasks()
            time.sleep(tick_interval)
        
        if test == 10:
            num_columns = 6
            tick_interval = 1  # Start with 1 second per tick
            running = True
            generate_columns(num_columns)
            while running:
                tick_manager()
                generate_task()
                for i in range(num_columns):
                    process_tasks(i)
                    task_display = [f"{task.name} (status: {task.status}) column history: {task.column_entry_tick}" for task in board_1.columns[i].tasks]
                    print(f"\nColumn {i}: {task_display}\n")
                done_tasks()
                time.sleep(tick_interval)




    #Test all
    if test == 11:
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
