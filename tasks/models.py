"""Schema for Items"""


class Task:
    """Class for Item objects"""

    def structure(self):
        """task structure"""
        Task = {
            "id": "",
            "user_id": "",
            "name": "",
            "completed_time": "",
            "estimated_time": "",
            "start_date": "",
            "description": "",
            "due_date": "",
            "completed": "",
            "label": "",
        }
        return Task
