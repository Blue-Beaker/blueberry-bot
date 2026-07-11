
import argparse


class ArgumentError(Exception):
    pass

class ShowHelp(Exception):
    message:str
    def __init__(self, message:str, *args: object) -> None:
        super().__init__(*args)
        self.message=message
        
    def __str__(self) -> str:
        return self.message

class ArgParser(argparse.ArgumentParser):
    def __init__(self, command_name=None, add_help=True, *args, **kwargs):
        super().__init__(exit_on_error=False, add_help=add_help, *args, **kwargs)
        self.messages = []
        self.command_name = command_name or self.prog
    def _print_message(self, message, file=None):
        self.messages.append(message)
    def print_help(self, file=None):
        """将帮助信息输出到 self.messages 中，使用指令名替代文件名"""
        if self.command_name:
            # 暂存原始 prog，替换为指令名
            orig_prog = self.prog
            self.prog = self.command_name
        super().print_help(file=None)
        if self.command_name:
            self.prog = orig_prog
        raise ShowHelp("\n".join(self.messages))
    def format_help(self):
        """返回格式化的帮助字符串，使用指令名替代文件名"""
        if self.command_name:
            orig_prog = self.prog
            self.prog = self.command_name
        result = super().format_help()
        if self.command_name:
            self.prog = orig_prog
        return result
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