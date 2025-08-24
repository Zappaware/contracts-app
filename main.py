from nicegui import ui

from components.header import header
from components.home_page import home_page


def main():
    header()
    home_page()
    ui.run(port=5000)


if __name__ in {"__main__", "__mp_main__"}:
    main()
