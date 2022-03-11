"""Schema for Items"""


class Item:
    """Class for Item objects"""

    def structure(self):
        """item structure"""
        Item = {
            "id": "",
            "user_id": "",
            "name": "",
            "work_hours": "",
            "start_date": "",
            "due_date": "",
            "completed": "",
        }
        return Item
