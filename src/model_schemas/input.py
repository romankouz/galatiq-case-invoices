from pydantic import BaseModel

class InputState(BaseModel):
    """
        The input of our system that ALWAYS starts with an invoice file to be processed.

        file_path: str, the path to the file to be processed.
    """
    file_path: str