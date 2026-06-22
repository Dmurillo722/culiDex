import tkinter as tk       
from tkinter import ttk
import customtkinter as ctk
from pathlib import Path
import similarity
import sys

import culidex
import db


ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")

class Application(ctk.CTk):
    def __init__(self):
        ctk.CTk.__init__(self)
        self.title("CuliDex")
        self.attributes("-fullscreen", True)
        self.resizable(True, True)
        self.region_var = "United States"
        self.bind_all("<Button-1>", lambda event: event.widget.focus_set())
        self.bind("<Escape>", lambda e: self.attributes("-fullscreen", False))
        self.create_widgets()
        #fetch once and reuse for both matrix and food names
        _df = db.fetch_all()
        #build numpy matrix on initialization for faster querying and rust bindings
        self.matrix = similarity._build_matrix(_df, similarity.WEIGHTS)
        #initialize food names numpy array for index accessing
        self.food_names = similarity._build_food_names(_df)

    def create_widgets(self):
        self.build_menu()
        self.build_search_page()
        self.display_results_page()
        self.show_page(self.search_page)
        
    def _bind_scroll_recursive(self, widget, canvas):
        widget.bind("<MouseWheel>", lambda e: self._on_mousewheel(e, canvas))
        widget.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        widget.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))
        for child in widget.winfo_children():
            self._bind_scroll_recursive(child, canvas)

    def _on_mousewheel(self, event, canvas):
        if sys.platform.startswith("win"):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        elif sys.platform == "darwin":
            canvas.yview_scroll(int(-1 * event.delta), "units")

    def show_page(self, page):
        page.tkraise()

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
        self.region_var = region
        self.region_label.configure(text=f"Current Region: {self.region_var}")

    def build_search_page(self):
        self.search_page = ctk.CTkFrame(self, fg_color="#fdfbee", corner_radius=0)
        self.search_page.place(x=0, y= 40, relwidth=1, relheight=1)
        self.configure(fg_color="#fdfbee")
        
        ctk.CTkLabel(self.search_page, text="CuliDex", font=("Arial", 38, "bold"), text_color="#3E81BC").pack(pady=(80, 0))
        
        logo_path = Path(__file__).parent / "assets" / "logo.png"
        logo_img = tk.PhotoImage(file=str(logo_path))
        logo_label = tk.Label(self.search_page, image=logo_img, bg="#fdfbee")
        logo_label.image = logo_img
        logo_label.pack(pady=(8, 16))
        
        self.region_label = ctk.CTkLabel(self.search_page, text=f"Current Region: {self.region_var}", font=("Arial", 20), text_color="#3E81BC")
        self.region_label.pack()

        search_frame = ctk.CTkFrame(self.search_page, fg_color="#fdfbee", corner_radius=0)
        search_frame.pack(pady=20)
        self.search_entry = ctk.CTkEntry(search_frame, width=300, height=30, font=("Arial", 14), placeholder_text="Enter an ingredient...")
        self.search_entry.pack(side=tk.LEFT, padx=10)
        self.search_entry.bind("<Return>", lambda e: self._search())
        self.search_entry.bind("<Key>", lambda e: self.search_error_label.configure(text=""))
        ctk.CTkButton(search_frame, text="Search", width=100, height=30, command=self._search, font=("Arial", 12, "bold"), 
                      fg_color="#3A9E6F", text_color="white").pack(side=tk.LEFT)
        self.search_error_label = ctk.CTkLabel(self.search_page, text="", font=("Arial", 12), text_color="red")
        self.search_error_label.pack()
    def display_results_page(self):
        self.results_page = ctk.CTkFrame(self, fg_color="#fdfbee", corner_radius=0)
        self.results_page.place(x=0, y=40,relwidth=1, relheight=1)
        top_row = ctk.CTkFrame(self.results_page, fg_color="#fdfbee")
        top_row.pack(fill="x", padx=40, pady=20)

        ctk.CTkButton(top_row, text="← Back",
                       command=lambda: self.show_page(self.search_page),
                       fg_color="#3A9E6F", hover_color="#2E7D57", width=80).pack(side="left", padx=(0, 20))

        self.results_title = ctk.CTkLabel(top_row, text="",
                                           font=("Arial", 18, "bold"), text_color="#3E81BC")
        self.results_title.pack(side="left")
        split_frame = ctk.CTkFrame(self.results_page, fg_color="#fdfbee")
        split_frame.pack(fill="both", expand=True, padx=40, pady=(0, 20))
        #left panel for searched ingredient
        self.left_panel = ctk.CTkFrame(split_frame, fg_color="#f0f0e8", corner_radius=8, width=260)
        self.left_panel.pack(side="left", fill="y", padx=(0, 20))
        self.left_panel.pack_propagate(False)
        #right panel for substitutes
        self.right_panel = ctk.CTkScrollableFrame(split_frame, fg_color="#fdfbee")
        self.right_panel.pack(side="right", fill="both", expand=True)

    def show_results(self, name):
        #clear previous results
        for widget in self.left_panel.winfo_children():
            widget.destroy()
        for widget in self.right_panel.winfo_children():
            widget.destroy()
        
        self.results_title.configure(text = f"Substitutes for: {name}", font=("Arial", 30, "bold"))
        #retrieve ingredient information from db
        match = db.search(name)
        if not match.empty:
            row = match.iloc[0]
            self.build_ingredient_card(self.left_panel, row, is_selected = True)
        
        
        #dummy substitute ingredient information
        #dummy_results = [
        #    {"name": "Horseradish root", "score": 89},
        #    {"name": "Ginger root",      "score": 68},
        #    {"name": "Mustard seed",     "score": 49},
        #]

        results = similarity.get_substitutes(name, self.food_names, self.matrix, 30)

        for item in results:
            card = ctk.CTkFrame(self.right_panel, fg_color= "#fdfbee", corner_radius= 8)
            card.pack(fill = 'x', pady =6)
            self.build_substitute_card_numerical(card, item)

        self._bind_scroll_recursive(self.right_panel, self.right_panel._parent_canvas)
        self.show_page(self.results_page)


        #for item in results: #formerly dummy results
        #    card = ctk.CTkFrame(self.right_panel, fg_color= "#fdfbee", corner_radius= 8)
        #    card.pack(fill = "x", pady = 6)
        #    self.build_substitute_card(card, item)
        #self.show_page(self.results_page)

    def build_ingredient_card(self, parent, row, is_selected = False):
        key_nutrients = [
            ("Calories",  f"{row.get('energy_kcal', 'N/A')} kcal"),
            ("Protein",   f"{row.get('protein_g', 'N/A')} g"),
            ("Carbs",     f"{row.get('carb_g', 'N/A')} g"),
            ("Fat",       f"{row.get('fat_total_g', 'N/A')} g"),
            ("Fiber",     f"{row.get('fiber_g', 'N/A')} g"),
            ("Sodium",    f"{row.get('sodium_mg', 'N/A')} mg")
        ]
        extra_nutrients = [
            ("Sugars",    f"{row.get('sugars_total_g', 'NaN')} g"),
            ("Potassium", f"{row.get('potassium_mg', 'N/A')} mg"),
            ("Calcium",   f"{row.get('calcium_mg', 'N/A')} mg"),
            ("Iron",      f"{row.get('iron_mg', 'N/A')} mg"),
            ("Vitamin C", f"{row.get('vitamin_c_mg', 'N/A')} mg"),
            ("Zinc",      f"{row.get('zinc_mg', 'N/A')} mg")
        ]
        ctk.CTkLabel(parent, text=row["name"], font=("Arial", 24, "bold"), text_color="#3E81BC", wraplength=220).pack(padx = 16, pady=(16, 8))

        for label, value in key_nutrients:
            row_frame = ctk.CTkFrame(parent, fg_color="#f0f0e8", height=24)
            row_frame.pack(fill="x", padx=16, pady=0)
            ctk.CTkLabel(row_frame, text=label, font=("Arial", 22), text_color="#3E81BC", anchor="w").pack(side="left")
            ctk.CTkLabel(row_frame, text=value, font=("Arial", 18, "bold"), text_color="#3E81BC", anchor="e").pack(side="right")
        
        extra_frame = ctk.CTkFrame(parent, fg_color="#f0f0e8")
        def toggle_extra():
            if extra_frame.winfo_ismapped():
                extra_frame.pack_forget()
                more_btn.configure(text="+ More")
            else:
                extra_frame.pack(fill="x", padx=16, pady=(4, 0), before=more_btn)
                more_btn.configure(text="- Less")
        for label, value in extra_nutrients:
            row_frame = ctk.CTkFrame(extra_frame, fg_color="transparent", height=24)
            row_frame.pack(fill="x", pady=0)
            ctk.CTkLabel(row_frame, text=label, font=("Arial", 22), text_color="#3E81BC", anchor="w").pack(side="left", pady = 0)
            ctk.CTkLabel(row_frame, text=value, font=("Arial", 18, "bold"), text_color="#3E81BC", anchor="e").pack(side="right", pady = 0)

        more_btn = ctk.CTkButton(parent, text="+ More", command=toggle_extra, font=("Arial", 14), fg_color="transparent", text_color="#3A9E6F"
                                      , hover_color="#e8e8e0")
        more_btn.pack(padx = 16,pady=(4, 16))


    def build_substitute_card_numerical(self, parent, item):
        top = ctk.CTkFrame(parent, fg_color="transparent")
        top.pack(fill="x",padx=16, pady=(12, 4))

        ctk.CTkLabel(top, text=self.
                    food_names[item[0]], font=("Arial", 24, "bold"), text_color="#3E81BC",).pack(side="left")

        score = round(item[1]*100)
        score_color = "#3A9E6F" if score >= 75 else "#E8A020" if score >= 50 else "#CC4444"
        ctk.CTkLabel(top, text=f"{score}% match", font=("Arial", 20, "bold"), text_color=score_color).pack(side="right")
        #nothing for now

        food_data = db.search(self.food_names[item[0]])
        calories = food_data.iloc[0]["energy_kcal"]
        protein = food_data.iloc[0]["protein_g"]
        fat = food_data.iloc[0]["fat_total_g"]
        carbs = food_data.iloc[0]["carb_g"]
        sodium = food_data.iloc[0]["sodium_mg"]
        sugars = food_data.iloc[0]["sugars_total_g"]

        key_nutrients = [
            ("Calories", f"{calories} kcal"),
            ("Protein",  f"{protein} g"),
            ("Carbs",    f"{carbs} g"),
            ("Fat",      f"{fat} g"),
            ("Sodium",   f"{sodium} mg"),
            ("Total Sugars", f"{sugars} g")
        ]
        extra_frame = ctk.CTkFrame(parent, fg_color="transparent")

        nutrients_frame = ctk.CTkFrame(parent, fg_color="transparent")
        nutrients_frame.pack(fill="x", padx=16, pady=(0, 4))
        for label, value in key_nutrients:
            row_frame = ctk.CTkFrame(nutrients_frame, fg_color="transparent", height=24)
            row_frame.pack(fill="x", pady=0)
            ctk.CTkLabel(row_frame, text=label, font=("Arial", 20), text_color="#3E81BC", anchor="w").pack(side="left", pady=0)
            ctk.CTkLabel(row_frame, text=value, font=("Arial", 16, "bold"), text_color="#3E81BC", anchor="e").pack(side="right", pady=0)

        extra_nutrients = [
            ("Potassium", f"{food_data.iloc[0]['potassium_mg']} mg"),
            ("Calcium",   f"{food_data.iloc[0]['calcium_mg']} mg"),
            ("Iron",      f"{food_data.iloc[0]['iron_mg']} mg"),
            ("Vitamin C", f"{food_data.iloc[0]['vitamin_c_mg']} mg"),
            ("Sugars",    f"{food_data.iloc[0]['sugars_total_g']} g"),
        ]

        for label, value in extra_nutrients:
            row_frame = ctk.CTkFrame(extra_frame, fg_color="transparent", height=24)
            row_frame.pack(fill="x", pady=0)
            ctk.CTkLabel(row_frame, text=label, font=("Arial", 20), text_color="#3E81BC", anchor="w").pack(side="left")
            ctk.CTkLabel(row_frame, text=value, font=("Arial", 16, "bold"), text_color="#3E81BC", anchor="e").pack(side="right")

        def toggle_extra():
            if extra_frame.winfo_ismapped():
                extra_frame.pack_forget()
                more_btn.configure(text="+ More")
            else:
                extra_frame.pack(fill="x", padx=16, pady=(0, 4), before=more_btn)
                more_btn.configure(text="− Less")
        more_btn = ctk.CTkButton(parent, text="+ More", command=toggle_extra,
                          font=("Arial", 14), fg_color="transparent",
                          text_color="#3A9E6F", hover_color="#e8e8e0")
        more_btn.pack(padx=16, pady=(0, 12))


    def build_substitute_card(self, parent, item):
        top = ctk.CTkFrame(parent, fg_color="transparent")
        top.pack(fill="x",padx=16, pady=(12, 4))
        
        ctk.CTkLabel(top, text=item["name"], font=("Arial", 24, "bold"), text_color="#3E81BC",).pack(side="left")

        score_color = "#3A9E6F" if item["score"] >= 75 else "#E8A020" if item["score"] >= 50 else "#CC4444"
        ctk.CTkLabel(top, text=f"{item['score']}% match", font=("Arial", 20, "bold"), text_color=score_color).pack(side="right")
        #nothing for now
        key_nutrients = [
            ("Calories", "-- kcal"),#
            ("Protein",  "-- g"),
            ("Carbs",    "-- g"),
            ("Fat",      "-- g"),
        ]
        extra_frame = ctk.CTkFrame(parent, fg_color="transparent")

        nutrients_frame = ctk.CTkFrame(parent, fg_color="transparent")
        nutrients_frame.pack(fill="x", padx=16, pady=(0, 4))
        for label, value in key_nutrients:
            row_frame = ctk.CTkFrame(nutrients_frame, fg_color="transparent", height=24)
            row_frame.pack(fill="x", pady=0)
            ctk.CTkLabel(row_frame, text=label, font=("Arial", 20), text_color="#3E81BC", anchor="w").pack(side="left", pady=0)
            ctk.CTkLabel(row_frame, text=value, font=("Arial", 16, "bold"), text_color="#3E81BC", anchor="e").pack(side="right", pady=0)

        def toggle_extra():
            if extra_frame.winfo_ismapped():
                extra_frame.pack_forget()
                more_btn.configure(text="+ More")
            else:
                extra_frame.pack(fill="x", padx=16, pady=(0, 4), before=more_btn)
                more_btn.configure(text="− Less")
        #nothing for now
        extra_nutrients = [
            ("Fiber",   "-- g"),
            ("Sodium",  "-- mg"),
            ("Vitamin C", "-- mg"),
        ]
        for label, value in extra_nutrients:
            row_frame = ctk.CTkFrame(extra_frame, fg_color="transparent", height = 24)
            row_frame.pack(fill="x", pady=0)
            ctk.CTkLabel(row_frame, text=label, font=("Arial", 20), text_color="#3E81BC", anchor="w").pack(side="left", pady=0)
            ctk.CTkLabel(row_frame, text=value, font=("Arial", 16, "bold"), text_color="#3E81BC", anchor="e").pack(side="right", pady=0)
        more_btn = ctk.CTkButton(parent, text="+ More", command=toggle_extra, font=("Arial", 14), fg_color="transparent", text_color="#3A9E6F"
                                      , hover_color="#e8e8e0")
        more_btn.pack(padx = 16,pady=(0, 12))
    def _search(self):
        ingredient = self.search_entry.get().strip()
        #result = culidex.test_search()
        ingredient_find = db.search(ingredient)
        if ingredient_find.empty:
            self.search_error_label.configure(text="No matches found. Try a different term.")
            return
        selected = ingredient_find.iloc[0]["name"]
        self.show_results(selected)
        # if not ingredient:
        #     return

app = Application()
app.mainloop()