"""Schema for the Users"""


class User:
    """Creating a user object"""

    @staticmethod
    def structure():
        """Creating a user object"""
        user = {
            "name": "",
            "email": "",
            "id": "",
            "startOfDay": "",
            "endOfDay": "",
            "refresh_schedule": "",
        }
        return user
