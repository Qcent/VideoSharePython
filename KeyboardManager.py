import keyboard


class KeyboardManager:
    def __init__(self):
        self.key_states = {}

    def is_pressed_and_released(self, key):
        # Check the current pressed state of the key
        current_state = keyboard.is_pressed(key)

        # Get the previous state of the key from the dictionary
        previous_state = self.key_states.get(key, False)

        # Update the current state in the dictionary
        self.key_states[key] = current_state

        # Check if the key was previously pressed and is now released
        if previous_state and not current_state:
            return True

        return False
