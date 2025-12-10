import unittest
import threading
import time
import Backend.Kanban as K
from Backend.Kanban import *



class TestColumnGeneration(unittest.TestCase):
    """Test cases for generate_columns function."""

    def test_generate_columns(self):
        """Test column generation."""
        result = generate_columns(5)
        self.assertEqual(len(result),5)
        self.assertTrue(all(isinstance(col,list) for col in result))
        self.assertTrue(all(len(col)==0 for col in result))

class TestTaskGeneration(unittest.TestCase):
    """Test cases for generate_task function."""

    def test_task_generation(self):
        """Test task generation."""
        global running
        running = True
        K.generate_columns(3)
        initial_backlog_length = len(K.column[0])
        task_thread = threading.Thread(target = K.generate_task) #has to call the generate task from kanban
        task_thread.daemon = True
        task_thread.start()
        time.sleep(4)
        running = False
        self.assertGreater(len(K.column[0]),initial_backlog_length)

class TestTaskProcessing(unittest.TestCase):
    """Test cases for process_tasks function."""

    def test_task_processing(self):
        """Test task processing."""
        global running, num_columns
        K.generate_columns(4)
        num_columns = 4
        running = True
        K.column[0].append("Test Task")
        processor_thread = threading.Thread(target=K.process_tasks,args=(1,))
        processor_thread.daemon = True
        processor_thread.start()
        time.sleep(2)
        runnig = False

class TestDoneTasks(unittest.TestCase):
    """Test cases for done_tasks function."""

    def test_done_tasks(self):
        """Test marking tasks as done."""
        pass


if __name__ == "__main__":
    unittest.main()
