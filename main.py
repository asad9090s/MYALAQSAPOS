"""
POS Mobile - Main Kivy App
Aap ke Tkinter 'Shop ok.py' ka Android version
Same UI flow: Search -> Cart -> Customer -> Checkout -> Save Sale
"""
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.checkbox import CheckBox
from kivy.uix.togglebutton import ToggleButton
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp, sp
from kivy.utils import get_color_from_hex

from db import MobileDB
from datetime import datetime

# ════════════════════════════════════════════════════════════
# COLOR PALETTE (same as Tkinter app)
# ════════════════════════════════════════════════════════════
C_HEADER = get_color_from_hex("#1e293b")
C_ACCENT = get_color_from_hex("#6366f1")
C_ACCENT_DARK = get_color_from_hex("#4f46e5")
C_AMBER = get_color_from_hex("#f59e0b")
C_SUCCESS = get_color_from_hex("#10b981")
C_DANGER = get_color_from_hex("#ef4444")
C_PURPLE = get_color_from_hex("#8b5cf6")
C_TEXT = get_color_from_hex("#334155")
C_TEXT_LIGHT = get_color_from_hex("#94a3b8")
C_CARD_BG = get_color_from_hex("#ffffff")
C_CARD_BORDER = get_color_from_hex("#e2e8f0")
C_INPUT_BG = get_color_from_hex("#f8fafc")
C_INPUT_BD = get_color_from_hex("#cbd5e1")
C_SECTION_BG = get_color_from_hex("#f1f5f9")
C_BG = get_color_from_hex("#f0f2f5")
C_CART_HDR = get_color_from_hex("#0f172a")


# ════════════════════════════════════════════════════════════
# HELPER WIDGETS
# ════════════════════════════════════════════════════════════
class Card(BoxLayout):
    """White card with border, like Tkinter Frame with highlightthickness"""
    def __init__(self, **kw):
        kw.setdefault('orientation', 'vertical')
        kw.setdefault('padding', dp(10))
        kw.setdefault('spacing', dp(6))
        super().__init__(**kw)
        with self.canvas.before:
            Color(*C_CARD_BG)
            self.bg = Rectangle(pos=self.pos, size=self.size)
            Color(*C_CARD_BORDER)
            self.border = Rectangle(pos=(self.x, self.y), size=(self.width, 1))
            Color(*C_CARD_BORDER)
            self.border2 = Rectangle(pos=(self.x, self.y + self.height - 1), size=(self.width, 1))
        self.bind(pos=self._update, size=self._update)

    def _update(self, inst, val):
        self.bg.pos = self.pos
        self.bg.size = self.size
        self.border.pos = self.pos
        self.border.size = (self.width, 1)
        self.border2.pos = (self.x, self.y + self.height - 1)
        self.border2.size = (self.width, 1)


class SectionLabel(Label):
    """Bold label for section headers"""
    def __init__(self, text, color=C_TEXT_LIGHT, **kw):
        kw['text'] = text
        kw['color'] = color
        kw['font_size'] = sp(11)
        kw['bold'] = True
        kw['size_hint_y'] = None
        kw['height'] = dp(18)
        kw.setdefault('halign', 'left')
        kw.setdefault('valign', 'middle')
        super().__init__(**kw)
        self.bind(size=lambda *a: setattr(self, 'text_size', (self.width, None)))


class HeaderBar(BoxLayout):
    """Dark slate header with shop name"""
    def __init__(self, shop_name, **kw):
        kw.setdefault('orientation', 'horizontal')
        kw.setdefault('size_hint_y', None)
        kw.setdefault('height', dp(50))
        kw.setdefault('padding', (dp(12), dp(8)))
        super().__init__(**kw)
        with self.canvas.before:
            Color(*C_HEADER)
            self.bg = Rectangle(pos=self.pos, size=self.size)
            Color(*C_ACCENT)
            self.line = Rectangle(pos=(self.x, self.y), size=(self.width, dp(3)))
        self.bind(pos=self._upd, size=self._upd)

        self.lbl_shop = Label(text=shop_name, color=(1,1,1,1), font_size=sp(16),
                              bold=True, size_hint_x=0.7, halign='left', valign='middle')
        self.lbl_shop.bind(size=lambda *a: setattr(self.lbl_shop, 'text_size', (self.lbl_shop.width, None)))
        self.add_widget(self.lbl_shop)

        self.lbl_sub = Label(text="POS Mobile", color=C_TEXT_LIGHT[:3] + (1,),
                             font_size=sp(11), size_hint_x=0.3, halign='right', valign='middle')
        self.lbl_sub.bind(size=lambda *a: setattr(self.lbl_sub, 'text_size', (self.lbl_sub.width, None)))
        self.add_widget(self.lbl_sub)

    def _upd(self, inst, val):
        self.bg.pos = self.pos
        self.bg.size = self.size
        self.line.pos = (self.x, self.y)
        self.line.size = (self.width, dp(3))


