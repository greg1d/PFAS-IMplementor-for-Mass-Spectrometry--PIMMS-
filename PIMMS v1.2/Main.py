import sys
from PIMMS_GUI_Application import PimmsGUI, TextRedirector


# ============================================================================================
# MAIN APPLICATION ENTRY POINT
# ============================================================================================
def main():
    """
    Initializes and runs the PIMMS GUI application.
    """
    app = PimmsGUI()

    # It's good practice to redirect stdout here as well, in case of early errors
    # The GUI's own redirector will take over once the window is created.
    sys.stdout = (
        TextRedirector(app.log_text, "stdout")
        if hasattr(app, "log_text")
        else sys.stdout
    )

    app.mainloop()


if __name__ == "__main__":
    main()
