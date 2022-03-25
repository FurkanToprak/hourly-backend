"""Schema for Blocks"""


class Block:
    """Class for Block objects"""

    def structure(self):
        """block structure"""
        block = {
            "id": "",
            "user_ids": [],
            "task_id": "",
            "type": "",
            "name": "",
            "start_time": "",
            "end_time": "",
            "completed": "",
        }
        return block