# ════════════════════════════════════════════════════════════
# POS SCREEN (main billing)
# ════════════════════════════════════════════════════════════
class POSScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.db = None
        self.cart = []
        self.customer = {'id': None, 'name': 'Walk-in Customer', 'shop': 'N/A', 'phone': 'N/A'}
        self.disc_mode = 'EveryItem'
        self.pay_type = 'Cash'
        self.print_mode = '3inch'

        # Main scrollable layout
        self.layout = BoxLayout(orientation='vertical', spacing=dp(6), padding=dp(6))
        with self.layout.canvas.before:
            Color(*C_BG)
            self.bg = Rectangle(pos=self.layout.pos, size=self.layout.size)
        self.layout.bind(pos=lambda i, v: (setattr(self.bg, 'pos', v), setattr(self.bg, 'size', self.layout.size)))

        self.header = HeaderBar("My Shop")
        self.layout.add_widget(self.header)

        # Search card
        self._build_search_card()
        # Customer card
        self._build_customer_card()
        # Cart card
        self._build_cart_card()
        # Checkout card
        self._build_checkout_card()

        scroll = ScrollView(size_hint_y=1)
        scroll.add_widget(self.layout)
        self.add_widget(scroll)

    # ════════════════════════════════════════════════════════════
    # SEARCH CARD
    # ════════════════════════════════════════════════════════════
    def _build_search_card(self):
        card = Card(size_hint_y=None)
        card.add_widget(SectionLabel("SEARCH PRODUCT", C_ACCENT))

        # Mode toggles
        mode_row = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(4))
        self.btn_barcode = ToggleButton(text="Barcode", group="mode",
            state="down", color=(1,1,1,1), background_color=C_ACCENT,
            font_size=sp(12))
        self.btn_name = ToggleButton(text="Name", group="mode",
            color=C_TEXT, background_normal="", background_color=C_SECTION_BG,
            font_size=sp(12))
        self.btn_barcode.bind(state=lambda i, v: self._on_mode_change())
        self.btn_name.bind(state=lambda i, v: self._on_mode_change())
        mode_row.add_widget(self.btn_barcode)
        mode_row.add_widget(self.btn_name)
        card.add_widget(mode_row)

        # Search input
        self.search_input = TextInput(hint_text="Scan barcode or type name...",
            size_hint_y=None, height=dp(44), font_size=sp(16),
            multiline=False, background_color=C_INPUT_BG,
            foreground_color=C_TEXT)
        self.search_input.bind(on_text_validate=self._on_search_enter)
        card.add_widget(self.search_input)

        # Qty + Disc row
        row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(6))
        qty_box = BoxLayout(orientation='vertical', size_hint_x=0.3)
        qty_box.add_widget(SectionLabel("QTY"))
        self.qty_input = TextInput(text="1", size_hint_y=None, height=dp(28),
            font_size=sp(14), multiline=False, halign='center',
            input_filter='int')
        qty_box.add_widget(self.qty_input)
        row.add_widget(qty_box)

        disc_box = BoxLayout(orientation='vertical', size_hint_x=0.3)
        disc_box.add_widget(SectionLabel("DISC"))
        self.disc_input = TextInput(text="0", size_hint_y=None, height=dp(28),
            font_size=sp(14), multiline=False, halign='center',
            input_filter='float')
        disc_box.add_widget(self.disc_input)
        row.add_widget(disc_box)

        btn_add = Button(text="+ ADD", size_hint_x=0.4,
            color=(1,1,1,1), background_color=C_ACCENT,
            font_size=sp(14), bold=True)
        btn_add.bind(on_release=self._on_search_enter)
        row.add_widget(btn_add)
        card.add_widget(row)

        # Product dropdown (for Name search)
        self.product_list = BoxLayout(orientation='vertical', size_hint_y=None,
            height=0, spacing=dp(2))
        card.add_widget(self.product_list)

        self.layout.add_widget(card)

    def _on_mode_change(self):
        if self.btn_barcode.state == 'down':
            self.search_input.hint_text = "Scan barcode..."
        else:
            self.search_input.hint_text = "Type product name..."
        self.search_input.focus = True

    def _on_search_enter(self, *args):
        term = self.search_input.text.strip()
        if not term:
            return
        if self.btn_barcode.state == 'down':
            p = self.db.get_product_by_barcode(term)
            if p:
                self._add_to_cart(p)
                self.search_input.text = ""
            else:
                self._toast(f"Barcode not found: {term}")
        else:
            self._show_product_list(term)

    def _show_product_list(self, term):
        self.product_list.clear_widgets()
        products = self.db.get_products(term)
        if not products:
            self.product_list.add_widget(Label(
                text="No products found", color=C_TEXT_LIGHT,
                size_hint_y=None, height=dp(28), font_size=sp(12)))
            self.product_list.height = dp(28)
            return
        for p in products[:15]:  # limit to 15 for performance
            btn = Button(
                text=f"{p['name']}  |  Rs {p['price']:.0f}  |  Stk: {p['stock']}",
                size_hint_y=None, height=dp(36),
                color=C_TEXT, background_color=C_INPUT_BG,
                font_size=sp(12), halign='left')
            btn.bind(on_release=lambda i, prod=p: self._add_to_cart_from_list(prod))
            self.product_list.add_widget(btn)
        self.product_list.height = dp(36) * min(15, len(products)) + dp(4)

    def _add_to_cart_from_list(self, prod):
        self._add_to_cart(prod)
        self.product_list.clear_widgets()
        self.product_list.height = 0
        self.search_input.text = ""

    def _add_to_cart(self, prod):
        try:
            qty = int(self.qty_input.text or 1)
            disc = float(self.disc_input.text or 0) if self.disc_mode == 'EveryItem' else 0
        except ValueError:
            qty, disc = 1, 0

        if prod['stock'] < qty:
            self._toast(f"Short stock! Only {prod['stock']} left.")
            return

        # Check if already in cart
        for item in self.cart:
            if item['id'] == prod['id']:
                item['qty'] += qty
                if self.disc_mode == 'EveryItem':
                    item['disc'] += disc
                self._render_cart()
                self._toast(f"Added: {prod['name']} (x{qty})")
                return

        self.cart.append({
            'id': prod['id'],
            'name': prod['name'],
            'price': prod['price'],
            'barcode': prod.get('barcode', ''),
            'qty': qty,
            'disc': disc,
        })
        self._render_cart()
        self._toast(f"Added: {prod['name']} (x{qty})")

    # ════════════════════════════════════════════════════════════
    # CUSTOMER CARD
    # ════════════════════════════════════════════════════════════
    def _build_customer_card(self):
        card = Card(size_hint_y=None)
        card.add_widget(SectionLabel("CUSTOMER", C_PURPLE))

        # Customer search row
        row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(4))
        self.cust_search = TextInput(hint_text="Search customer...",
            size_hint_x=0.7, font_size=sp(14), multiline=False,
            background_color=C_INPUT_BG)
        self.cust_search.bind(on_text_validate=self._on_cust_search)
        row.add_widget(self.cust_search)

        btn_find = Button(text="FIND", size_hint_x=0.3,
            color=(1,1,1,1), background_color=C_PURPLE, font_size=sp(12))
        btn_find.bind(on_release=self._on_cust_search)
        row.add_widget(btn_find)
        card.add_widget(row)

        # Customer info display
        self.lbl_cust_info = Label(
            text="Walk-in Customer | Shop: N/A | Ph: N/A",
            size_hint_y=None, height=dp(28),
            color=C_TEXT, font_size=sp(12), halign='left', valign='middle')
        self.lbl_cust_info.bind(size=lambda i, v: setattr(self.lbl_cust_info, 'text_size', (v[0], v[1])))
        card.add_widget(self.lbl_cust_info)

        # Customer dropdown
        self.cust_list = BoxLayout(orientation='vertical', size_hint_y=None, height=0, spacing=dp(2))
        card.add_widget(self.cust_list)

        # New customer button
        btn_new = Button(text="+ New Customer", size_hint_y=None, height=dp(34),
            color=(1,1,1,1), background_color=C_SUCCESS, font_size=sp(12))
        btn_new.bind(on_release=self._show_new_customer_popup)
        card.add_widget(btn_new)

        self.layout.add_widget(card)

    def _on_cust_search(self, *args):
        term = self.cust_search.text.strip()
        if not term:
            return
        customers = self.db.get_customers(term)
        self.cust_list.clear_widgets()
        if not customers:
            self.cust_list.add_widget(Label(text="No customers found",
                color=C_TEXT_LIGHT, size_hint_y=None, height=dp(28), font_size=sp(12)))
            self.cust_list.height = dp(28)
            return
        for c in customers[:10]:
            btn = Button(
                text=f"{c['name']}  |  {c.get('fatherName','N/A')}  |  {c.get('Phone','N/A')}",
                size_hint_y=None, height=dp(34),
                color=C_TEXT, background_color=C_INPUT_BG,
                font_size=sp(11), halign='left')
            btn.bind(on_release=lambda i, cust=c: self._select_customer(cust))
            self.cust_list.add_widget(btn)
        self.cust_list.height = dp(34) * min(10, len(customers)) + dp(4)

    def _select_customer(self, cust):
        self.customer = cust
        self.lbl_cust_info.text = f"{cust['name']} | Shop: {cust.get('fatherName','N/A')} | Ph: {cust.get('Phone','N/A')}"
        self.cust_list.clear_widgets()
        self.cust_list.height = 0
        self.cust_search.text = ""

    def _show_new_customer_popup(self, *args):
        content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(8))
        content.add_widget(Label(text="New Customer", font_size=sp(18), bold=True, size_hint_y=None, height=dp(40)))

        name_input = TextInput(hint_text="Name", size_hint_y=None, height=dp(40), font_size=sp(14))
        shop_input = TextInput(hint_text="Shop", size_hint_y=None, height=dp(40), font_size=sp(14))
        phone_input = TextInput(hint_text="Phone", size_hint_y=None, height=dp(40), font_size=sp(14))
        content.add_widget(name_input)
        content.add_widget(shop_input)
        content.add_widget(phone_input)

        btn_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
        btn_save = Button(text="SAVE", color=(1,1,1,1), background_color=C_SUCCESS)
        btn_cancel = Button(text="CANCEL", color=(1,1,1,1), background_color=C_DANGER)
        btn_row.add_widget(btn_save)
        btn_row.add_widget(btn_cancel)
        content.add_widget(btn_row)

        popup = Popup(title="Create Customer", content=content,
            size_hint=(0.9, None), height=dp(280), auto_dismiss=False)

        def do_save(*a):
            n = name_input.text.strip()
            s = shop_input.text.strip() or "N/A"
            p = phone_input.text.strip() or "0000000000"
            if not n:
                return
            new_id = self.db.add_customer(n, s, p)
            self._select_customer({'id': new_id, 'name': n, 'fatherName': s, 'Phone': p})
            self._toast(f"Customer created: {n}")
            popup.dismiss()

        btn_save.bind(on_release=do_save)
        btn_cancel.bind(on_release=popup.dismiss)
        popup.open()

    # ════════════════════════════════════════════════════════════
    # CART CARD
    # ════════════════════════════════════════════════════════════
    def _build_cart_card(self):
        card = Card(size_hint_y=None)
        # Header
        hdr = BoxLayout(size_hint_y=None, height=dp(36))
        with hdr.canvas.before:
            Color(*C_CART_HDR)
            self.cart_hdr_bg = Rectangle(pos=hdr.pos, size=hdr.size)
        hdr.bind(pos=lambda i, v: setattr(self.cart_hdr_bg, 'pos', v),
                 size=lambda i, v: setattr(self.cart_hdr_bg, 'size', v))
        self.lbl_cart_hdr = Label(text="  CART (0 items)", color=(1,1,1,1),
            font_size=sp(13), bold=True, halign='left')
        self.lbl_cart_hdr.bind(size=lambda i, v: setattr(self.lbl_cart_hdr, 'text_size', (v[0], v[1])))
        hdr.add_widget(self.lbl_cart_hdr)
        self.lbl_cart_total = Label(text="Rs 0.00  ", color=C_AMBER,
            font_size=sp(13), bold=True, halign='right')
        self.lbl_cart_total.bind(size=lambda i, v: setattr(self.lbl_cart_total, 'text_size', (v[0], v[1])))
        hdr.add_widget(self.lbl_cart_total)
        card.add_widget(hdr)

        # Cart items container
        self.cart_items = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(80))
        card.add_widget(self.cart_items)

        # Clear button
        btn_clear = Button(text="Clear Cart", size_hint_y=None, height=dp(30),
            color=(1,1,1,1), background_color=C_DANGER, font_size=sp(11))
        btn_clear.bind(on_release=self._clear_cart)
        card.add_widget(btn_clear)

        self.layout.add_widget(card)
        self._render_cart()

    def _render_cart(self):
        self.cart_items.clear_widgets()
        if not self.cart:
            self.cart_items.add_widget(Label(
                text="Cart is empty. Scan a product to start.",
                color=C_TEXT_LIGHT, font_size=sp(12), size_hint_y=None, height=dp(60)))
            self.cart_items.height = dp(60)
        else:
            total = 0
            for idx, item in enumerate(self.cart):
                row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(2))
                item_total = (item['price'] * item['qty']) - item['disc']
                total += item_total

                info = Label(
                    text=f"{item['name']}\nRs {item['price']:.0f} x {item['qty']} = Rs {item_total:.0f}",
                    color=C_TEXT, font_size=sp(11), halign='left', valign='middle',
                    size_hint_x=0.7)
                info.bind(size=lambda i, v: setattr(info, 'text_size', (v[0], v[1])))
                row.add_widget(info)

                btn_rem = Button(text="X", size_hint_x=0.15,
                    color=(1,1,1,1), background_color=C_DANGER, font_size=sp(12))
                btn_rem.bind(on_release=lambda i, ix=idx: self._remove_item(ix))
                row.add_widget(btn_rem)

                btn_edit = Button(text="Edit", size_hint_x=0.15,
                    color=(1,1,1,1), background_color=C_ACCENT, font_size=sp(10))
                btn_edit.bind(on_release=lambda i, ix=idx, it=item: self._edit_item(ix, it))
                row.add_widget(btn_edit)

                self.cart_items.add_widget(row)

            self.cart_items.height = dp(50) * len(self.cart) + dp(4)
            self.lbl_cart_total.text = f"Rs {total:.2f}  "

        count = len(self.cart)
        self.lbl_cart_hdr.text = f"  CART ({count} item{'s' if count != 1 else ''})"
        self._calc_totals()

    def _remove_item(self, idx):
        if 0 <= idx < len(self.cart):
            self.cart.pop(idx)
            self._render_cart()

    def _edit_item(self, idx, item):
        content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(8))
        content.add_widget(Label(text=item['name'], font_size=sp(14), bold=True, size_hint_y=None, height=dp(36)))
        qty_in = TextInput(text=str(item['qty']), size_hint_y=None, height=dp(40), font_size=sp(14))
        disc_in = TextInput(text=str(item['disc']), size_hint_y=None, height=dp(40), font_size=sp(14))
        content.add_widget(Label(text="Qty:", size_hint_y=None, height=dp(20), font_size=sp(11), halign='left'))
        content.add_widget(qty_in)
        content.add_widget(Label(text="Disc:", size_hint_y=None, height=dp(20), font_size=sp(11), halign='left'))
        content.add_widget(disc_in)
        btn_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
        btn_ok = Button(text="UPDATE", color=(1,1,1,1), background_color=C_SUCCESS)
        btn_cancel = Button(text="CANCEL", color=(1,1,1,1), background_color=C_TEXT_LIGHT)
        btn_row.add_widget(btn_ok)
        btn_row.add_widget(btn_cancel)
        content.add_widget(btn_row)

        popup = Popup(title="Edit Item", content=content,
            size_hint=(0.9, None), height=dp(280), auto_dismiss=False)

        def do_save(*a):
            try:
                self.cart[idx]['qty'] = max(1, int(qty_in.text or 1))
                self.cart[idx]['disc'] = max(0, float(disc_in.text or 0))
            except ValueError:
                pass
            self._render_cart()
            popup.dismiss()

        btn_ok.bind(on_release=do_save)
        btn_cancel.bind(on_release=popup.dismiss)
        popup.open()

    def _clear_cart(self, *args):
        if not self.cart:
            return
        content = BoxLayout(orientation='vertical', padding=dp(20))
        content.add_widget(Label(text="Clear entire cart?", font_size=sp(16)))
        btn_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
        btn_yes = Button(text="YES", color=(1,1,1,1), background_color=C_DANGER)
        btn_no = Button(text="NO", color=(1,1,1,1), background_color=C_TEXT_LIGHT)
        btn_row.add_widget(btn_yes)
        btn_row.add_widget(btn_no)
        content.add_widget(btn_row)
        popup = Popup(title="Confirm", content=content, size_hint=(0.8, None), height=dp(160))
        btn_yes.bind(on_release=lambda *a: (self.cart.clear(), self._render_cart(), popup.dismiss()))
        btn_no.bind(on_release=popup.dismiss)
        popup.open()

    # ════════════════════════════════════════════════════════════
    # CHECKOUT CARD
    # ════════════════════════════════════════════════════════════
    def _build_checkout_card(self):
        card = Card(size_hint_y=None)
        card.add_widget(SectionLabel("CHECKOUT", C_ACCENT))

        # Discount mode
        mode_row = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(4))
        self.btn_mode_item = ToggleButton(text="Per Item", group="discmode",
            state="down", color=(1,1,1,1), background_color=C_ACCENT, font_size=sp(11))
        self.btn_mode_overall = ToggleButton(text="Overall", group="discmode",
            color=C_TEXT, background_color=C_SECTION_BG, font_size=sp(11))
        self.btn_mode_pct = ToggleButton(text="Percent %", group="discmode",
            color=C_TEXT, background_color=C_SECTION_BG, font_size=sp(11))
        self.btn_mode_item.bind(state=lambda i, v: self._on_disc_mode_change())
        self.btn_mode_overall.bind(state=lambda i, v: self._on_disc_mode_change())
        self.btn_mode_pct.bind(state=lambda i, v: self._on_disc_mode_change())
        mode_row.add_widget(self.btn_mode_item)
        mode_row.add_widget(self.btn_mode_overall)
        mode_row.add_widget(self.btn_mode_pct)
        card.add_widget(mode_row)

        # Bill Disc
        bill_box = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(50))
        bill_box.add_widget(SectionLabel("BILL DISC"))
        self.bill_disc_input = TextInput(text="0", size_hint_y=None, height=dp(28),
            font_size=sp(14), multiline=False, halign='center',
            input_filter='float', disabled=True, background_color=C_SECTION_BG)
        self.bill_disc_input.bind(text=lambda i, v: self._calc_totals())
        bill_box.add_widget(self.bill_disc_input)
        card.add_widget(bill_box)

        # Grand Total + Paid + Balance
        totals_grid = GridLayout(cols=2, size_hint_y=None, height=dp(110), spacing=dp(4))
        totals_grid.add_widget(SectionLabel("GRAND TOTAL"))
        self.lbl_grand = Label(text="0.00", color=C_ACCENT, font_size=sp(18), bold=True)
        totals_grid.add_widget(self.lbl_grand)
        totals_grid.add_widget(SectionLabel("PAID"))
        self.paid_input = TextInput(text="0", size_hint_y=None, height=dp(32),
            font_size=sp(14), multiline=False, halign='center', input_filter='float')
        self.paid_input.bind(text=lambda i, v: self._calc_totals())
        totals_grid.add_widget(self.paid_input)
        totals_grid.add_widget(SectionLabel("BALANCE"))
        self.lbl_balance = Label(text="0.00", color=C_SUCCESS, font_size=sp(18), bold=True)
        totals_grid.add_widget(self.lbl_balance)
        card.add_widget(totals_grid)

        # Cash Disc + Comments
        row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(6))
        cd_box = BoxLayout(orientation='vertical', size_hint_x=0.5)
        cd_box.add_widget(SectionLabel("CASH DISC"))
        self.cash_disc_input = TextInput(text="0", size_hint_y=None, height=dp(28),
            font_size=sp(14), multiline=False, halign='center', input_filter='float')
        self.cash_disc_input.bind(text=lambda i, v: self._calc_totals())
        cd_box.add_widget(self.cash_disc_input)
        row.add_widget(cd_box)
        cm_box = BoxLayout(orientation='vertical', size_hint_x=0.5)
        cm_box.add_widget(SectionLabel("COMMENTS"))
        self.comments_input = TextInput(text="N/A", size_hint_y=None, height=dp(28),
            font_size=sp(12), multiline=False)
        cm_box.add_widget(self.comments_input)
        row.add_widget(cm_box)
        card.add_widget(row)

        # Pay type toggles
        pay_row = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(4))
        self.btn_cash = ToggleButton(text="Cash", group="pay",
            state="down", color=(1,1,1,1), background_color=C_SUCCESS, font_size=sp(11))
        self.btn_online = ToggleButton(text="Online", group="pay",
            color=C_TEXT, background_color=C_SECTION_BG, font_size=sp(11))
        self.btn_cash.bind(state=lambda i, v: setattr(self, 'pay_type', 'Cash' if self.btn_cash.state == 'down' else 'Online'))
        self.btn_online.bind(state=lambda i, v: setattr(self, 'pay_type', 'Cash' if self.btn_cash.state == 'down' else 'Online'))
        pay_row.add_widget(self.btn_cash)
        pay_row.add_widget(self.btn_online)
        card.add_widget(pay_row)

        # Save button
        btn_save = Button(text="SAVE & PROCESS SALE", size_hint_y=None, height=dp(50),
            color=(1,1,1,1), background_color=C_ACCENT, font_size=sp(15), bold=True)
        btn_save.bind(on_release=self._process_sale)
        card.add_widget(btn_save)

        self.layout.add_widget(card)

    def _on_disc_mode_change(self):
        if self.btn_mode_item.state == 'down':
            self.disc_mode = 'EveryItem'
            self.disc_input.disabled = False
            self.bill_disc_input.disabled = True
            self.bill_disc_input.text = "0"
        elif self.btn_mode_overall.state == 'down':
            self.disc_mode = 'OverAll'
            self.disc_input.disabled = True
            self.disc_input.text = "0"
            self.bill_disc_input.disabled = False
        else:
            self.disc_mode = 'Percentage'
            self.disc_input.disabled = True
            self.disc_input.text = "0"
            self.bill_disc_input.disabled = False
        self._calc_totals()

    def _calc_totals(self, *args):
        subtotal = sum((i['price'] * i['qty']) - i['disc'] for i in self.cart)
        try:
            bd = float(self.bill_disc_input.text or 0)
        except ValueError:
            bd = 0
        if self.disc_mode == 'OverAll':
            gt = max(0, subtotal - bd)
        elif self.disc_mode == 'Percentage':
            gt = max(0, subtotal - (bd / 100) * subtotal) if subtotal > 0 else 0
        else:
            gt = subtotal

        try:
            cd = float(self.cash_disc_input.text or 0)
        except ValueError:
            cd = 0
        net_total = max(0, gt - cd)

        # Auto-fill paid if empty
        if self.cart and (not self.paid_input.text or self.paid_input.text == "0"):
            self.paid_input.text = f"{net_total:.2f}"

        try:
            paid = float(self.paid_input.text or 0)
        except ValueError:
            paid = 0
        balance = max(0, net_total - paid)

        self.lbl_grand.text = f"{gt:.2f}"
        self.lbl_balance.text = f"{balance:.2f}"
        self.lbl_balance.color = C_DANGER if balance > 0 else (C_SUCCESS if balance == 0 else C_ACCENT)
        self.lbl_cart_total.text = f"Rs {gt:.2f}  "

    def _process_sale(self, *args):
        if not self.cart:
            self._toast("Cart is empty!")
            return

        try:
            bd = float(self.bill_disc_input.text or 0)
            cd = float(self.cash_disc_input.text or 0)
            paid = float(self.paid_input.text or 0)
        except ValueError:
            bd = cd = paid = 0

        gt = float(self.lbl_grand.text)
        net_total = max(0, gt - cd)

        pay_method, pay_ref = "", ""
        if self.pay_type == "Online":
            pay_method = self._prompt("Payment Method", "e.g. JazzCash") or "N/A"
            pay_ref = self._prompt("Reference", "Txn ID") or "N/A"

        invoice_num, balance = self.db.save_sale(
            items=self.cart,
            customer_id=self.customer.get('id'),
            total=gt,
            paid=paid,
            comments=self.comments_input.text or "N/A",
            pay_type=self.pay_type,
            pay_method=pay_method,
            pay_ref=pay_ref,
            bill_disc=bd,
            cash_disc=cd,
            disc_mode=self.disc_mode
        )

        # Success popup
        msg = (f"Sale Saved!\n\n"
               f"Invoice: {invoice_num}\n"
               f"Total: Rs {net_total:.2f}\n"
               f"Paid: Rs {paid:.2f}\n"
               f"Balance: Rs {balance:.2f}")
        content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        content.add_widget(Label(text=msg, font_size=sp(14), halign='center'))
        btn = Button(text="OK", color=(1,1,1,1), background_color=C_SUCCESS, size_hint_y=None, height=dp(44))
        content.add_widget(btn)
        popup = Popup(title="Success", content=content, size_hint=(0.85, None), height=dp(280))
        btn.bind(on_release=popup.dismiss)
        popup.open()

        # Reset
        self.cart.clear()
        self.bill_disc_input.text = "0"
        self.cash_disc_input.text = "0"
        self.paid_input.text = "0"
        self.comments_input.text = "N/A"
        self.customer = {'id': None, 'name': 'Walk-in Customer', 'shop': 'N/A', 'phone': 'N/A'}
        self.lbl_cust_info.text = "Walk-in Customer | Shop: N/A | Ph: N/A"
        self._render_cart()

    def _prompt(self, title, hint):
        """Simple text input popup. Returns string or empty."""
        result = []

        content = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))
        inp = TextInput(hint_text=hint, size_hint_y=None, height=dp(44), font_size=sp(14), multiline=False)
        content.add_widget(inp)
        btn_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
        btn_ok = Button(text="OK", color=(1,1,1,1), background_color=C_SUCCESS)
        btn_cancel = Button(text="CANCEL", color=(1,1,1,1), background_color=C_TEXT_LIGHT)
        btn_row.add_widget(btn_ok)
        btn_row.add_widget(btn_cancel)
        content.add_widget(btn_row)

        popup = Popup(title=title, content=content, size_hint=(0.85, None), height=dp(180), auto_dismiss=False)

        def do_ok(*a):
            result.append(inp.text.strip())
            popup.dismiss()

        btn_ok.bind(on_release=do_ok)
        btn_cancel.bind(on_release=lambda *a: popup.dismiss())
        popup.open()
        return result[0] if result else ""

    def _toast(self, msg):
        """Quick popup notification"""
        content = Label(text=msg, font_size=sp(14), color=C_TEXT)
        popup = Popup(title="", content=content, size_hint=(0.7, None), height=dp(80), auto_dismiss=True)
        popup.open()
        # auto-dismiss after 1.5s
        from kivy.clock import Clock
        Clock.schedule_once(lambda *a: popup.dismiss(), 1.5)


# ════════════════════════════════════════════════════════════
# APP
# ════════════════════════════════════════════════════════════
class POSApp(App):
    def build(self):
        self.title = "POS Mobile"
        # Set window size on desktop
        try:
            Window.size = (400, 720)
        except Exception:
            pass

        sm = ScreenManager()
        self.pos_screen = POSScreen(name='pos')
        sm.add_widget(self.pos_screen)

        # Init DB after screen is shown (Android storage path needs app context)
        from kivy.clock import Clock
        Clock.schedule_once(self._init_db, 0.1)
        return sm

    def _init_db(self, *args):
        try:
            self.pos_screen.db = MobileDB()
            # Seed sample data for testing
            added = self.pos_screen.db.seed_sample_data()
            if added:
                self.pos_screen._toast("Sample data added - 10 products, 4 customers")
        except Exception as e:
            # Show error
            content = Label(text=f"DB Init Error:\n{e}", font_size=sp(12))
            Popup(title="Error", content=content, size_hint=(0.9, None), height=dp(200)).open()

    def on_pause(self):
        # Android: allow pausing
        return True

    def on_resume(self):
        pass


if __name__ == '__main__':
    POSApp().run()
