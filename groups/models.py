"""Schema for Group"""


class Group:
    """Class for Group objects"""

    @staticmethod
    def structure():
        """Group structure"""
        group = {
            "id": "",
            "user_ids": [],
            "name": "",
            "description": "",
            "collaborators": [],
        }
        return group
