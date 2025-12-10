import time
import threading
import random

running = True
#backlog = column[0]
#done = column[num_columns - 1]


def generate_columns(n):
        global column
        column = [[] for _ in range(n)]
        print(f"Generated {n} columns.")
        return column

def generate_task():
    global column
    i=0
    while running:
        if len(column[0]) <= max_tasks:
            i += 1
            column[0].append(f"Task {i}")
            #print(column[0])
        #print(f"Backlog: {column[0]}")
        time.sleep(random.randint(1,5))


def process_tasks(col):
    while running:
        if len(column[col - 1]) > 0 and col < num_columns:
            task = column[col - 1].pop(0)
            column[col].append(task)
            time.sleep(random.randint(2,10))
            while len(column[col+1]) >= max_tasks:
                time.sleep(0.1)
            column[ col ].remove(task)
            column[col+1].append(task)
            print(f"Column {col}: {column[col]}")
            print(f"Column {col+1}: {column[col+1]}")

        else:
            time.sleep(0.1)

def done_tasks():
    while running:
        if len(column[num_columns - 2]) > 0:
            if len(column[num_columns - 1]) >= max_tasks:
                column[num_columns - 1].pop(0)
            task = column[num_columns - 2].pop(0)
            column[num_columns - 1].append(task)
            print(f"Done: {column[num_columns - 1]}")
        else:
            time.sleep(0.1)
        

def main():
    global running
    global num_columns
    global col
    global worker_count
    global max_tasks
    num_columns = int(input("Enter number of columns: "))
    while num_columns >= 11:
        print(f"Maximum columns is 10")
        num_columns = int(input("Enter number of columns: "))
        
    worker_count = int(input("Enter number of workers per processing column: "))

    max_tasks = int(input("Enter maximum tasks per column: "))

    columns = generate_columns(num_columns)
    print(columns)
    generator_thread = threading.Thread(target=generate_task)
    for col in range(num_columns):
        if col%2!=0 and col < num_columns - 1:
            print(col)
            for i in range(worker_count):
                t = threading.Thread(target=process_tasks, args=(col,), name=f"Processor_{col}", daemon=True)
                t.start()
                print(f"Started worker {i+1} for column {col}")

    done_tasks_thread = threading.Thread(target=done_tasks, name="Done_Processor", daemon=True)
    done_tasks_thread.start()

    generator_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        running = False
        generator_thread.join()
        for i in range(num_columns - 1):
            t.join()
        done_tasks_thread.join()

if __name__ == "__main__":
    main()


#Usage:
# 1. User defines number of columns (max 10) , number of workers per processing column and maximum tasks per column.
# 2. 