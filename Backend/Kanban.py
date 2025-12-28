import time
import threading
import random
import datetime



running = False
#backlog = column[0]
#done = column[num_columns - 1]
lock = threading.Lock() #lock for thread safety

######################################################################################################################################################################################################################################

class Column:
    def __init__(self, id, name, max_tasks, workers_column, processing_time):
        self.id = id
        self.name = name
        self.tasks = []
        self.max_tasks = max_tasks
        self.workers = workers_column
        self.processing_time = processing_time
    
    def __repr__(self):
        return f"Column(id={self.id}, name='{self.name}', tasks={len(self.tasks)}/{self.max_tasks}, workers={self.workers}), processing_time={self.processing_time})"

class Task:
    def __init__(self, id, name, created_at, done_at=None, worker_task=None, status=None):
        self.id = id
        self.name = name
        self.created_at = created_at
        self.done_at = done_at
        self.worker_task = worker_task
        self.status = status
    
    def __repr__(self):
        return f"Task(id={self.id}, name='{self.name}', created_at='{self.created_at}', done_at='{self.done_at}', worker_task='{self.worker_task}', status='{self.status}')"

class Board:
    def __init__(self, total_columns):
        self.columns = []
        self.total_columns = total_columns

########################################################################################################################################################################################################################################

def tick_manager():
    global tick
    global tick_interval
    global running
    global clock
    global day

    tick = tick + 1
    clock = clock + 0.10
    if clock%1 >= 0.60:
        clock = clock + 0.40

    if clock >= 17.00:
        clock = 9.00
        day = day + 1

    #print(f"Time: {round(clock, 3)}, Day: {day}, Tick: {tick}")

def generate_columns(n):
    global num_columns
    global board_1
    global tick_interval
    num_columns = n

    board_1 = Board(total_columns=n)
    
    for i in range(n):
        col = Column(
            id=i,
            name=f"Column {i}",
            max_tasks=5,
            workers_column=2,
            processing_time=random.randint(3,12)*tick_interval
        )
        #print(f"Generated column {i}")
        board_1.columns.append(col)

def generate_task():
    global id

    
    if len(board_1.columns[0].tasks) < board_1.columns[0].max_tasks:
        id = id+1
        task = Task(
            id=id,
            name=f"Task {id}",
            created_at=f"Day: {day}, Time: {round(clock, 3)}"
        )
        board_1.columns[0].tasks.append(task)
        #print(column[0])
        #print(f"Backlog: {board_1.columns[0].tasks}\n")

def process_tasks(col):
    if len(board_1.columns[col - 1].tasks) > 0 and len(board_1.columns[col].tasks) < board_1.columns[col].max_tasks:
        task = board_1.columns[col - 1].tasks.pop(0)
        board_1.columns[col].tasks.append(task)

    if len(board_1.columns[col].tasks) > 0:
        # Iterate backwards to safely remove items during iteration
        for i in range(len(board_1.columns[col].tasks) - 1, -1, -1):
            task = board_1.columns[col].tasks[i]
            if task.status is None:
                task.status = board_1.columns[col].processing_time
            
            task.status = task.status - tick_interval
            #print(f"Processing Task {task.id} in Column {col}, Time left: {task.status}")
    
   
            if task.status <= 0 and i == 0:
                if col + 2 < num_columns and  len(board_1.columns[col + 1].tasks) < board_1.columns[col + 1].max_tasks:
                    board_1.columns[col].tasks.remove(task)
                    board_1.columns[col + 1].tasks.append(task)
                    task.status = None
                
                elif col + 2 >= num_columns:
                    board_1.columns[col].tasks.remove(task)
                    board_1.columns[col + 1].tasks.append(task)
                    task.status = None


    
    #print(f"Column {col}: {len(board_1.columns[col].tasks)}")
    #if col + 1 < num_columns:
        #print(f"Column {col + 1}: {len(board_1.columns[col + 1].tasks)}")

            

def done_tasks():
    if num_columns%2 != 0:
        if len(board_1.columns[num_columns - 1].tasks) >= board_1.columns[num_columns - 1].max_tasks:
             
            task = board_1.columns[num_columns - 1].tasks.pop(0)
            task.done_at = f"Day: {day}, Time: {round(clock, 3)}"
            #print(f"Done: {board_1.columns[num_columns - 1].tasks}")


    


        

def main():
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

    num_columns = 3

    generate_columns(num_columns)

    while running:
        tick_manager()
        generate_task()
        for i in range(num_columns):
            if i%2 != 0 and i < num_columns - 1:
                process_tasks(i)
        #for i in range(num_columns):
            #task_display = [f"{task.name} (status: {task.status})" for task in board_1.columns[i].tasks]
            #print(f"\nColumn {i}: {task_display}\n")
        done_tasks()
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
                print(f"\nColumn {i}: {tasks_display}\n")
            done_tasks()
            time.sleep(tick_interval)

 

    
    
    



if __name__ == "__main__":
    #main()
    test_board()
