class Column:
    def __init__(self, id, name, max_tasks, workers_column, processing_time, column_type="process"):
        self.id = id
        self.name = name
        self.tasks = []
        self.max_tasks = max_tasks
        self.workers = workers_column
        self.total_workers = workers_column
        self.processing_time = processing_time
        self.column_type = column_type

    def __repr__(self):
        return f"Column(id={self.id}, name='{self.name}', type='{self.column_type}', tasks={len(self.tasks)}/{self.max_tasks}, workers={self.workers}), processing_time={self.processing_time})"


class Task:
    def __init__(self, id, name, created_at, done_at=None, worker_task=None, status=None, processing_duration=None):
        self.id = id
        self.name = name
        self.created_at = created_at
        self.done_at = done_at
        self.worker_task = worker_task
        self.status = status
        self.processing_duration = processing_duration

    def __repr__(self):
        return f"Task(id={self.id}, name='{self.name}', created_at='{self.created_at}', done_at='{self.done_at}', worker_task='{self.worker_task}', status='{self.status}', processing_duration='{self.processing_duration}')"


class Board:
    def __init__(self, total_columns):
        self.columns = []
        self.total_columns = total_columns
