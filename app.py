from tkinter import *
from tkinter import filedialog, font, ttk

from app_utils import (
    export_data,
    parse_gene_text,
    parse_rsid_text,
    query_table,
    read_file,
    create_pretty_filename,
)


class EnteredData:
    def __init__(self):
        self.option_selected = "gene"
        self.query_data = None
        self.file_in = None
        self.query_results = None
        self.save_file = None


class App(Tk):
    label_options = {
        "gene": "Enter a gene(s) to search or select a file",
        "rsid": "Enter an rsID(s) to search or select a file",
        "allele": "Allele search is not yet supported",
    }
    entry_options = {
        "gene": "Ex:\nCYP2D6\nCYP2C9\nor\nCYP2D6,CYP2C9",
        "rsid": "Ex:\nrs1234\nrs5678\nor\nrs1234,rs5678",
        "allele": "Allele search is not yet supported",
    }
    default_search = "gene"

    def __init__(self):
        super().__init__()
        self.entered_data = EnteredData()

        style = ttk.Style()
        style.theme_use("alt")

        self.title("Pharmacoscan Query Tool")
        # Set window size
        # root.geometry("550x550")
        # Disable resizing of the window using maximize button
        # root.resizable(0, 0)

        #####radio button and entry labels######
        self.frame_label_radiobuttons = Frame(self)
        self.frame_label_radiobuttons.grid(row=0, column=0)

        ######radio buttons for query type######
        self.frame_radio_buttons = Frame(self)
        self.frame_radio_buttons.grid(row=1, column=0, padx=20)
        self.label_radiobuttons = Label(
            self.frame_radio_buttons, text="Select a type of query:"
        )
        self.label_radiobuttons.grid(row=0, column=0)

        self.option_selected = StringVar(None, "gene")
        button_labels = {"By Gene": "gene", "By rsID": "rsid", "By Allele": "allele"}
        for i, (text, value) in enumerate(button_labels.items(), 1):
            font_ = font.Font()
            if value == "allele":
                font_ = font.Font(overstrike=1)
            radiobutton = Radiobutton(
                self.frame_radio_buttons,
                text=text,
                variable=self.option_selected,
                value=value,
                command=self.query_option_selected,
                font=font_,
            )
            radiobutton.grid(row=i, column=0, sticky="w")

        ######Entry Label and Text Field######
        self.frame_labels_entry = Frame(self)
        self.frame_labels_entry.grid(row=0, column=1)
        self.label_entry = Label(
            self.frame_labels_entry, text=self.label_options[self.default_search]
        )
        self.label_entry.grid(row=0, column=0)

        self.frame_text_entry = Frame(self)
        self.frame_text_entry.grid(row=1, column=1)

        self.text_entry = Text(self.frame_text_entry, width=20, height=6)
        self.text_entry.insert(INSERT, self.entry_options[self.default_search])
        self.text_entry.grid(row=0, column=0)
        self.text_entry.bind("<Control-Key-a>", self.select_all)
        self.text_entry.bind("<Control-Key-A>", self.select_all)
        self.text_scroll_entry = ttk.Scrollbar(
            self.frame_text_entry, command=self.text_entry.yview
        )
        self.text_scroll_entry.grid(row=0, column=1, sticky="nsew")
        self.text_entry["yscrollcommand"] = self.text_scroll_entry.set

        self.frame_text_browse = Frame(self)
        self.frame_text_browse.grid(row=2, column=1)
        self.file_button_entry = Button(
            self.frame_text_browse,
            text="Browse Files",
            command=self.select_file_open,
        )
        self.file_button_entry.grid(row=0, column=0)
        self.label_entry_info = Label(self.frame_text_browse, text="")
        self.label_entry_info.grid(row=1, column=0)

        #####Submit label and  button#####
        self.frame_submit = Frame(self)
        self.frame_submit.grid(row=3, column=0, columnspan=2)
        self.label_error = Label(self.frame_submit, text="", fg="red")
        self.label_error.grid(row=0, column=0)

        self.button_submit = Button(
            self.frame_submit, text="Submit Query", command=self.submit
        )
        self.button_submit.grid(row=1, column=0)

        #####table label######
        self.frame_table_label = Frame(self)
        self.frame_table_label.grid(row=4, column=0, pady=(10, 2), columnspan=2)
        self.label_table = Label(self.frame_table_label, text="")
        self.label_table.grid(row=0, column=0)

        ####table#####
        self.frame_table = Frame(self)
        self.frame_table.grid(row=5, column=0, columnspan=2)

        self.data_table = ttk.Treeview(self.frame_table)
        self.data_table.grid(row=0, column=0)
        self.data_table.grid_remove()
        self.table_scroll = ttk.Scrollbar(
            self.frame_table, command=self.data_table.yview
        )
        self.table_scroll.grid(row=0, column=1, sticky="nsew")
        self.data_table["yscrollcommand"] = self.table_scroll.set
        self.table_scroll.grid_remove()

        # # #####export button#####
        self.file_button_export = Button(
            self.frame_table, text="Export Table", command=self.select_file_save
        )
        self.file_button_export.grid(row=2, column=0)
        self.file_button_export.grid_remove()
        self.label_export = Label(self.frame_table, text="")
        self.label_export.grid(row=3, column=0)

    @staticmethod
    def select_all(event):
        event.widget.tag_add(SEL, "1.0", END)
        event.widget.mark_set(INSERT, "1.0")
        event.widget.see(INSERT)
        return "break"

    def select_file_open(self):
        file_path = filedialog.askopenfilename(title="Select a File")
        if isinstance(file_path, tuple) or file_path == "":
            self.file_button_entry.configure(text="Browse Files")
            self.entered_data.file_in = None
            return
        text = create_pretty_filename(file_path)
        self.file_button_entry.configure(text=text)
        self.entered_data.file_in = file_path

    def select_file_save(self):
        file_path = filedialog.asksaveasfilename(title="Select a file name for export")
        if file_path is None or file_path == "":
            # asksaveasfile return `None` if dialog closed with "cancel".
            if self.entered_data.save_file is not None:
                text = create_pretty_filename(self.entered_data.save_file)
                self.file_button_export.configure(text=text)
            return
        text = create_pretty_filename(file_path, save=True)
        if text.endswith("xls"):
            text = text.replace("xls", "xlsx")
        self.entered_data.save_file = file_path
        error = export_data(
            self.entered_data.query_results, self.entered_data.save_file
        )
        if error == PermissionError:
            self.error_label_update("Unable to save output. Permission Denied")
        elif error == FileNotFoundError:
            self.error_label_update("Directory for output file does not exist")
        self.file_button_export.configure(text=text)
        self.label_export.configure(text="Data exported Succesfully")

    def reset_table(self):
        # Couldn't figure out any other way of doing this other than
        # destroying the entire table widget and recreating it
        self.data_table.destroy()
        self.data_table = ttk.Treeview(self.frame_table)
        self.data_table.grid(row=0, column=0)
        self.table_scroll.destroy()
        self.table_scroll = ttk.Scrollbar(
            self.frame_table, command=self.data_table.yview
        )
        self.table_scroll.grid(row=0, column=1, sticky="nsew")
        self.data_table["yscrollcommand"] = self.table_scroll.set

    def build_table(self, df):
        self.reset_table()
        self.label_table.configure(text="Query Results")
        self.data_table.grid()
        self.data_table.configure(columns=df.columns.tolist())
        self.table_scroll.grid()

        self.data_table.column("#0", width=0, stretch=NO)
        self.data_table.heading("#0", text="", anchor=CENTER)

        for column in df.columns:
            width = 100
            if column == "Ref" or column == "Alt":
                width = 40
            self.data_table.column(column, anchor=CENTER, width=width, stretch=NO)
            self.data_table.heading(column, text=column, anchor=CENTER)
        for iid, row_data in df.iterrows():
            values = row_data.values.tolist()
            self.data_table.insert(
                parent="", index="end", iid=iid, text="", values=values
            )

    def error_label_update(self, text):
        self.label_error.configure(text=text)

    def reset_data(self):
        self.error_label_update("")
        self.entered_data.query_data = None
        self.label_export.configure(text="")
        self.label_table.configure(text="")
        self.label_entry_info.configure(text="")

    def reset_entered_data(self):
        self.entered_data.file_in = None
        self.entered_data.query_data = None

    def submit(self):
        self.reset_data()
        text_entered = self.text_entry.get("1.0", END)
        if self.entered_data.option_selected == "gene":
            parsed_data = parse_gene_text(text_entered)
        elif self.entered_data.option_selected == "rsid":
            parsed_data = parse_rsid_text(text_entered)
        elif self.entered_data.option_selected == "allele":
            self.reset_entered_data()
            return
        if parsed_data is not None:
            self.entered_data.query_data = parsed_data

        if self.entered_data.query_data and self.entered_data.file_in:
            self.error_label_update("Can only accept one of text entry or file")
            return

        if self.entered_data.file_in:
            data_type = self.entered_data.option_selected
            parsed_data, error = read_file(
                self.entered_data.file_in, data_type=data_type
            )
            if error == PermissionError:
                self.error_label_update("Permission denied when accessing file")
                self.reset_entered_data()
                return
            elif error == FileNotFoundError:
                self.error_label_update("Unable to find file")
                self.reset_entered_data()
                return
            elif error == UnicodeDecodeError:
                self.error_label_update("Unable to handle binary files")
                self.reset_entered_data()
                return
            if parsed_data is not None:
                self.entered_data.query_data = parsed_data
        if self.entered_data.query_data is None:
            self.error_label_update("Must supply one of text entry or file")
            return
        text = f"Parsed out {len(self.entered_data.query_data)} {self.entered_data.option_selected}"
        self.label_entry_info.configure(text=text)

        query_results = query_table(self.entered_data.query_data)
        self.entered_data.query_results = query_results
        self.build_table(self.entered_data.query_results)
        self.file_button_export.grid()

    def query_option_selected(self):
        self.entered_data.option_selected = self.option_selected.get()
        text_label_option = self.label_options[self.entered_data.option_selected]
        self.label_entry.configure(text=text_label_option)

        self.text_entry.delete("1.0", END)
        text_entry_option = self.entry_options[self.entered_data.option_selected]
        self.text_entry.insert(INSERT, text_entry_option)

        self.file_button_entry.configure(text="Browse Files")


if __name__ == "__main__":
    app = App()
    app.mainloop()
