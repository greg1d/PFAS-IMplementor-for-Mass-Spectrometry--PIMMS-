import sys

from GUI.app import PimmsGUI
from GUI.text_redirector import TextRedirector

if __name__ == "__main__":
    app = PimmsGUI()

    # Redirect stdout to the Text widget in the run_tab
    # This assumes RunTab has an attribute 'log_text' which is the tk.Text widget
    sys.stdout = TextRedirector(app.run_tab.log_text, "stdout")

    app.mainloop()
