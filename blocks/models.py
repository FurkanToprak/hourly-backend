"""Schema for Blocks"""


class Block:
    """Class for Block objects"""

    @staticmethod
    def structure():
        """block structure"""
        block = {
            "id": "",
            "user_ids": [],
            "task_id": "",
            "type": "",
            "name": "",
            "start_time": "",
            "end_time": "",
        }
        return block
