# coding: utf-8

import os 
from os import system, name

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# def colors
# - - - - - - - - - - - - - - - - - - - - - - - - - -

class Color:
    ESCAPE_SEQ_START = '\033[{}m'
    ESCAPE_SEQ_END = '\033[0m'

    def __init__(self, code):
        self.code = code

    def __call__(self, text):
        try:
            return f'{self.ESCAPE_SEQ_START.format(self.code)}{text}{self.ESCAPE_SEQ_END}'
        except Exception:
            return text

# Color instances
default_c = Color(0)
white = Color(97)
cyan = Color(96)
magenta = Color(95)
blue = Color(94)
yellow = Color(93)
green = Color(92)
red = Color(91)
black = Color(90)
white_b = Color(47)
cyan_b = Color(46)
magenta_b = Color(45)
blue_b = Color(44)
yellow_b = Color(43)
green_b = Color(42)
red_b = Color(41)
black_b = Color(40)

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# clear shell screen
# - - - - - - - - - - - - - - - - - - - - - - - - - -

def clear():
    try:
        if name == 'nt':  # Windows
            system('cls')
        else:  # Mac and Linux
            system('clear')
    except Exception:
        pass

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# expand local path
# - - - - - - - - - - - - - - - - - - - - - - - - - -

def path_expander(path):

    try:
        expanded_path = os.path.expanduser(path)
        return expanded_path
    
    except (ValueError, TypeError, OSError) as e:
        raise SystemExit(1, print_error("check_folder error:", e))

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# print script info
# - - - - - - - - - - - - - - - - - - - - - - - - - -

def print_info(color, v1, v2, v3):
    align = '<35' if isinstance(v3, int) else '35'
    print(color(f"{'*'*5:10} {v1:20} {v2:20} {v3:{align}} {'*'*5:5}"))

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# print script error
# - - - - - - - - - - - - - - - - - - - - - - - - - -

def print_error(*args, color=red, level='ERROR'):

    color = yellow if level == 'INFO' else color 
    max_length = min(max(len(str(error_message)) for error_message in args) + 6, 98)
    error_box_width = max_length + 4
    error_message_width = max_length + 2
    blank_line = color("║" + " " * error_box_width + "║")

    print(color("\n╔" + "=" * error_box_width + "╗"))
    print(blank_line)
    print(color("║"), color(f"{level}!".center(error_message_width)), color("║"))
    print(blank_line)

    for error_message in args:
        error_message = str(error_message)
        if len(error_message) > 98:
            split_messages = [error_message[i:i + 98] for i in range(0, len(error_message), 98)]
            for split_message in split_messages:
                print(color("║"), color(split_message.center(error_message_width)), color("║"))
        else:
            print(color("║"), color(error_message.center(error_message_width)), color("║"))

    print(blank_line)
    print(blank_line)
    print(color("╚" + "=" * error_box_width + "╝\n"))

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# print formated output 
# - - - - - - - - - - - - - - - - - - - - - - - - - -

def print_output(data):

    color = data.get('color')
    region = data.get('region')
    region_ad = data.get('region_ad')
    compartment = data.get('compartment')
    service = data.get('service')
    obj_name = data.get('obj_name')
    
    formatted_string = color(
        f'{region:20}'
        f'{region_ad[-4:]:6}'
        f'{compartment[0:18]:20}'
        f'{service:20}'
        f'{obj_name[0:18]:20}'
    )
    print(formatted_string)

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# calculate time delta
# - - - - - - - - - - - - - - - - - - - - - - - - - -
    
def strfdelta(td):
    days = td.days
    hours, rem = divmod(td.seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    return f"{days} days, {hours} hours, {minutes} minutes, {seconds} seconds"