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
        self.region_sort_active = False
        self.current_results = []
        self.bind_all("<Button-1>", lambda event: event.widget.focus_set() if hasattr(event.widget, 'focus_set') else None)
        self.bind("<Escape>", lambda e: self.attributes("-fullscreen", False))
        # self.create_widgets()
        #fetch once and reuse for both matrix and food names
        _df = db.fetch_all()
        self._df = _df
        self.food_regions = None
        self.available_regions = None
        #build numpy matrix on initialization for faster querying and rust bindings
        self.matrix = similarity._build_matrix(_df, similarity.WEIGHTS)
        #initialize food names numpy array for index accessing
        self.food_names = similarity._build_food_names(_df)
        self.cat_map = similarity._build_category_mapping(_df)
        #tracks which categories the user currently wants included in similarity search
        #kept in sync with the checkboxes in the category selector panel
        self.selected_categories = set(self.cat_map.keys())
        self.create_widgets()


    def create_widgets(self):
        self.build_menu()
        self.build_search_page()
        self.display_results_page()
        self.show_page(self.search_page)
        
    def _bind_scroll(self, scrollable_frame):
        canvas = scrollable_frame._parent_canvas
        if sys.platform.startswith("win"):
            scrollable_frame.bind_all("<MouseWheel>",
                lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)) * 6, "units"))
        elif sys.platform == "darwin":
            scrollable_frame.bind_all("<MouseWheel>",
                lambda e: canvas.yview_scroll(int(-1 * e.delta), "units"))
        else:
            scrollable_frame.bind_all("<Button-4>",
                lambda e: canvas.yview_scroll(-1, "units"))
            scrollable_frame.bind_all("<Button-5>",
                lambda e: canvas.yview_scroll(1, "units"))

    def _unbind_scroll(self, scrollable_frame):
        if sys.platform.startswith("win") or sys.platform == "darwin":
            scrollable_frame.unbind_all("<MouseWheel>")
        else:
            scrollable_frame.unbind_all("<Button-4>")
            scrollable_frame.unbind_all("<Button-5>")
        

    def show_page(self, page):
        page.tkraise()

    def build_menu(self):
        menubar = ctk.CTkFrame(self, fg_color="#3A9E6F", height=40, corner_radius=0)
        menubar.pack(fill=tk.X, side=tk.TOP)
        menubar.pack_propagate(False)

        settings_menu = tk.Menu(self, tearoff=0)
        settings_menu.add_command(label="Region:", state="disabled")
        settings_menu.add_separator()

        region_menu_built = False
        def open_settings_menu():
            nonlocal region_menu_built
            if not region_menu_built:
                self._get_food_regions()
                for i, region in enumerate(self.available_regions):
                    settings_menu.insert_command(i + 1, label=region,
                        command=lambda r=region: self.set_region(r))
                region_menu_built = True
            x = settings_button.winfo_rootx()
            y = settings_button.winfo_rooty() + settings_button.winfo_height()
            settings_menu.tk_popup(x, y)

        settings_button = ctk.CTkButton(menubar, text="Settings", command=open_settings_menu,
        fg_color="#3A9E6F", hover_color="#2E7D57", font=("Arial", 18, "bold"),
        width=100, height=28, corner_radius=4)
        settings_button.pack(side=tk.LEFT, padx=6, pady=6)

        ctk.CTkButton(menubar, text="Categories", command=self.open_category_selector,
        fg_color="#3A9E6F", hover_color="#2E7D57", font=("Arial", 18, "bold"),
        width=100, height=28, corner_radius=4).pack(side=tk.LEFT, padx=6, pady=6)

        ctk.CTkButton(menubar, text="Saved", command=self.show_saved_page, font=("Arial", 18, "bold"),
               fg_color="#3A9E6F", hover_color="#2E7D57", width=80, height=28, corner_radius=4).pack(side=tk.LEFT, padx=4, pady=6)

        ctk.CTkButton(menubar, text="✕", command=self.destroy, font=("Arial", 12, "bold"), fg_color="#3A9E6F",
               hover_color="#2E7D57", width=36, height=28, corner_radius=4).pack(side=tk.RIGHT, padx=4, pady = 6)
        ctk.CTkButton(menubar, text="⛶", command=lambda: self.attributes("-fullscreen", not self.attributes("-fullscreen")), 
                fg_color="#3A9E6F", hover_color="#2E7D57", width=36, height=28, corner_radius=4).pack(side="right", pady=6)
    
    def set_region(self, region):
        print(f"Region set to: {region}")
        self.region_var = region
        self.region_label.configure(text=f"Current Region: {self.region_var}")
        #keep the on-screen list in sync if region sorting is currently applied
        if self.region_sort_active:
            self._render_substitute_cards()

    def _get_food_regions(self):
        if self.food_regions is None:
            self.food_regions = (self._df["country"].fillna("")
                                 .replace("", "United States").to_numpy())
            self.available_regions = sorted(set(self.food_regions))
        return self.food_regions

    def _rerank_by_region(self, results, region):
    
        if not region:
            return results
        regions = self._get_food_regions()
        return sorted(results, key=lambda r: regions[r[0]] != region)

    def open_category_selector(self):
        if hasattr(self, "category_selector_window") and self.category_selector_window.winfo_exists():
            self.category_selector_window.lift()
            self.category_selector_window.focus_force()
            return

        win = ctk.CTkToplevel(self)
        win.title("Select Categories")
        win.geometry("340x520")
        win.transient(self)
        win.attributes("-topmost", True)
        self.category_selector_window = win

        ctk.CTkLabel(win, text="Categories", font=("Arial", 20, "bold"),
                     text_color="#3E81BC").pack(pady=(16, 8))

        button_row = ctk.CTkFrame(win, fg_color="transparent")
        button_row.pack(fill="x", padx=16, pady=(0, 8))

        def set_all(value):
            for category, var in category_vars.items():
                var.set(value)
                self._on_category_toggle(category, var)

        ctk.CTkButton(button_row, text="Select All", command=lambda: set_all(True),
                      font=("Arial", 12, "bold"), fg_color="#3A9E6F",
                      hover_color="#2E7D57", width=100).pack(side="left")
        ctk.CTkButton(button_row, text="Clear All", command=lambda: set_all(False),
                      font=("Arial", 12, "bold"), fg_color="#CC4444",
                      hover_color="#a83a3a", width=100).pack(side="right")

        scroll = ctk.CTkScrollableFrame(win, fg_color="#fdfbee")
        scroll.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        category_vars = {}
        for category in sorted(self.cat_map.keys()):
            var = ctk.BooleanVar(value=category in self.selected_categories)
            checkbox = ctk.CTkCheckBox(
                scroll, text=category, variable=var,
                command=lambda cat=category, var=var: self._on_category_toggle(cat, var),
                font=("Arial", 14), text_color="#3E81BC",
                fg_color="#3A9E6F", hover_color="#2E7D57")
            checkbox.pack(anchor="w", padx=4, pady=4)
            category_vars[category] = var

        self._bind_scroll(scroll)

        def on_close():
            self._unbind_scroll(scroll)
            win.destroy()

        win.protocol("WM_DELETE_WINDOW", on_close)
        ctk.CTkButton(win, text="Done", command=on_close, font=("Arial", 12, "bold"),
                      fg_color="#3A9E6F", hover_color="#2E7D57").pack(pady=(0, 16))

    def _on_category_toggle(self, category, var):
        if var.get():
            self.selected_categories.add(category)
        else:
            self.selected_categories.discard(category)

    def get_selected_categories(self):
        """Returns a copy of the category names currently checked in the selector."""
        return set(self.selected_categories)

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
    
        self.recent_frame = ctk.CTkFrame(self.search_page, fg_color="#f0f0e8", corner_radius=8, width=450)
        self.recent_frame.pack(pady=(16, 0))
        self.recent_frame.pack_propagate(False)
        self.refresh_recent_searches()

    def build_disambiguation_page(self, matches):
        if hasattr(self, 'disambiguation_page'):
            self.disambiguation_page.destroy()
        self.disambiguation_page = ctk.CTkFrame(self, fg_color="#fdfbee", corner_radius=0)
        self.disambiguation_page.place(x=0, y=40, relwidth=1, relheight=1)
        ctk.CTkButton(self.disambiguation_page, text="← Back",
                   command=lambda: self.show_page(self.search_page),
                   fg_color="#3A9E6F", hover_color="#2E7D57", width=80).pack(anchor="w", padx=40, pady=20)
        ctk.CTkLabel(self.disambiguation_page, text="Multiple matches found. Please select one:", font=("Arial", 32, "bold"), text_color="#3E81BC").pack(anchor="w", padx=40)
        filter_entry = ctk.CTkEntry(self.disambiguation_page, width=300, font=("Arial", 13),
                                 placeholder_text="Filter results...")
        filter_entry.pack(anchor="w", padx=40, pady=(0, 10))

        scroll = ctk.CTkScrollableFrame(self.disambiguation_page, fg_color="#fdfbee")
        scroll.pack(fill="both", expand=True, padx=40, pady=(0, 20))

        # buttons = {}
        # for match in matches:
        #     btn = ctk.CTkButton(scroll, text=match, command=lambda m=match: self.show_results(m),
        #                         font=("Arial", 30, "bold"), fg_color="#f0f0e8", text_color="#3E81BC",
        #                         hover_color="#d8d8cc", anchor="w")
        #     btn.pack(fill="x", pady=4)
        #     buttons[match] = btn


        # replaced with pagination for more efficient search results

        full_matches_list = matches
        results_size = 10
        state = {"loaded": 0}
        cache = {} # buttons only constructed once for same ingredient to save performance

        def build_button(match):
            button = cache.get(match)
            if button is None:
                button = ctk.CTkButton(scroll, text=match, command=lambda m=match: self.show_results(m),
                                font=("Arial", 30, "bold"), fg_color="#f0f0e8", text_color="#3E81BC",
                                hover_color="#d8d8cc", anchor="w")
                cache[match] = button
            return button

        load_more_btn = ctk.CTkButton(scroll, text="See more results...", command=lambda: load_next_batch(),
            font=("Arial", 16, "bold"), fg_color="#e0e0d0", text_color="#3E81BC",
            hover_color="#cfcfc0")

        def get_filtered(): # if user enters text for filtering
            query = filter_entry.get().strip().lower()
            if query:
                return query, [m for m in full_matches_list if query in m.lower()]
            return query, full_matches_list

        def render():
            query, filtered = get_filtered()
            if state.get("last_query") != query:
                state["last_query"] = query
                state["loaded"] = 0

            for btn in cache.values():
                btn.pack_forget()
            load_more_btn.pack_forget()

            if state["loaded"] == 0:
                state["loaded"] = min(results_size, len(filtered))

            for match in filtered[:state["loaded"]]:
                build_button(match).pack(fill="x", pady=4)

            if state["loaded"] < len(filtered):
                load_more_btn.pack(fill="x", pady=8)

        def load_next_batch():
            _, filtered = get_filtered()
            state["loaded"] = min(state["loaded"] + results_size, len(filtered))
            render()

        filter_entry.bind("<Key>", lambda e: self.after(10, render))
        render()

    def show_saved_page(self):
        if hasattr(self, 'saved_page'):
            self.saved_page.destroy()
        self.saved_page = ctk.CTkFrame(self, fg_color="#fdfbee", corner_radius=0)
        self.saved_page.place(x=0, y=40, relwidth=1, relheight=1)
        ctk.CTkButton(self.saved_page, text="← Back",
                   command=lambda: self.show_page(self.search_page),
                   fg_color="#3A9E6F", hover_color="#2E7D57", width=80).pack(anchor="w", padx=40, pady=20)
        ctk.CTkLabel(self.saved_page, text="Saved Ingredients", font=("Arial", 32, "bold"), text_color="#3E81BC").pack(anchor="w", padx=40)

        saved = db.fetch_saved()
        if saved.empty:
            ctk.CTkLabel(self.saved_page, text="No saved ingredients yet.", font=("Arial", 20), text_color="#3E81BC").pack(anchor="w", padx=40, pady=20)
            self.show_page(self.saved_page)
            return

        scroll = ctk.CTkScrollableFrame(self.saved_page, fg_color="#fdfbee")
        scroll.pack(fill="both", expand=True, padx=40, pady=(20, 20))

        def remove_saved(name):
            db.unsave_food(name)
            self.show_saved_page()

        for name in saved["name"]:
            row_frame = ctk.CTkFrame(scroll, fg_color="transparent")
            row_frame.pack(fill="x", pady=4)
            ctk.CTkButton(row_frame, text="✕", command=lambda n=name: remove_saved(n),
                          font=("Arial", 20, "bold"), width=40, fg_color="#f0f0e8",
                          text_color="#CC4444", hover_color="#d8d8cc").pack(side="right", padx=(8, 0))
            name_btn = ctk.CTkButton(row_frame, text=name, command=lambda n=name: self.show_results(n),
                                     font=("Arial", 30, "bold"), fg_color="#f0f0e8", text_color="#3E81BC",
                                     hover_color="#d8d8cc", anchor="w")
            # food may have been removed from the database by a CSV rebuild
            if name not in self.food_names:
                name_btn.configure(state="disabled")
            name_btn.pack(side="left", fill="x", expand=True)

        self._bind_scroll(scroll)
        self.show_page(self.saved_page)

    def refresh_recent_searches(self):
        for widget in self.recent_frame.winfo_children():
            widget.destroy()

        recent = db.fetch_recent()
        if recent.empty:
            self.recent_frame.pack_forget()
            return

        self.recent_frame.pack(pady=(16, 0))
        ctk.CTkLabel(self.recent_frame, text="Recently Searched:", font=("Arial", 18, "bold"),
                     text_color="#3E81BC").pack(pady=(10, 4))

        def remove_recent(n):
            db.delete_recent_search(n)
            self.refresh_recent_searches()

        for name in recent["name"]:
            row_frame = ctk.CTkFrame(self.recent_frame, fg_color="transparent")
            row_frame.pack(fill="x", padx=8, pady=1)

            ctk.CTkButton(row_frame, text="✕", command=lambda n=name: remove_recent(n),
                          font=("Arial", 18, "bold"), width=22, height=22, fg_color="transparent",
                          text_color="#CC4444", hover_color="#e0e0d4").pack(side="right")

            btn = ctk.CTkButton(row_frame, text=name, command=lambda n=name: self.show_results(n),
                                 font=("Arial", 13), fg_color="transparent", text_color="#3E81BC",
                                 hover_color="#e0e0d4", anchor="w", height=26)
            if name not in self.food_names:
                btn.configure(state="disabled")
            btn.pack(side="left", fill="x", expand=True)

        ctk.CTkFrame(self.recent_frame, fg_color="transparent", height=8).pack()

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

        #on-demand region sorting for the substitute list below
        self.region_sort_btn = ctk.CTkButton(top_row, text="Region first: Off",
                       command=self.toggle_region_sort,
                       fg_color="#3A9E6F", hover_color="#2E7D57", width=140)
        self.region_sort_btn.pack(side="right")
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
        
        db.add_recent_search(name)
        self.after_idle(self.refresh_recent_searches)

        #dummy substitute ingredient information
        #dummy_results = [
        #    {"name": "Horseradish root", "score": 89},
        #    {"name": "Ginger root",      "score": 68},
        #    {"name": "Mustard seed",     "score": 49},
        #]

        indices = similarity._build_index_list(self.cat_map, self.selected_categories)
        #raw similarity order kept so the region toggle can re-render without re-searching
        self.current_results = similarity.get_substitutes(name, self.food_names, indices, self.matrix,top_n=30)
        self._render_substitute_cards()
        self.show_page(self.results_page)

    def toggle_region_sort(self):
        self.region_sort_active = not self.region_sort_active
        self.region_sort_btn.configure(
            text=f"Region first: {'On' if self.region_sort_active else 'Off'}")
        self._render_substitute_cards()

    def _render_substitute_cards(self):
        for widget in self.right_panel.winfo_children():
            widget.destroy()

        results = self.current_results
        if self.region_sort_active:
            results = self._rerank_by_region(results, self.region_var)

        for item in results:
            card = ctk.CTkFrame(self.right_panel, fg_color= "#fdfbee", corner_radius= 8)
            card.pack(fill = 'x', pady =6)
            self.build_substitute_card_numerical(card, item)

        self._bind_scroll(self.right_panel)


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

        if is_selected:
            name = row["name"]
            def toggle_save():
                if db.is_saved(name):
                    db.unsave_food(name)
                    save_btn.configure(text="☆ Save")
                else:
                    db.save_food(name)
                    save_btn.configure(text="★ Saved")
            save_btn = ctk.CTkButton(parent, text="★ Saved" if db.is_saved(name) else "☆ Save",
                                     command=toggle_save, font=("Arial", 14, "bold"),
                                     fg_color="#3A9E6F", hover_color="#2E7D57", text_color="white")
            save_btn.pack(padx=16, pady=(0, 16))


    def build_substitute_card_numerical(self, parent, item):
        top = ctk.CTkFrame(parent, fg_color="transparent")
        top.pack(fill="x",padx=16, pady=(12, 4))

        ctk.CTkLabel(top, text=self.
                    food_names[item[0]], font=("Arial", 24, "bold"), text_color="#3E81BC",).pack(side="left")

        #small region tag next to the name, row-aligned with the similarity indices
        region = self._get_food_regions()[item[0]]
        ctk.CTkLabel(top, text=f" {region} ", font=("Arial", 14, "bold"), text_color="#6B8F71",
                     fg_color="#e4efe0", corner_radius=6).pack(side="left", padx=(10, 0))

        score = round(item[1]*100)
        score_color = "#3A9E6F" if score >= 75 else "#E8A020" if score >= 50 else "#CC4444"
        ctk.CTkLabel(top, text=f"{score}% match", font=("Arial", 20, "bold"), text_color=score_color).pack(side="right")

        sub_name = self.food_names[item[0]]
        def toggle_save():
            if db.is_saved(sub_name):
                db.unsave_food(sub_name)
                save_btn.configure(text="☆")
            else:
                db.save_food(sub_name)
                save_btn.configure(text="★")
        save_btn = ctk.CTkButton(top, text="★" if db.is_saved(sub_name) else "☆",
                                 command=toggle_save, width=36, font=("Arial", 20),
                                 fg_color="transparent", text_color="#3A9E6F", hover_color="#e8e8e0")
        save_btn.pack(side="right", padx=(0, 8))
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
        # if not ingredient:
        #     return
        if len(ingredient_find) == 1:
            self.show_results(ingredient_find.iloc[0]["name"])
        else:
            matches = ingredient_find["name"].tolist()
            self.build_disambiguation_page(matches)
            self.show_page(self.disambiguation_page)


app = Application()
app.mainloop()