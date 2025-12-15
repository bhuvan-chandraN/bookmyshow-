import wx
import wx.grid
import time

# --- PRESENTATION THEME CONFIGURATION ---
THEME = {
    "bg_main": "#121212",  # Very dark grey
    "bg_card": "#1E1E1E",  # Slightly lighter dark grey
    "accent": "#E50914",  # Cinema Red
    "text_white": "#FFFFFF",  # White text
    "text_grey": "#B3B3B3",  # Grey text
    "seat_available": "#FFFFFF",
    "seat_selected": "#FFD700",  # Gold for better visibility
    "seat_booked": "#333333",  # Dark grey for unavailable
    "screen_color": "#555555"  # Screen visual color
}

# --- MOCK DATA ---
MOVIES = [
    {
        "id": 1,
        "title": "Avengers: Endgame",
        "genre": "Action/Sci-Fi",
        "price": 350.00,
        "timings": ["09:00 AM", "01:00 PM", "05:00 PM"],
        "description": "The Avengers take a final stand against Thanos, culminating in an epic battle for the fate of the universe."
    },
    {
        "id": 2,
        "title": "The Lion King",
        "genre": "Animation/Drama",
        "price": 250.00,
        "timings": ["10:30 AM", "02:00 PM", "06:00 PM"],
        "description": "Simba idolizes his father, King Mufasa, and takes to heart his own royal destiny, facing betrayal and destiny."
    },
    {
        "id": 3,
        "title": "Inception",
        "genre": "Sci-Fi/Thriller",
        "price": 300.00,
        "timings": ["11:00 AM", "03:30 PM", "08:00 PM"],
        "description": "A thief who steals corporate secrets through dream-sharing technology must plant an idea in a target's mind."
    },
    {
        "id": 4,
        "title": "Titanic",
        "genre": "Romance/Drama",
        "price": 200.00,
        "timings": ["12:00 PM", "04:00 PM"],
        "description": "A seventeen-year-old aristocrat falls in love with a kind but poor artist aboard the ill-fated RMS Titanic."
    }
]

# --- UPDATED DATABASE STRUCTURE ---
# Structure: { MovieID: { "Time String": [(row, col), (row, col)] } }
BOOKED_SEATS_DB = {
    1: {
        "09:00 AM": [(0, 1), (0, 2)],
        "01:00 PM": [],
        "05:00 PM": [(2, 2), (2, 3), (2, 4)]
    },
    2: {"10:30 AM": [], "02:00 PM": [], "06:00 PM": []},
    3: {"11:00 AM": [(1, 1)], "03:30 PM": [], "08:00 PM": []},
    4: {"12:00 PM": [], "04:00 PM": []}
}

# Prevent mac native metal dark-mode override (best-effort)
try:
    wx.SystemOptions.SetOption("mac.window-apple-metal", False)
except Exception:
    pass


