import tkinter as tk       
from tkinter import ttk
import customtkinter as ctk
from pathlib import Path

import culidex

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")

class Application(ctk.CTk):
    def __init__(self):
        ctk.CTk.__init__(self)
        self.title("CuliDex")
        self.attributes("-fullscreen", True)
        self.resizable(True, True)
        self.bind_all("<Button-1>", lambda event: event.widget.focus_set())
        self.bind("<Escape>", lambda e: self.attributes("-fullscreen", False))
        self.create_widgets()

    def create_widgets(self):
        self.build_menu()
        self.build_search_page()

    def build_menu(self):
        menubar = ctk.CTkFrame(self, fg_color="#3A9E6F", height=40, corner_radius=0)
        menubar.pack(fill=tk.X, side=tk.TOP)
        menubar.pack_propagate(False)

        settings_button = tk.Menubutton(menubar, text="Settings", bg="#3A9E6F", fg="white", font=("Arial", 12, "bold"), relief="flat",
                              activebackground="#2E7D57", activeforeground="white")
        settings_button.pack(side=tk.LEFT, padx=10, pady = 6)
        settings_menu = tk.Menu(settings_button, tearoff=0)
        settings_menu.add_command(label="Region:", state="disabled")
        settings_menu.add_command(label="United States", command=lambda: self.set_region("United States"))
        settings_menu.add_command(label="Japan", command=lambda: self.set_region("Japan"))
        settings_menu.add_separator()
        settings_button.config(menu=settings_menu)

        ctk.CTkButton(menubar, text="✕", command=self.destroy, font=("Arial", 12, "bold"), fg_color="#3A9E6F",
               hover_color="#2E7D57", width=36, height=28, corner_radius=4).pack(side=tk.RIGHT, padx=4, pady = 6)
        ctk.CTkButton(menubar, text="⛶", command=lambda: self.attributes("-fullscreen", not self.attributes("-fullscreen")), 
                fg_color="#3A9E6F", hover_color="#2E7D57", width=36, height=28, corner_radius=4).pack(side="right", pady=6)
    
    def set_region(self, region):
        print(f"Region set to: {region}")
        self.region = region
        self.region_label.configure(text=f"Current Region: {self.region}")

    def build_search_page(self):
        ctk.CTkLabel(self, text="CuliDex", font=("Arial", 38, "bold"), text_color="#3E81BC").pack(pady=20)
        self.configure(fg_color="#fdfbee")
        logo_path = Path(__file__).parent / "assets" / "logo.png"
        logo_img = tk.PhotoImage(file=str(logo_path))
        logo_label = tk.Label(self, image=logo_img, bg="#fdfbee")
        logo_label.image = logo_img
        logo_label.pack(pady=(8, 16))
        self.region = tk.StringVar(value="United States")
        self.region_label = ctk.CTkLabel(self, text=f"Current Region: {self.region.get()}", font=("Arial", 20), text_color="#3E81BC")
        self.region_label.pack(pady=10)

        search_frame = ctk.CTkFrame(self, fg_color="#fdfbee", corner_radius=0)
        search_frame.pack(pady=20)
        self.search_entry = ctk.CTkEntry(search_frame, width=300, font=("Arial", 12), placeholder_text="Enter an ingredient...")
        self.search_entry.pack(side=tk.LEFT, padx=10)
        self.search_entry.bind("<Return>", self._search)
        ctk.CTkButton(search_frame, text="Search", width=100, command=self._search, font=("Arial", 12, "bold"), fg_color="#3A9E6F", text_color="white").pack(side=tk.LEFT)
    def _search(self):
        #ingredient = self.search_entry.get().strip()
        result = culidex.test_search()
        print(result)
        # if not ingredient:
        #     return

app = Application()
app.mainloop()