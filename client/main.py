import tkinter as tk       
from tkinter import ttk
from pathlib import Path

class Application(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.master.title("CuliDex")
        self.master.attributes("-fullscreen", True)
        self.master.resizable(True, True)
        self.create_widgets()

    def create_widgets(self):
        self.build_menu()
        self.build_search_page()

    def build_menu(self):
        menu = tk.Menu(self.master)
        settings_menu = tk.Menu(menu, tearoff=0)
        settings_menu.add_command(label="Region:", state="disabled")
        settings_menu.add_command(label="United States", command=lambda: self.set_region("United States"))
        settings_menu.add_command(label="Japan", command=lambda: self.set_region("Japan"))
        settings_menu.add_separator()
        menu.add_cascade(label="Settings", menu=settings_menu)
        self.master.config(menu=menu)
        exit_btn = tk.Button(self.master, text="✕", command=self.quit,
                         font=("Arial", 12), relief="flat",
                         bg="#fafbed", activebackground="#ffcccc")
        exit_btn.place(relx=1.0, rely=0.0, anchor="ne")
    def set_region(self, region):
        print(f"Region set to: {region}")
        self.region = region
        self.region_label.config(text=f"Current Region: {self.region}")

    def build_search_page(self):
        tk.Label(self.master, text="CuliDex", font=("Arial", 28, "bold")).pack(pady=20)
        logo_path = Path(__file__).parent / "assets" / "logo.png"
        logo_img = tk.PhotoImage(file=str(logo_path))
        logo_label = tk.Label(self.master, image=logo_img, bg="#fafbed")
        logo_label.image = logo_img
        logo_label.pack(pady=(8, 16))
        self.region = tk.StringVar(value="United States")
        self.region_label = tk.Label(self.master, text=f"Current Region: {self.region.get()}", font=("Arial", 12))
        self.region_label.pack(pady=10)

        search_frame = tk.Frame(self.master)
        search_frame.pack(pady=20)
        self.search_entry = tk.Entry(search_frame, width=40, font=("Arial", 12))
        self.search_entry.pack(side=tk.LEFT, padx=10)
        self.search_entry.bind("<Return>", self._search)
        tk.Button(search_frame, text="Search", command=self._search, font=("Arial", 12)).pack(side=tk.LEFT)
    def _search(self):
        ingredient = self.search_entry.get().strip()
        if not ingredient:
            return

app = Application()
app.mainloop()