"""
Exit gdb on error
"""
import gdb

def exit_handler(event):
    if event.exit_code in [0, 1]:
        gdb.execute("quit")

gdb.events.exited.connect(exit_handler)
