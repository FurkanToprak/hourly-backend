"""Schema for Blocks"""


class Block:
    """Class for Item objects"""

    def structure(self):
        """item structure"""
        block = {
            "id": "",
            "user_ids": [],
            "task_id": "",
            "type": "",
            "name": "",
            "start_time": "",
            "end_time": "",
            "date": "",
            "completed": "",
            "repeat": "",
        }
        return block
