import curses
import subprocess
import os

normal_menu = [
    ("Build", [
        ("Build    - Build and deploy all", "./starter.sh build"), 
        ("Destroy  - Destroy all",          "./starter.sh destroy"),
        ("Log      - Show last build log",  "cat target/build.log")
    ]),
    ("Other", [
        ("Advanced", "Advanced"),
        ("Help", "./starter.sh help"), 
        ("Exit", "Exit")
    ])
]

advanced_menu = [
    ("Build", [
        ("Build      - Build and deploy all", "./starter.sh build"), 
        ("Destroy    - Destroy all",          "./starter.sh destroy"),
        ("Log        - Show last build log",  "cat target/build.log")
    ]),
    ("Resource Manager", [
        ("Distribute - Create Resource Manager Stack", "./starter.sh rm"),
        ("Build      - Create and Build using Resource Manager", "./starter.sh rm build")
    ]),      
    ("SSH", [
        ("Key        - SSH private key",      "cat target/ssh_key_starter"), 
        ("Bastion    - SSH Bastion",          "./starter.sh ssh bastion"), 
        ("Compute    - SSH Compute",          "./starter.sh ssh compute"),
        ("Database   - SSH Database Node",    "./starter.sh ssh db_node"),
    ]),
    ("Start/Stop", [
        ("Start      - Start all resources",  "./starter.sh start"), 
        ("Stop       - Stop all resources",   "./starter.sh stop")
    ]),                
    ("Terraform", [
        ("Plan       - Terraform Plan",       "./starter.sh terraform plan"), 
        ("Apply      - Terraform Apply",      "./starter.sh terraform apply"),
        ("Destroy    - Terraform Destroy",    "./starter.sh terraform destroy")
    ]),                
    ("Other", [
        ("Env        - Set Environment variables", "./starter.sh env"), 
        ("Help", "./starter.sh help"), 
        ("Exit", "Exit")
    ])
]

def resetMenu( a_menu ):
    global current_item
    global current_subitem 
    global menu     

    current_item = 0
    current_subitem = 0  # Start with the first command selected
    menu = a_menu
 
def main(stdscr):
    global current_item
    global current_subitem 
    global menu 

    try: 
        stdscr.clear()
        curses.curs_set(0)
        stdscr.keypad(True)
        curses.start_color()
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)

        resetMenu( normal_menu )

        while True:
            stdscr.clear()
            stdscr.addstr(0, 0, f"OCI Starter")
            stdscr.addstr(1, 0, f"-----------")
            y=2
            for i, (topic, commands) in enumerate(menu):
                stdscr.addstr(y, 0, topic)  # Topic headers are NOT selectable
                y += 1
                if commands:
                    for j, (command, command_path) in enumerate(commands):
                        if i == current_item and j == current_subitem:
                            stdscr.attron(curses.color_pair(1))
                            selected_command = command_path
                        stdscr.addstr(y, 2, command)
                        stdscr.attroff(curses.color_pair(1))
                        y += 1

            # Display the selected command at the bottom
            stdscr.addstr(y + 1, 0, f"Command: {selected_command or 'None'}")

            key = stdscr.getch()

            if key == curses.KEY_UP:
                if current_item == 0 and current_subitem == 0: #prevent going up from first command
                    continue
                if current_subitem > 0:
                    current_subitem -= 1
                else:
                    current_item -= 1
                    if menu[current_item][1]:
                        current_subitem = len(menu[current_item][1]) - 1
                    else: #if it is exit
                        current_subitem = 0
            elif key == curses.KEY_DOWN:
                if current_item == len(menu)-1 and current_subitem == 2: #prevent going down from exit
                    continue
                if menu[current_item][1] and current_subitem < len(menu[current_item][1]) - 1:
                    current_subitem += 1
                else:
                    current_item += 1
                    if menu[current_item][1]:
                        current_subitem = 0
                    else: #if it is exit
                        current_subitem = 0

            elif key in (curses.KEY_ENTER, 10):
                selected_item = menu[current_item]
                if selected_command == "Exit":
                    break
                elif selected_command == "Advanced":
                    resetMenu( advanced_menu )
                elif selected_item[1]:
                    command_path = selected_item[1][current_subitem][1]
                    curses.endwin()
                    try:
                        print(f"Command: {command_path}")
                        # Write the command to a file and execute via bash to avoid issue with the terminal prompt
                        with open(f"{os.environ['TARGET_DIR']}/command.txt", "w") as f:
                            f.write(command_path)
                        # subprocess.run(["bash", "-c", command_path], check=True)
                    except subprocess.CalledProcessError as e:
                        print(f"Error executing {command_path}: {e}")
                    except FileNotFoundError:
                        print(f"Error: {command_path} not found")
                    break

            elif key == 27: # ESC
                break
    except:
        print( "WARNING - screen too small", flush=True )
        print( "-> HELP", flush=True )
        with open(f"{os.environ['TARGET_DIR']}/command.txt", "w") as f:
            f.write("./starter.sh help")

if __name__ == "__main__":
    curses.wrapper(main)

