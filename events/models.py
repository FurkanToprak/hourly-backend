"""Schema for Event"""


class Event:
    """Class for Event objects"""

    @staticmethod
    def structure():
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
