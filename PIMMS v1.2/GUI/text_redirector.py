# pimms_project/gui/text_redirector.py
class TextRedirector(object):
    """A class to redirect stdout or stderr to a tkinter Text widget."""

    def __init__(self, widget, tag="stdout"):
        self.widget = widget
        self.tag = tag

    def write(self, str_val):
        self.widget.configure(state="normal")
        self.widget.insert("end", str_val, (self.tag,))
        self.widget.configure(state="disabled")
        self.widget.see("end")

    def flush(self):
        # This is needed for compatibility with the file-like object interface.
        pass
