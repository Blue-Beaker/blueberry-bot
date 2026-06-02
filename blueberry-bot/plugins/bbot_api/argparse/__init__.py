
import argparse


class ArgumentError(Exception):
    pass

class ArgParser(argparse.ArgumentParser):
    def __init__(self,*args,**kwargs):
        super().__init__(exit_on_error=False,add_help=False,*args,**kwargs)
        self.messages=[]
    def _print_message(self, message, file=None):
        self.messages.append(message)
    def error(self, message):
        """error(message: string)

        Prints a usage message incorporating the message to stderr and
        exits.

        If you override this in a subclass, it should not return -- it
        should either exit or raise an exception.
        """
        raise ArgumentError(message)
    def exit(self, status=0, message=None):
        raise ArgumentError(message)