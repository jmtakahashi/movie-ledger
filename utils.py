"""Debug utilities for our Flask app"""


class DebugUtilities:

    def print_var(var, message=None):
        """Print out debug lines with spacing and variable."""

        print("")
        print("***********************")
        if message:
            print(message)
        print(var)
        print("***********************")
        print("")