# --- PAYMENT DIALOG ---
class PaymentDialog(wx.Dialog):
    def __init__(self, parent, total_amount):
        super().__init__(parent, title="Complete Payment", size=(450, 400))
        self.total_amount = total_amount
        self.payment_successful = False
        self.SetBackgroundColour(THEME["bg_main"])
        self.init_ui()
        self.Centre()

    def init_ui(self):
        panel = wx.Panel(self)
        panel.SetBackgroundColour(THEME["bg_card"])
        vbox = wx.BoxSizer(wx.VERTICAL)

        lbl_header = wx.StaticText(panel, label=f"Total Due: ₹{self.total_amount:.2f}")
        lbl_header.SetFont(wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        lbl_header.SetForegroundColour(THEME["accent"])
        vbox.Add(lbl_header, 0, wx.ALL | wx.CENTER, 20)

        form_sizer = wx.FlexGridSizer(rows=3, cols=2, vgap=15, hgap=10)

        def create_label(text):
            l = wx.StaticText(panel, label=text)
            l.SetForegroundColour(THEME["text_white"])
            l.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
            return l

        form_sizer.Add(create_label("Card Number:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        self.txt_card = wx.TextCtrl(panel, value="1234567890123456", size=(200, -1))
        form_sizer.Add(self.txt_card, 0, wx.EXPAND)

        form_sizer.Add(create_label("Expiry (MM/YY):"), 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        self.txt_expiry = wx.TextCtrl(panel, value="12/26", size=(80, -1))
        form_sizer.Add(self.txt_expiry, 0)

        form_sizer.Add(create_label("CVV:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        self.txt_cvv = wx.TextCtrl(panel, value="123", size=(60, -1))
        form_sizer.Add(self.txt_cvv, 0)

        vbox.Add(form_sizer, 0, wx.ALL | wx.CENTER, 20)

        self.btn_pay = wx.Button(panel, label=f"PAY ₹{self.total_amount:.2f}")
        self.btn_pay.SetBackgroundColour(THEME["accent"])
        self.btn_pay.SetForegroundColour(THEME["text_white"])
        self.btn_pay.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.btn_pay.Bind(wx.EVT_BUTTON, self.on_pay)
        vbox.Add(self.btn_pay, 0, wx.ALL | wx.EXPAND, 30)

        self.gauge = wx.Gauge(panel, range=100, size=(250, 10))
        vbox.Add(self.gauge, 0, wx.ALL | wx.EXPAND, 30)

        btn_cancel = wx.Button(panel, wx.ID_CANCEL, "Cancel Transaction")
        vbox.Add(btn_cancel, 0, wx.ALL | wx.CENTER, 5)

        panel.SetSizer(vbox)

    def on_pay(self, event):
        if len(self.txt_card.GetValue()) < 16 or len(self.txt_cvv.GetValue()) < 3:
            wx.MessageBox("Please enter valid mock card details.", "Validation Error", wx.OK | wx.ICON_ERROR)
            return

        self.btn_pay.Disable()
        self.btn_pay.SetLabel("Processing Payment...")

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_timer, self.timer)
        self.timer.Start(100)
        self.gauge_value = 0

    def on_timer(self, event):
        self.gauge_value += 5
        self.gauge.SetValue(self.gauge_value)

        if self.gauge_value >= 100:
            self.timer.Stop()
            self.payment_successful = True

            self.btn_pay.SetLabel("PAYMENT SUCCESSFUL")
            self.btn_pay.SetBackgroundColour("#46D369")  # Green for success

            wx.CallLater(1000, self.EndModal, wx.ID_OK)
        elif self.gauge_value == 50:
            self.btn_pay.SetLabel("Authorizing Bank...")


# --- SEAT SELECTION DIALOG (Updated Logic) ---

class SeatButton(wx.ToggleButton):
    def __init__(self, parent, id, label, coordinate):
        super().__init__(parent, id, label, size=(45, 45))
        self.coordinate = coordinate
        self.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.Bind(wx.EVT_TOGGLEBUTTON, self.on_toggle)

    def on_toggle(self, event):
        if self.GetValue():
            # Set to the new Gold color
            self.SetBackgroundColour(THEME["seat_selected"])
            self.SetForegroundColour("BLACK")
        else:
            self.SetBackgroundColour(wx.NullColour)
            self.SetForegroundColour("BLACK")
        event.Skip()

    def set_booked(self, is_booked):
        """ Helper to change look if booked """
        if is_booked:
            self.SetBackgroundColour(THEME["seat_booked"])
            self.SetForegroundColour("GREY")
            self.Disable()
            self.SetValue(False)
            self.SetLabel("X")
        else:
            self.SetBackgroundColour(wx.NullColour)
            self.SetForegroundColour("BLACK")
            self.Enable()
            self.SetValue(False)
            # Reset Label based on coordinate
            rows = "ABCDE"
            r, c = self.coordinate
            self.SetLabel(f"{rows[r]}{c + 1}")


class SeatSelectionDialog(wx.Dialog):
    def __init__(self, parent, movie_data):
        super().__init__(parent, title=f"Booking: {movie_data['title']}", size=(600, 750))
        self.movie = movie_data
        self.selected_seats = []
        self.ticket_price = movie_data['price']
        self.timings = movie_data['timings']
        self.SetBackgroundColour(THEME["bg_main"])

        # Ensure DB entry exists for this movie
        if self.movie['id'] not in BOOKED_SEATS_DB:
            BOOKED_SEATS_DB[self.movie['id']] = {}
        for t in self.timings:
            if t not in BOOKED_SEATS_DB[self.movie['id']]:
                BOOKED_SEATS_DB[self.movie['id']][t] = []

        self.init_ui()
        self.Centre()

        # Trigger initial load for the first time slot
        self.load_seats_for_time(self.timings[0])

    def init_ui(self):
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # 1. Header
        lbl_title = wx.StaticText(panel, label=self.movie['title'])
        lbl_title.SetFont(wx.Font(20, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        lbl_title.SetForegroundColour(THEME["text_white"])

        lbl_price = wx.StaticText(panel, label=f"Ticket Price: ₹{self.ticket_price:.2f}")
        lbl_price.SetForegroundColour(THEME["text_grey"])
        lbl_price.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))

        vbox.Add(lbl_title, 0, wx.ALL | wx.CENTER, 10)
        vbox.Add(lbl_price, 0, wx.ALL | wx.CENTER, 5)

        # 2. Time Selector
        hbox_time = wx.BoxSizer(wx.HORIZONTAL)
        lbl_time = wx.StaticText(panel, label="Select Show Time: ")
        lbl_time.SetForegroundColour("WHITE")
        lbl_time.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))

        self.choice_time = wx.Choice(panel, choices=self.timings)
        self.choice_time.SetSelection(0)
        self.choice_time.Bind(wx.EVT_CHOICE, self.on_time_changed)  # NEW: Bind Event

        hbox_time.Add(lbl_time, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        hbox_time.Add(self.choice_time, 0, wx.ALIGN_CENTER_VERTICAL)
        vbox.Add(hbox_time, 0, wx.ALL | wx.CENTER, 15)

        # 3. Screen Visual
        screen_panel = wx.Panel(panel, size=(-1, 40))
        screen_panel.SetBackgroundColour(THEME["screen_color"])
        screen_sizer = wx.BoxSizer(wx.VERTICAL)
        lbl_screen = wx.StaticText(screen_panel, label="S C R E E N")
        lbl_screen.SetForegroundColour("WHITE")
        lbl_screen.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        screen_sizer.Add(lbl_screen, 1, wx.ALIGN_CENTER | wx.ALL, 10)
        screen_panel.SetSizer(screen_sizer)
        vbox.Add(screen_panel, 0, wx.EXPAND | wx.ALL, 20)

        # 4. Seat Grid
        grid_sizer = wx.GridSizer(rows=5, cols=6, vgap=15, hgap=15)
        self.seat_buttons = {}

        rows = "ABCDE"
        for r in range(5):
            for c in range(6):
                seat_label = f"{rows[r]}{c + 1}"
                coord = (r, c)
                btn = SeatButton(panel, wx.ID_ANY, seat_label, coord)
                btn.Bind(wx.EVT_TOGGLEBUTTON, self.on_seat_click)
                grid_sizer.Add(btn, 0)
                self.seat_buttons[coord] = btn  # Store reference to update later

        vbox.Add(grid_sizer, 1, wx.ALIGN_CENTER | wx.ALL, 10)

        # 5. Legend
        hbox_legend = wx.BoxSizer(wx.HORIZONTAL)

        def add_legend_item(color, text):
            p = wx.Panel(panel, size=(20, 20))
            p.SetBackgroundColour(color)
            t = wx.StaticText(panel, label=text)
            t.SetForegroundColour("WHITE")
            hbox_legend.Add(p, 0, wx.RIGHT, 5)
            hbox_legend.Add(t, 0, wx.RIGHT, 15)

        add_legend_item(THEME["seat_available"], "Available")
        add_legend_item(THEME["seat_selected"], "Selected")  # Shows Gold
        add_legend_item(THEME["seat_booked"], "Sold")
        vbox.Add(hbox_legend, 0, wx.ALIGN_CENTER | wx.BOTTOM, 15)

        # 6. Footer
        footer_panel = wx.Panel(panel)
        footer_panel.SetBackgroundColour(THEME["bg_card"])
        footer_sizer = wx.BoxSizer(wx.VERTICAL)

        self.lbl_total = wx.StaticText(footer_panel, label="Selected: 0  |  Total: ₹0.00")
        self.lbl_total.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.lbl_total.SetForegroundColour(THEME["text_white"])
        footer_sizer.Add(self.lbl_total, 0, wx.ALIGN_CENTER | wx.TOP, 15)

        hbox_btns = wx.BoxSizer(wx.HORIZONTAL)
        btn_cancel = wx.Button(footer_panel, wx.ID_CANCEL, "Cancel")

        self.btn_proceed = wx.Button(footer_panel, wx.ID_OK, "PROCEED TO PAYMENT")
        self.btn_proceed.SetBackgroundColour(THEME["accent"])
        self.btn_proceed.SetForegroundColour("WHITE")
        self.btn_proceed.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.btn_proceed.Disable()
        self.btn_proceed.Bind(wx.EVT_BUTTON, self.on_proceed_to_payment)

        hbox_btns.Add(btn_cancel, 0, wx.ALL, 10)
        hbox_btns.Add(self.btn_proceed, 0, wx.ALL, 10)

        footer_sizer.Add(hbox_btns, 0, wx.ALIGN_CENTER | wx.BOTTOM, 15)
        footer_panel.SetSizer(footer_sizer)
        vbox.Add(footer_panel, 0, wx.EXPAND)
        panel.SetSizer(vbox)

    # --- NEW LOGIC FOR TIME HANDLING ---

    def on_time_changed(self, event):
        """ Triggered when user picks a different time from dropdown """
        new_time = self.choice_time.GetString(self.choice_time.GetSelection())
        self.load_seats_for_time(new_time)

    def load_seats_for_time(self, time_slot):
        """ Refreshes the grid based on the time slot """
        # 1. Clear current selections when switching time
        self.selected_seats = []
        self.update_totals()

        # 2. Fetch booked seats for THIS specific time
        movie_timings_db = BOOKED_SEATS_DB.get(self.movie['id'], {})
        booked_for_this_slot = movie_timings_db.get(time_slot, [])

        # 3. Update all buttons
        for coord, btn in self.seat_buttons.items():
            if coord in booked_for_this_slot:
                btn.set_booked(True)
            else:
                btn.set_booked(False)

        self.Layout()  # Refresh layout if needed

    def on_seat_click(self, event):
        btn = event.GetEventObject()
        coord = btn.coordinate

        if btn.GetValue():
            self.selected_seats.append(coord)
        else:
            self.selected_seats.remove(coord)
        self.update_totals()

    def update_totals(self):
        count = len(self.selected_seats)
        self.total_amount = count * self.ticket_price
        self.lbl_total.SetLabel(f"Selected: {count}  |  Total: ₹{self.total_amount:.2f}")

        if count > 0:
            self.btn_proceed.Enable()
            self.btn_proceed.SetBackgroundColour(THEME["accent"])
        else:
            self.btn_proceed.Disable()
            # Set to default button color on disable
            self.btn_proceed.SetBackgroundColour(wx.NullColour)

    def on_proceed_to_payment(self, event):
        if not self.selected_seats:
            return

        selected_time = self.choice_time.GetString(self.choice_time.GetSelection())

        # Since using dialogs is fine, replacing wx.MessageBox for confirmation dialog
        dlg = wx.MessageDialog(self,
                               f"Book {len(self.selected_seats)} tickets for {selected_time}?\nTotal: ₹{self.total_amount:.2f}",
                               "Confirm Booking Details", wx.YES_NO | wx.ICON_QUESTION)

        if dlg.ShowModal() != wx.ID_YES:
            dlg.Destroy()
            return
        dlg.Destroy()

        payment_dlg = PaymentDialog(self, self.total_amount)
        result = payment_dlg.ShowModal()

        if result == wx.ID_OK and payment_dlg.payment_successful:
            self.final_book_seats(selected_time)
        else:
            wx.MessageBox("Payment Cancelled or Failed.", "Status", wx.OK | wx.ICON_WARNING)

        payment_dlg.Destroy()

    def final_book_seats(self, booked_time):
        # Save to the SPECIFIC time slot in the DB
        current_booked = BOOKED_SEATS_DB[self.movie['id']].get(booked_time, [])
        BOOKED_SEATS_DB[self.movie['id']][booked_time] = current_booked + self.selected_seats

        wx.MessageBox(
            f"Success! Booked {len(self.selected_seats)} tickets for the {booked_time} show.\nEnjoy the show!",
            "Booking Confirmed", wx.OK | wx.ICON_INFORMATION)

        self.EndModal(wx.ID_OK)


class MoviePanel(wx.Panel):
    def __init__(self, parent, movie_data, size=(250, 240)):  # Increased size for content
        super().__init__(parent, size=size, style=wx.BORDER_DOUBLE)  # Added border style for definition
        self.movie_data = movie_data
        self.SetBackgroundColour(THEME["bg_card"])

        self._init_layout()
        wx.CallAfter(self.wrap_and_layout)  # Ensure wrapping happens after the window is created

    def _init_layout(self):
        self.vbox = wx.BoxSizer(wx.VERTICAL)

        # 1. Title (Top)
        self.title = wx.StaticText(self, label=self.movie_data['title'])
        self.title.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.title.SetForegroundColour(THEME["text_white"])

        # 2. Genre (Under Title)
        self.genre = wx.StaticText(self, label=self.movie_data['genre'])
        self.genre.SetForegroundColour(THEME["accent"])
        self.genre.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL))

        # 3. Description (Middle - Flexible)
        # Use wx.ST_NO_AUTORESIZE to manually control wrap
        self.desc = wx.StaticText(self, label=self.movie_data['description'],
                                  style=wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE)
        self.desc.SetForegroundColour(THEME["text_grey"])
        self.desc.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))

        # 4. Button (Bottom)
        self.btn_book = wx.Button(self, label=f"BOOK @ ₹{self.movie_data['price']:.2f}")
        self.btn_book.SetBackgroundColour(THEME["accent"])
        self.btn_book.SetForegroundColour(THEME["text_white"])
        self.btn_book.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.btn_book.Bind(wx.EVT_BUTTON, self.on_book)

        # Sizer logic: The description gets priority (proportion=1) to fill the space.
        self.vbox.Add(self.title, 0, wx.ALIGN_CENTER | wx.TOP, 15)
        self.vbox.Add(self.genre, 0, wx.ALIGN_CENTER)
        self.vbox.Add(wx.StaticLine(self), 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 5)  # Separator
        self.vbox.Add(self.desc, 1, wx.EXPAND | wx.ALL, 10)  # EXPAND and priority 1
        self.vbox.Add(self.btn_book, 0, wx.ALIGN_CENTER | wx.BOTTOM, 15)

        self.SetSizer(self.vbox)

    def wrap_and_layout(self):
        """Wraps the description text based on the panel's current width."""
        width, _ = self.GetClientSize()
        # Set wrap width to the client width minus horizontal padding (e.g., 20 pixels)
        wrap_width = max(100, width - 20)

        try:
            self.desc.Wrap(wrap_width)
        except Exception:
            # Handle cases where Wrap is not available or fails
            pass

        self.Layout()

    def on_book(self, event):
        dlg = SeatSelectionDialog(self.GetTopLevelParent(), self.movie_data)
        dlg.ShowModal()
        dlg.Destroy()


class MainFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Python BookMyShow", size=(900, 750))  # Increased frame height
        self.SetBackgroundColour(THEME["bg_main"])
        self.init_ui()
        self.Centre()

    def init_ui(self):
        panel = wx.Panel(self)
        panel.SetBackgroundColour(THEME["bg_main"])
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Header Panel
        header_panel = wx.Panel(panel)
        header_panel.SetBackgroundColour(THEME["bg_card"])
        header_sizer = wx.BoxSizer(wx.VERTICAL)

        header_text = wx.StaticText(header_panel, label="BookMyShow")
        header_text.SetFont(wx.Font(24, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        header_text.SetForegroundColour(THEME["accent"])

        sub_text = wx.StaticText(header_panel, label="PREMIUM CINEMA EXPERIENCE")
        sub_text.SetFont(wx.Font(10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_LIGHT))
        sub_text.SetForegroundColour("WHITE")

        header_sizer.Add(header_text, 0, wx.ALIGN_CENTER | wx.TOP, 15)
        header_sizer.Add(sub_text, 0, wx.ALIGN_CENTER | wx.BOTTOM, 15)
        header_panel.SetSizer(header_sizer)

        main_sizer.Add(header_panel, 0, wx.EXPAND)

        # Movie Grid
        grid = wx.GridSizer(cols=2, hgap=40, vgap=40)  # Increased gap
        for movie in MOVIES:
            # Use a slightly larger size for the movie card to prevent overlap
            movie_card = MoviePanel(panel, movie, size=(380, 240))
            grid.Add(movie_card, 0, wx.ALIGN_CENTER)

        main_sizer.Add(grid, 1, wx.ALIGN_CENTER | wx.ALL, 40)
        panel.SetSizer(main_sizer)


if __name__ == "__main__":
    app = wx.App(False)
    frame = MainFrame()
    frame.Show()
    app.MainLoop()