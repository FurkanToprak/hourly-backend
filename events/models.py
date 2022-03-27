"""Schema for Blocks"""


class Event:
    """Class for Block objects"""

    def structure(self):
        """Event structure"""
        event = {
            "id": "",
            "user_id": "",
            "name": "",
            "start_time": "",
            "end_time": "",
            "repeat": "",
        }
        return event
