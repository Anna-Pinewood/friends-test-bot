"""
FSM states for the test creation and taking process.
"""
from aiogram.fsm.state import State, StatesGroup


class TestStates(StatesGroup):
    """States for test creation and completion."""
    creating_test = State()  # User is creating a test
    taking_test = State()    # User is taking someone else's test
