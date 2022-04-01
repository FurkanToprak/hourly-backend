"""Schema for Items"""


class Task:
    """Class for Item objects"""

    @staticmethod
    def structure():
        """task structure"""
        task = {
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
            "do_not_schedule": "",
        }
        return task
