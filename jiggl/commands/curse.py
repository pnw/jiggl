from cliff.command import Command
import curses


def print_commands(screen):
    top_pos = 0
    # for top_pos in range(5):

    screen.addstr(0, 0, "Commands:")
    screen.addstr(1, 0, "p: Print out some stuff")
    screen.addstr(2, 0, "P: Print out some upper case stuff")
    screen.addstr(3, 0, "3: I am a three")
    screen.addstr(4, 0, "<space>: The space bar: Where astronauts can grab a beer.")
    screen.addstr(5, 0, "q: quit")


class Curse(Command):
    def take_action(self, parsed_args):
        print 'Curse you!'
        try:
            screen = curses.initscr()
            # screen.addstr("This is a String")
            curses.noecho()
            curses.curs_set(0)
            screen.keypad(1)

            top_pos = 0
            left_pos = 0
            # screen.addstr(top_pos, left_pos, "Positioned String")
            print_commands(screen)
            while True:
                event = screen.getch()
                if event == ord("q"): break
                elif event == ord("p"):
                  screen.clear()
                  # print_commands(screen)
                  screen.addstr(top_pos, left_pos, "The User Pressed Lower Case p")

                elif event == ord("P"):
                  screen.clear()
                  # print_commands(screen)
                  screen.addstr(top_pos, left_pos, "The User Pressed Upper Case P")

                elif event == ord("3"):
                  screen.clear()
                  # print_commands(screen)
                  screen.addstr(top_pos, left_pos, "The User Pressed 3")

                elif event == ord(" "):
                    screen.clear()
                    # print_commands(screen)
                    screen.addstr(top_pos, left_pos, "The User Pressed The Space Bar")
                elif event == ord("h"):
                    screen.clear()
                    print_commands(screen)


        finally:
            curses.endwin()