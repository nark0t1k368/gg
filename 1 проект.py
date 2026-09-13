from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Rectangle, Line
from kivy.core.text import Label as CoreLabel
from random import randint, uniform, random
from math import sin


Window.size = (1000, 650)


class Game(Widget):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # =========================
        # WORLD
        # =========================
        self.world_width = 6000
        self.world_height = 900

        # =========================
        # LOCATION
        # =========================
        self.location = "normal"

        self.locations = {
            "normal": {
                "name": "Звичайна місцевість",
                "unlocked": True,
                "price": 0
            },
            "city": {
                "name": "Місто",
                "unlocked": False,
                "price": 1000
            },
            "moon": {
                "name": "Місяць",
                "unlocked": False,
                "price": 2500
            }
        }

        # =========================
        # PLAYER
        # =========================
        self.player_x = 500
        self.player_y = 140
        self.speed = 7
        self.player_direction = 1

        # =========================
        # CAMERA
        # =========================
        self.camera_x = 0

        # =========================
        # RESOURCES
        # =========================
        self.coins = 500
        self.brains = 20

        # =========================
        # INPUT
        # =========================
        self.left = False
        self.right = False

        # =========================
        # OBJECTS
        # =========================
        self.projectiles = []
        self.flying_brains = []
        self.zombies = []

        # Бос може періодично викликати швидких тіньових зомбі.
        self.boss_summon_interval = 4.0
        self.boss_summon_max = 4
        self.boss_max_hp = 10
        self.shadow_mutant_heal_interval = 2.0
        self.shadow_mutant_heal_chance = 0.50

        # =========================
        # МІСЯЧНІ БОССИ
        # =========================
        self.moon_boss1_kills = 0
        self.moon_boss2_unlocked = False

        # Місячних босів треба спочатку купити.
        # Куплений бос з'являється лише після 5 мозків у великій лунці.
        self.owned_moon_bosses = {
            "moon_boss1": False,
            "moon_boss2": False
        }
        self.selected_moon_boss = None
        self.moon_boss_brains = 0

        self.moon_boss_respawn_timer = 0.0
        self.moon_boss_spawn_x = self.world_width / 2
        self.moon_boss_pit = {
            "x": self.world_width / 2,
            "y": 145
        }

        # =========================
        # ГРАВЕЦЬ НА МІСЯЦІ
        # =========================
        self.astronaut_suit = False

        # ВАЖЛИВО:
        # У попередній версії цього списку не було,
        # через це виникала помилка:
        # AttributeError: 'Game' object has no attribute 'trees'
        self.trees = [
            (250, 125),
            (900, 125),
            (1600, 125),
            (2350, 125),
            (3150, 125),
            (3950, 125),
            (4750, 125),
            (5550, 125)
        ]

        # =========================
        # SPAWNER TYPES
        # =========================
        self.owned_pile_types = {
            "radioactive": False,
            "fast": False,
            "mutant": False,
            "gold": False
        }

        self.owned_sewer_types = {
            "sewer": False,
            "toxic": False,
            "shadow": False,
            "boss": False
        }

        # Нові місячні типи зомбі.
        # Босси зберігаються окремо в owned_moon_bosses.
        self.owned_moon_types = {
            "lunar": False,
            "crystal": False,
            "alien": False,
            "meteor": False
        }

        self.shop_open = False
        self.shop_popup = None
        self.console_popup = None

        # Режим високої продуктивності: вимикає важкі декоративні ефекти.
        self.performance_mode = False

        self.create_piles()

        Window.bind(
            on_key_down=self.key_down,
            on_key_up=self.key_up
        )

        Clock.schedule_interval(
            self.update,
            1 / 60
        )

        self.draw()

    # ==================================================
    # SPAWNERS
    # ==================================================

    def create_piles(self):
        positions = [
            400, 750, 1100, 1450, 1800, 2200, 2600,
            3000, 3400, 3800, 4200, 4600, 5000, 5400
        ]

        self.piles = []

        for x in positions:
            # Центр Місяця зарезервований тільки під велику лунку боса.
            if self.location == "moon" and abs(x - self.moon_boss_pit["x"]) < 1:
                continue

            self.piles.append({
                "x": x,
                "y": 145,
                "type": "normal",
                "active": False,
                "exists": True,
                "timer": 0
            })

    def random_pile_type(self):
        roll = randint(1, 100)
        current = 0

        if self.location == "normal":
            if self.owned_pile_types["radioactive"]:
                current += 10
                if roll <= current:
                    return "radioactive"
            if self.owned_pile_types["fast"]:
                current += 10
                if roll <= current:
                    return "fast"
            if self.owned_pile_types["mutant"]:
                current += 10
                if roll <= current:
                    return "mutant"
            if self.owned_pile_types["gold"]:
                current += 10
                if roll <= current:
                    return "gold"
            return "normal"

        if self.location == "city":
            if self.owned_sewer_types["toxic"]:
                current += 10
                if roll <= current:
                    return "toxic"
            if self.owned_sewer_types["shadow"]:
                current += 10
                if roll <= current:
                    return "shadow"
            if self.owned_sewer_types["boss"]:
                current += 10
                if roll <= current:
                    return "boss"
            return "sewer"

        # МІСЯЦЬ
        if self.owned_moon_types["lunar"]:
            current += 10
            if roll <= current:
                return "lunar"
        if self.owned_moon_types["crystal"]:
            current += 10
            if roll <= current:
                return "crystal"
        if self.owned_moon_types["alien"]:
            current += 10
            if roll <= current:
                return "alien"
        if self.owned_moon_types["meteor"]:
            current += 10
            if roll <= current:
                return "meteor"

        return "lunar"

    # ==================================================
    # KEYBOARD
    # ==================================================

    def key_down(self, window, key, *args):
        if key == 97:       # A
            self.left = True
            self.player_direction = -1

        elif key == 100:    # D
            self.right = True
            self.player_direction = 1

        elif key == 101:    # E
            self.throw_brain()

        elif key == 32:     # SPACE
            self.shoot()

        elif key == 98:     # B
            self.open_shop()

        elif key == 49:     # 1
            self.change_location("normal")

        elif key == 50:     # 2
            self.change_location("city")

        elif key == 51:     # 3
            self.change_location("moon")

        elif key == 39:     # apostrophe (')
            self.open_console()

        elif key == 27:     # ESC
            if self.console_popup is not None:
                self.console_popup.dismiss()

    def key_up(self, window, key, *args):
        if key == 97:
            self.left = False

        elif key == 100:
            self.right = False

    # ==================================================
    # DEVELOPER CONSOLE
    # ==================================================

    def toggle_performance_mode(self, button=None, result=None):
        self.performance_mode = not self.performance_mode
        if button is not None:
            button.text = (
                "⚡ ВИСОКА ПРОДУКТИВНІСТЬ: УВІМК"
                if self.performance_mode
                else "⚡ ВИСОКА ПРОДУКТИВНІСТЬ: ВИМК"
            )
        if result is not None:
            result.text = (
                "⚡ FPS режим увімкнено — спрощено графіку."
                if self.performance_mode
                else "🎨 Повна графіка увімкнена."
            )
        self.draw()

    def open_console(self):
        if self.console_popup is not None:
            return

        layout = BoxLayout(orientation="vertical", padding=12, spacing=8)
        layout.add_widget(Label(
            text="КОНСОЛЬ РОЗРОБНИКА",
            font_size=22, size_hint_y=None, height=40
        ))
        layout.add_widget(Label(
            text="gt 1 — відкрити Звичайну локацію\ngt 2 — відкрити Місто\ngt 3 — відкрити Місяць",
            font_size=15, size_hint_y=None, height=90
        ))

        command_input = TextInput(
            hint_text="Введи команду, наприклад: gt 3",
            multiline=False, font_size=20, size_hint_y=None, height=48
        )
        layout.add_widget(command_input)

        result = Label(text="", font_size=16, size_hint_y=None, height=35)
        layout.add_widget(result)

        performance_button = Button(
            text=(
                "⚡ ВИСОКА ПРОДУКТИВНІСТЬ: УВІМК"
                if self.performance_mode
                else "⚡ ВИСОКА ПРОДУКТИВНІСТЬ: ВИМК"
            ),
            font_size=15,
            size_hint_y=None,
            height=48
        )
        layout.add_widget(performance_button)
        performance_button.bind(
            on_press=lambda *args: self.toggle_performance_mode(
                performance_button, result
            )
        )

        buttons = BoxLayout(orientation="horizontal", spacing=8, size_hint_y=None, height=48)
        run_button = Button(text="ВИКОНАТИ")
        close_button = Button(text="ЗАКРИТИ")
        buttons.add_widget(run_button)
        buttons.add_widget(close_button)
        layout.add_widget(buttons)

        popup = Popup(
            title="Developer Console", content=layout,
            size_hint=(0.62, 0.55), auto_dismiss=False
        )
        self.console_popup = popup

        def execute_command(*args):
            parts = command_input.text.strip().lower().split()
            if len(parts) != 2 or parts[0] != "gt" or parts[1] not in ("1", "2", "3"):
                result.text = "Помилка: введи gt 1, gt 2 або gt 3"
                return

            number = int(parts[1])
            location = {1: "normal", 2: "city", 3: "moon"}[number]
            self.locations[location]["unlocked"] = True
            result.text = f"✓ Локація {number} відкрита!"

        run_button.bind(on_press=execute_command)
        close_button.bind(on_press=lambda *args: popup.dismiss())

        def on_dismiss(*args):
            if self.console_popup is popup:
                self.console_popup = None

        popup.bind(on_dismiss=on_dismiss)
        popup.open()

    # ==================================================
    # LOCATION
    # ==================================================

    def change_location(self, location):
        if not self.locations[location]["unlocked"]:
            return

        self.location = location
        self.player_x = 500
        self.camera_x = 0

        self.astronaut_suit = (location == "moon")

        self.zombies.clear()
        self.projectiles.clear()
        self.flying_brains.clear()
        self.moon_boss_respawn_timer = 0.0
        self.moon_boss_brains = 0

        self.create_piles()

        # Після зміни локації всі спавнери отримують
        # актуальний тип для цієї локації.
        for pile in self.piles:
            pile["type"] = self.random_pile_type()

        self.draw()

    # ==================================================
    # SHOP
    # ==================================================

    def open_shop(self):
        if self.shop_open:
            return

        self.shop_open = True

        # Головний контейнер магазину.
        # Верх і низ залишаються на місці, а список товарів прокручується.
        main_layout = BoxLayout(
            orientation="vertical",
            padding=10,
            spacing=5
        )

        title = Label(
            text="🛒 МАГАЗИН",
            font_size=27,
            size_hint_y=None,
            height=42
        )
        main_layout.add_widget(title)

        money = Label(
            text=f"💰 Монети: {self.coins}     🧠 Мозки: {self.brains}",
            font_size=17,
            size_hint_y=None,
            height=32
        )
        main_layout.add_widget(money)

        # Усе, що може бути довшим за вікно, кладемо сюди.
        scroll = ScrollView(
            do_scroll_x=False,
            do_scroll_y=True,
            bar_width=12,
            scroll_type=['bars', 'content']
        )

        shop_content = BoxLayout(
            orientation="vertical",
            padding=(0, 4),
            spacing=5,
            size_hint_y=None
        )
        shop_content.bind(
            minimum_height=shop_content.setter("height")
        )

        scroll.add_widget(shop_content)
        main_layout.add_widget(scroll)

        locations_label = Label(
            text="━━ ЛОКАЦІЇ ━━",
            font_size=19,
            size_hint_y=None,
            height=30
        )
        shop_content.add_widget(locations_label)

        city_button = Button(
            text="🏙️ МІСТО\nЦіна відкриття: 1000 монет",
            font_size=15,
            size_hint_y=None,
            height=55
        )

        if self.locations["city"]["unlocked"]:
            city_button.text = "🏙️ МІСТО\n✓ ВІДКРИТО"

        city_button.bind(
            on_press=lambda x: self.unlock_city(popup)
        )
        shop_content.add_widget(city_button)

        moon_button = Button(
            text="🌙 МІСЯЦЬ\nЦіна відкриття: 2500 монет",
            font_size=15,
            size_hint_y=None,
            height=55
        )

        if self.locations["moon"]["unlocked"]:
            moon_button.text = "🌙 МІСЯЦЬ\n✓ ВІДКРИТО"

        moon_button.bind(
            on_press=lambda x: self.unlock_location("moon", popup)
        )
        shop_content.add_widget(moon_button)

        normal_label = Label(
            text="━━ КУПКИ ━━",
            font_size=19,
            size_hint_y=None,
            height=30
        )
        shop_content.add_widget(normal_label)

        self.add_shop_button(
            shop_content,
            "☢️ РАДІОАКТИВНА КУПКА",
            "50 монет | +10% шанс",
            "radioactive",
            50,
            self.owned_pile_types
        )

        self.add_shop_button(
            shop_content,
            "⚡ ШВИДКА КУПКА",
            "100 монет | +10% шанс",
            "fast",
            100,
            self.owned_pile_types
        )

        self.add_shop_button(
            shop_content,
            "🧟 МУТАНТ",
            "150 монет | +10% шанс",
            "mutant",
            150,
            self.owned_pile_types
        )

        self.add_shop_button(
            shop_content,
            "🌟 ЗОЛОТА КУПКА",
            "250 монет | +10% шанс",
            "gold",
            250,
            self.owned_pile_types
        )

        sewer_label = Label(
            text="━━ МІСЬКІ ЛЮКИ ━━",
            font_size=19,
            size_hint_y=None,
            height=30
        )
        shop_content.add_widget(sewer_label)

        self.add_shop_button(
            shop_content,
            "🟢 ТОКСИЧНИЙ ЛЮК",
            "300 монет | +10% шанс",
            "toxic",
            300,
            self.owned_sewer_types
        )

        self.add_shop_button(
            shop_content,
            "🌑 ТІНЬОВИЙ ЛЮК",
            "450 монет | +10% шанс",
            "shadow",
            450,
            self.owned_sewer_types
        )

        self.add_shop_button(
            shop_content,
            "👹 ЛЮК БОСА",
            "700 монет | +10% шанс",
            "boss",
            700,
            self.owned_sewer_types
        )

        moon_label = Label(
            text="━━ МІСЯЧНІ ЗОМБІ ━━",
            font_size=19,
            size_hint_y=None,
            height=30
        )
        shop_content.add_widget(moon_label)

        self.add_shop_button(
            shop_content,
            "🌙 МІСЯЧНИЙ ЗОМБІ",
            "500 монет | +10% шанс",
            "lunar",
            500,
            self.owned_moon_types
        )

        self.add_shop_button(
            shop_content,
            "💎 КРИСТАЛЬНИЙ ЗОМБІ",
            "750 монет | +10% шанс",
            "crystal",
            750,
            self.owned_moon_types
        )

        self.add_shop_button(
            shop_content,
            "👽 ІНОПЛАНЕТНИЙ ЗОМБІ",
            "1000 монет | +10% шанс",
            "alien",
            1000,
            self.owned_moon_types
        )

        self.add_shop_button(
            shop_content,
            "☄️ МЕТЕОРИТНИЙ ЗОМБІ",
            "1400 монет | +10% шанс",
            "meteor",
            1400,
            self.owned_moon_types
        )

        moon_boss_label = Label(
            text="━━ МІСЯЧНІ БОССИ ━━",
            font_size=19,
            size_hint_y=None,
            height=30
        )
        shop_content.add_widget(moon_boss_label)

        # Перший бос завжди доступний для покупки.
        self.add_moon_boss_button(
            shop_content,
            "👹 МІСЯЧНИЙ ВАРД",
            "3000 монет | 15 HP",
            "moon_boss1",
            3000
        )

        # Другий бос відкривається після 2 перемог над першим.
        if self.moon_boss2_unlocked:
            self.add_moon_boss_button(
                shop_content,
                "👑 ВОЛОДАР ЗАТЕМНЕННЯ",
                "6000 монет | 30 HP",
                "moon_boss2",
                6000
            )
        else:
            locked = Label(
                text="🔒 ВОЛОДАР ЗАТЕМНЕННЯ\nВідкриється після 2 перемог над Місячним Вардом",
                font_size=14,
                size_hint_y=None,
                height=54
            )
            shop_content.add_widget(locked)

        # Додаткова порожня область внизу, щоб остання кнопка не прилипала.
        spacer = Widget(size_hint_y=None, height=8)
        shop_content.add_widget(spacer)

        close_button = Button(
            text="ЗАКРИТИ",
            size_hint_y=None,
            height=45
        )
        main_layout.add_widget(close_button)

        popup = Popup(
            title="SHOP",
            content=main_layout,
            size_hint=(0.82, 0.90),
            auto_dismiss=False
        )

        close_button.bind(
            on_press=popup.dismiss
        )

        popup.bind(
            on_dismiss=self.shop_closed
        )

        self.shop_popup = popup
        popup.open()

    def add_moon_boss_button(
        self,
        layout,
        name,
        description,
        boss_type,
        price
    ):
        """Кнопка покупки/вибору місячного боса."""

        owned = self.owned_moon_bosses[boss_type]
        selected = self.selected_moon_boss == boss_type

        if owned:
            if selected:
                text_value = (
                    f"{name}\n"
                    "✓ КУПЛЕНО | ✓ ВИБРАНО"
                )
            else:
                text_value = (
                    f"{name}\n"
                    "✓ КУПЛЕНО | натисни, щоб вибрати"
                )
        else:
            text_value = f"{name}\n{description}"

        button = Button(
            text=text_value,
            font_size=14,
            size_hint_y=None,
            height=58
        )

        button.bind(
            on_press=lambda x: self.buy_or_select_moon_boss(
                boss_type,
                price
            )
        )

        layout.add_widget(button)

    def buy_or_select_moon_boss(self, boss_type, price):
        # Якщо бос уже куплений — просто вибираємо його.
        if self.owned_moon_bosses[boss_type]:
            self.selected_moon_boss = boss_type
            self.refresh_shop()
            return

        # Другий бос не можна купити до його розблокування.
        if boss_type == "moon_boss2" and not self.moon_boss2_unlocked:
            return

        if self.coins < price:
            return

        self.coins -= price
        self.owned_moon_bosses[boss_type] = True
        self.selected_moon_boss = boss_type

        self.refresh_shop()

    def refresh_shop(self):
        """Перемальовує магазин після покупки/вибору."""
        if self.shop_popup is not None:
            self.shop_popup.dismiss()

        self.shop_open = False
        self.shop_popup = None

        Clock.schedule_once(
            lambda dt: self.open_shop(),
            0.05
        )

    def add_shop_button(
        self,
        layout,
        name,
        description,
        item,
        price,
        dictionary
    ):
        button = Button(
            text=f"{name}\n{description}",
            font_size=14,
            size_hint_y=None,
            height=54
        )

        if dictionary[item]:
            button.text = f"{name}\n✓ ВЖЕ КУПЛЕНО"
            button.disabled = True

        button.bind(
            on_press=lambda x: self.buy_item(
                item,
                price,
                dictionary,
                self.shop_popup
            )
        )

        layout.add_widget(button)

    def buy_item(
        self,
        item,
        price,
        dictionary,
        popup
    ):
        if dictionary[item]:
            return

        if self.coins < price:
            return

        self.coins -= price
        dictionary[item] = True

        popup.dismiss()

        Clock.schedule_once(
            lambda dt: self.open_shop(),
            0.1
        )

    def unlock_city(self, popup):
        if self.locations["city"]["unlocked"]:
            popup.dismiss()
            Clock.schedule_once(
                lambda dt: self.change_location("city"),
                0.1
            )
            return

        price = self.locations["city"]["price"]

        if self.coins < price:
            return

        self.coins -= price
        self.locations["city"]["unlocked"] = True

        popup.dismiss()

        Clock.schedule_once(
            lambda dt: self.change_location("city"),
            0.1
        )

    def unlock_location(self, location, popup):
        if self.locations[location]["unlocked"]:
            popup.dismiss()
            Clock.schedule_once(
                lambda dt: self.change_location(location),
                0.1
            )
            return

        price = self.locations[location]["price"]

        if self.coins < price:
            return

        self.coins -= price
        self.locations[location]["unlocked"] = True

        popup.dismiss()

        Clock.schedule_once(
            lambda dt: self.change_location(location),
            0.1
        )

    def shop_closed(self, *args):
        self.shop_open = False
        self.shop_popup = None

    # ==================================================
    # BRAIN
    # ==================================================

    def throw_brain(self):
        if self.brains <= 0:
            return

        # На Місяці мозок спочатку перевіряє ВЕЛИКУ ЛУНКУ.
        # Маленькі лунки ніколи не можуть перекрити її.
        if self.location == "moon":
            boss_alive = any(
                z["type"] in ("moon_boss1", "moon_boss2")
                for z in self.zombies
            )

            if self.selected_moon_boss is not None and not boss_alive:
                pit_distance = abs(self.moon_boss_pit["x"] - self.player_x)

                if pit_distance <= 900:
                    self.brains -= 1
                    self.flying_brains.append({
                        "x": self.player_x,
                        "y": self.player_y + 50,
                        "start_x": self.player_x,
                        "start_y": self.player_y + 50,
                        "target": {
                            "kind": "moon_boss_pit",
                            "x": self.moon_boss_pit["x"],
                            "y": self.moon_boss_pit["y"]
                        },
                        "progress": 0
                    })
                    return

        closest = None
        closest_distance = float("inf")

        for pile in self.piles:
            if not pile["exists"] or pile["active"]:
                continue

            if self.location == "moon" and abs(pile["x"] - self.moon_boss_pit["x"]) < 1:
                continue

            distance = abs(pile["x"] - self.player_x)
            if distance < closest_distance:
                closest_distance = distance
                closest = pile

        if closest is None or closest_distance > 650:
            return

        self.brains -= 1
        self.flying_brains.append({
            "x": self.player_x,
            "y": self.player_y + 50,
            "start_x": self.player_x,
            "start_y": self.player_y + 50,
            "target": closest,
            "progress": 0
        })

    # ==================================================
    # SHOOT
    # ==================================================

    def shoot(self):
        self.projectiles.append({
            "x": self.player_x + self.player_direction * 80,
            "y": self.player_y + 55,
            "direction": self.player_direction,
            "speed": 16
        })

    # ==================================================
    # ZOMBIES
    # ==================================================

    def spawn_zombie(self, pile):
        zombie_type = pile["type"]

        data = {
            "normal": {
                "speed": 2.2, "reward": 10, "brain_reward": 1,
                "hits": 1, "hitbox": 40, "timer": None,
                "dodge": 0.0
            },
            "radioactive": {
                "speed": 2.5, "reward": 30, "brain_reward": 0,
                "hits": 1, "hitbox": 45, "timer": 5,
                "dodge": 0.0
            },
            "fast": {
                "speed": 5.5, "reward": 50, "brain_reward": 2,
                "hits": 1, "hitbox": 40, "timer": None,
                "dodge": 0.0
            },
            "mutant": {
                "speed": 1.2, "reward": 100, "brain_reward": 3,
                "hits": 5, "hitbox": 40, "timer": None,
                "dodge": 0.0
            },
            "gold": {
                "speed": 3.0, "reward": 200, "brain_reward": 5,
                "hits": 2, "hitbox": 40, "timer": None,
                "dodge": 0.0
            },
            "sewer": {
                "speed": 2.8, "reward": 40, "brain_reward": 1,
                "hits": 2, "hitbox": 40, "timer": None,
                "dodge": 0.0
            },
            "toxic": {
                "speed": 3.0, "reward": 80, "brain_reward": 2,
                "hits": 2, "hitbox": 45, "timer": 7,
                "dodge": 0.0
            },
            "shadow": {
                "speed": 4.5, "reward": 150, "brain_reward": 4,
                "hits": 3, "hitbox": 42, "timer": None,
                "dodge": 0.0
            },

            # Новий зомбі, якого викликає бос:
            # швидкий + тіньовий + 40% шанс ухилення.
            "shadow_fast": {
                "speed": 6.5, "reward": 0, "brain_reward": 3,
                "hits": 2, "hitbox": 42, "timer": None,
                "dodge": 0.40
            },
            "shadow_mutant_fast": {
                "speed": 5.8, "reward": 0, "brain_reward": 5,
                "hits": 5, "hitbox": 48, "timer": None,
                "dodge": 0.40
            },

            # Місячні зомбі.
            "lunar": {
                "speed": 3.2, "reward": 70, "brain_reward": 2,
                "hits": 2, "hitbox": 42, "timer": None,
                "dodge": 0.05
            },
            "crystal": {
                "speed": 2.0, "reward": 140, "brain_reward": 4,
                "hits": 5, "hitbox": 45, "timer": None,
                "dodge": 0.15
            },
            "alien": {
                "speed": 5.0, "reward": 220, "brain_reward": 5,
                "hits": 3, "hitbox": 42, "timer": None,
                "dodge": 0.25
            },
            "meteor": {
                "speed": 3.8, "reward": 350, "brain_reward": 7,
                "hits": 7, "hitbox": 48, "timer": None,
                "dodge": 0.20
            },

            # Місячні босси НЕ купуються в магазині.
            "moon_boss1": {
                "speed": 1.5, "reward": 0, "brain_reward": 20,
                "hits": 15, "hitbox": 68, "timer": None,
                "dodge": 0.45
            },
            "moon_boss2": {
                "speed": 2.0, "reward": 0, "brain_reward": 40,
                "hits": 30, "hitbox": 75, "timer": None,
                "dodge": 0.55
            },

            # Міський бос має 60% шанс ухилитися.
            "boss": {
                "speed": 1.0, "reward": 0, "brain_reward": 10,
                "hits": self.boss_max_hp, "hitbox": 60, "timer": None,
                "dodge": 0.60
            }
        }

        info = data.get(zombie_type, data["normal"])

        # Звичайні зомбі з купок з'являються одразу.
        # shadow_fast, яких викликає бос, починають під землею.
        is_minion = zombie_type in ("shadow_fast", "shadow_mutant_fast")

        zombie = {
            "type": zombie_type,
            "x": pile["x"],
            "y": pile["y"] + 5 if not is_minion else 70,
            "ground_y": pile["y"] + 5,
            "speed": info["speed"],
            "direction": randint(0, 1) * 2 - 1,
            "bob": uniform(0, 6),
            "timer": info["timer"],
            "reward": info["reward"],
            "brain_reward": info["brain_reward"],
            "hits": info["hits"],
            "max_hits": info["hits"],
            "hitbox": info["hitbox"],
            "dodge": info["dodge"],
            "emerging": is_minion,
            "emerge_progress": 0.0,
            "summon_timer": self.boss_summon_interval
                if zombie_type == "boss" else None,
            "heal_timer": self.shadow_mutant_heal_interval
                if zombie_type == "shadow_mutant_fast" else None,
            "boss_ref": None
        }

        self.zombies.append(zombie)

    def spawn_moon_boss(self):
        if self.location != "moon":
            return

        # Не створюємо другого боса, якщо один уже живий.
        if any(
            z["type"] in ("moon_boss1", "moon_boss2")
            for z in self.zombies
        ):
            return

        # Бос з'являється тільки якщо він куплений.
        boss_type = self.selected_moon_boss

        if boss_type is None:
            return

        if not self.owned_moon_bosses.get(boss_type, False):
            return

        if boss_type == "moon_boss1":
            hp = 15
            speed = 1.5
            dodge = 0.45
            coin_reward = 1500
            brain_reward = 20
            boss_name = "МІСЯЧНИЙ ВАРД"
        else:
            # Другий бос доступний лише після 2 перемог над першим.
            if not self.moon_boss2_unlocked:
                return

            hp = 30
            speed = 2.0
            dodge = 0.55
            coin_reward = 3000
            brain_reward = 40
            boss_name = "ВОЛОДАР ЗАТЕМНЕННЯ"

        # Бос виходить саме з великої лунки посередині.
        boss = {
            "type": boss_type,
            "x": self.moon_boss_pit["x"],
            "y": 70,
            "ground_y": self.moon_boss_pit["y"],
            "speed": speed,
            "direction": -1,
            "bob": uniform(0, 6),
            "timer": None,
            # За босса даємо І монети, І мозки.
            "reward": coin_reward,
            "brain_reward": brain_reward,
            "hits": hp,
            "max_hits": hp,
            "hitbox": 75 if boss_type == "moon_boss2" else 68,
            "dodge": dodge,
            "emerging": True,
            "emerge_progress": 0.0,
            "summon_timer": 3.0 if boss_type == "moon_boss1" else 2.0,
            "heal_timer": None,
            "boss_ref": None,
            "boss_name": boss_name,
            "boss_from_big_pit": True
        }

        self.zombies.append(boss)

    def spawn_moon_minion(self, boss):
        if boss not in self.zombies:
            return

        current = sum(
            1 for z in self.zombies
            if z["type"] in ("lunar_guardian", "moon_hunter")
        )

        max_minions = 3 if boss["type"] == "moon_boss1" else 5

        if current >= max_minions:
            return

        if boss["type"] == "moon_boss2":
            zombie_type = "moon_hunter"
            hp = 4
            speed = 6.0
            reward = 0
            brains = 8
            dodge = 0.35
        else:
            zombie_type = "lunar_guardian"
            hp = 3
            speed = 4.5
            reward = 0
            brains = 5
            dodge = 0.20

        side = -1 if randint(0, 1) == 0 else 1

        self.zombies.append({
            "type": zombie_type,
            "x": max(
                50,
                min(
                    self.world_width - 50,
                    boss["x"] + side * randint(70, 130)
                )
            ),
            "y": 70,
            "ground_y": 150,
            "speed": speed,
            "direction": side,
            "bob": uniform(0, 6),
            "timer": None,
            "reward": reward,
            "brain_reward": brains,
            "hits": hp,
            "max_hits": hp,
            "hitbox": 45,
            "dodge": dodge,
            "emerging": True,
            "emerge_progress": 0.0,
            "summon_timer": None,
            "heal_timer": None,
            "boss_ref": boss
        })

    def spawn_shadow_minion(self, boss):
        """Бос викликає звичайного швидкого тіньового зомбі або
        рідкісного швидкого мутанта-тіньовика."""

        current_minions = sum(
            1 for z in self.zombies
            if z["type"] in ("shadow_fast", "shadow_mutant_fast")
        )

        if current_minions >= self.boss_summon_max:
            return

        side = -1 if randint(0, 1) == 0 else 1
        x = max(
            50,
            min(
                self.world_width - 50,
                boss["x"] + side * randint(55, 100)
            )
        )

        # 50% шанс на швидкого мутанта-тіньовика.
        if random() < 0.50:
            zombie_type = "shadow_mutant_fast"
            speed = 5.8
            hits = 5
            brain_reward = 5
        else:
            zombie_type = "shadow_fast"
            speed = 6.5
            hits = 2
            brain_reward = 3

        zombie = {
            "type": zombie_type,
            "x": x,
            "y": 70,
            "ground_y": 150,
            "speed": speed,
            "direction": side,
            "bob": uniform(0, 6),
            "timer": None,
            # За цих зомбі монети НЕ даються.
            "reward": 0,
            "brain_reward": brain_reward,
            "hits": hits,
            "max_hits": hits,
            "hitbox": 48 if zombie_type == "shadow_mutant_fast" else 42,
            "dodge": 0.40,
            "emerging": True,
            "emerge_progress": 0.0,
            "summon_timer": None,
            # Лише мутант-тіньовик може лікувати боса.
            "heal_timer": self.shadow_mutant_heal_interval
                if zombie_type == "shadow_mutant_fast" else None,
            "boss_ref": boss
        }

        self.zombies.append(zombie)

    # ==================================================
    # UPDATE
    # ==================================================

    def update(self, dt):

        # PLAYER
        if self.left:
            self.player_x -= self.speed
            self.player_direction = -1

        if self.right:
            self.player_x += self.speed
            self.player_direction = 1

        self.player_x = max(
            50,
            min(self.world_width - 50, self.player_x)
        )

        # CAMERA
        target_camera = self.player_x - Window.width / 2
        max_camera = self.world_width - Window.width

        target_camera = max(
            0,
            min(max_camera, target_camera)
        )

        self.camera_x += (
            target_camera - self.camera_x
        ) * 0.12

        # FLYING BRAINS
        for brain in self.flying_brains[:]:
            brain["progress"] += 0.035

            target = brain["target"]
            t = brain["progress"]

            brain["x"] = (
                brain["start_x"] +
                (target["x"] - brain["start_x"]) * t
            )

            brain["y"] = (
                brain["start_y"] +
                (target["y"] - brain["start_y"]) * t +
                220 * 4 * t * (1 - t)
            )

            if t >= 1:
                # Велика лунка: кожні 5 кинутів мозку викликають
                # купленого та вибраного місячного боса.
                if target.get("kind") == "moon_boss_pit":
                    self.moon_boss_brains += 1

                    if self.moon_boss_brains >= 5:
                        self.moon_boss_brains = 0
                        self.spawn_moon_boss()

                else:
                    target["active"] = True
                    target["timer"] = 1.2

                self.flying_brains.remove(brain)

        # SPAWNERS
        for pile in self.piles:
            if self.location == "moon" and abs(pile["x"] - self.moon_boss_pit["x"]) < 1:
                continue
            if not pile["exists"]:
                continue

            if pile["active"]:
                pile["timer"] -= dt

                if pile["timer"] <= 0:
                    pile["exists"] = False
                    pile["active"] = False

                    self.spawn_zombie(pile)

                    Clock.schedule_once(
                        lambda dt, p=pile: self.respawn_pile(p),
                        5
                    )

        # ZOMBIES
        for zombie in self.zombies[:]:

            # Швидкі тіньові зомбі спочатку вилазять з-під землі.
            if zombie.get("emerging", False):
                zombie["emerge_progress"] += dt * 1.8

                progress = min(
                    1.0,
                    zombie["emerge_progress"]
                )

                zombie["y"] = (
                    zombie["ground_y"] - 80 +
                    80 * progress
                )

                if progress >= 1.0:
                    zombie["emerging"] = False
                    zombie["y"] = zombie["ground_y"]

            else:
                zombie["x"] += (
                    zombie["speed"] *
                    zombie["direction"]
                )

                if zombie["x"] < 30:
                    zombie["x"] = 30
                    zombie["direction"] = 1

                if zombie["x"] > self.world_width - 30:
                    zombie["x"] = self.world_width - 30
                    zombie["direction"] = -1

            # Міські босси викликають тіньових помічників.
            if zombie["type"] == "boss":
                zombie["summon_timer"] -= dt

                if zombie["summon_timer"] <= 0:
                    self.spawn_shadow_minion(zombie)
                    zombie["summon_timer"] = self.boss_summon_interval

            # Місячні босси викликають власних місячних зомбі.
            if zombie["type"] in ("moon_boss1", "moon_boss2"):
                zombie["summon_timer"] -= dt

                if zombie["summon_timer"] <= 0:
                    self.spawn_moon_minion(zombie)
                    zombie["summon_timer"] = (
                        3.0
                        if zombie["type"] == "moon_boss1"
                        else 2.0
                    )

            # Швидкий мутант-тіньовик кожні 2 секунди має 50% шанс
            # відновити босу 1 HP. HP не може бути більшим за максимум.
            if zombie["type"] == "shadow_mutant_fast":
                zombie["heal_timer"] -= dt

                if zombie["heal_timer"] <= 0:
                    boss = zombie.get("boss_ref")

                    if boss in self.zombies and random() < self.shadow_mutant_heal_chance:
                        if boss["hits"] < boss["max_hits"]:
                            boss["hits"] += 1

                    zombie["heal_timer"] = self.shadow_mutant_heal_interval

            if zombie["timer"] is not None:
                zombie["timer"] -= dt

                if zombie["timer"] <= 0:
                    self.player_dead()
                    return

        # PROJECTILES
        for projectile in self.projectiles[:]:

            projectile["x"] += (
                projectile["speed"] *
                projectile["direction"]
            )

            projectile_hit = False

            for zombie in self.zombies[:]:

                distance_x = abs(
                    projectile["x"] - zombie["x"]
                )

                distance_y = abs(
                    projectile["y"] - (zombie["y"] + 40)
                )

                if distance_x < zombie["hitbox"] and distance_y < 60:

                    # Якщо зомбі ухиляється, постріл не завдає шкоди.
                    # Бос: 60%, швидкий тіньовий: 40%.
                    if zombie.get("dodge", 0.0) > 0:
                        if random() < zombie["dodge"]:
                            projectile_hit = True
                            break

                    zombie["hits"] -= 1
                    projectile_hit = True

                    if zombie["hits"] <= 0:
                        self.coins += zombie["reward"]
                        self.brains += zombie["brain_reward"]

                        # Перша місячна битва:
                        # після 2 перемог над першим босом відкривається другий.
                        if zombie["type"] == "moon_boss1":
                            self.moon_boss1_kills += 1

                            if self.moon_boss1_kills >= 2:
                                self.moon_boss2_unlocked = True

                            # Прибираємо його помічників.
                            self.zombies = [
                                z for z in self.zombies
                                if z.get("boss_ref") is not zombie
                            ]

                            self.moon_boss_respawn_timer = 0.0

                        elif zombie["type"] == "moon_boss2":
                            # Другий бос після перемоги просто готується
                            # з'явитися знову через 7 секунд.
                            self.moon_boss_respawn_timer = 0.0

                        if zombie in self.zombies:
                            self.zombies.remove(zombie)

                    break

            if projectile_hit:
                if projectile in self.projectiles:
                    self.projectiles.remove(projectile)

            elif (
                projectile["x"] < 0 or
                projectile["x"] > self.world_width
            ):
                if projectile in self.projectiles:
                    self.projectiles.remove(projectile)

        # Боси більше НЕ респавняться автоматично.
        # Для нового бою потрібно знову кинути 5 мозків у велику лунку.
        if self.moon_boss_respawn_timer > 0:
            self.moon_boss_respawn_timer -= dt

        self.draw()

    # ==================================================
    # RESPAWN
    # ==================================================

    def respawn_pile(self, pile):
        # Якщо гравець уже змінив локацію,
        # все одно створюємо спавнер правильно
        # для поточної локації.
        pile["type"] = self.random_pile_type()
        pile["exists"] = True
        pile["active"] = False
        pile["timer"] = 0

    # ==================================================
    # GAME OVER
    # ==================================================

    def player_dead(self):
        self.left = False
        self.right = False

        for zombie in self.zombies:
            zombie["speed"] = 0

        layout = BoxLayout(
            orientation="vertical",
            padding=20,
            spacing=15
        )

        label = Label(
            text="☠ ТИ ПОМЕР!\n\nЗомбі тебе переміг!",
            font_size=24
        )
        layout.add_widget(label)

        button = Button(
            text="ПОЧАТИ ЗАНОВО",
            size_hint_y=None,
            height=60
        )
        layout.add_widget(button)

        popup = Popup(
            title="GAME OVER",
            content=layout,
            size_hint=(0.55, 0.40),
            auto_dismiss=False
        )

        button.bind(
            on_press=lambda x: self.restart(popup)
        )

        popup.open()

    def restart(self, popup):
        popup.dismiss()

        self.player_x = 500
        self.camera_x = 0
        self.coins = 500
        self.brains = 20

        self.projectiles.clear()
        self.flying_brains.clear()
        self.zombies.clear()
        self.moon_boss_brains = 0

        self.create_piles()

        for pile in self.piles:
            pile["type"] = self.random_pile_type()

        self.draw()

    # ==================================================
    # DRAW
    # ==================================================

    def draw(self):
        self.canvas.clear()

        cam = self.camera_x

        with self.canvas:

            # SKY / BACKGROUND
            if self.location == "normal":
                Color(0.25, 0.65, 0.95)
            else:
                Color(0.06, 0.07, 0.11)

            Rectangle(
                pos=(0, 0),
                size=Window.size
            )

            # =========================
            # NORMAL LOCATION
            # =========================
            if self.location == "normal":

                # Clouds — вимикаються у FPS-режимі.
                if not self.performance_mode:
                    Color(1, 1, 1)
                    for x, y in [
                        (200, 500), (900, 530), (1700, 490),
                        (2500, 540), (3300, 500), (4200, 530)
                    ]:
                        sx = x - cam * 0.25
                        Ellipse(pos=(sx, y), size=(120, 55))

                # Sun
                Color(1, 0.85, 0.15)

                Ellipse(
                    pos=(820, 500),
                    size=(100, 100)
                )

                # Hills — вимикаються у FPS-режимі.
                if not self.performance_mode:
                    Color(0.20, 0.50, 0.25)
                    for x in range(-500, self.world_width + 500, 400):
                        sx = x - cam * 0.5
                        Ellipse(pos=(sx, 80), size=(600, 220))

                # Ground
                Color(0.25, 0.55, 0.18)

                Rectangle(
                    pos=(-cam, 0),
                    size=(self.world_width, 120)
                )

                Color(0.35, 0.75, 0.20)

                Rectangle(
                    pos=(-cam, 115),
                    size=(self.world_width, 25)
                )

                # Trees — вимикаються у FPS-режимі.
                if not self.performance_mode:
                    for x, y in self.trees:
                        sx = x - cam
                        Color(0.35, 0.18, 0.07)
                        Rectangle(pos=(sx - 12, y), size=(24, 100))
                        Color(0.10, 0.45, 0.12)
                        Ellipse(pos=(sx - 55, y + 70), size=(110, 100))

            # =========================
            # CITY / MOON
            # =========================
            elif self.location == "city":

                Color(0.18, 0.18, 0.20)

                Rectangle(
                    pos=(-cam, 0),
                    size=(self.world_width, 140)
                )

                Color(0.38, 0.38, 0.40)

                Rectangle(
                    pos=(-cam, 120),
                    size=(self.world_width, 35)
                )

                buildings = [
                    (100, 320, 230),
                    (500, 400, 280),
                    (950, 300, 200),
                    (1350, 450, 300),
                    (1800, 350, 240),
                    (2300, 420, 300),
                    (2800, 330, 220),
                    (3300, 450, 320),
                    (3900, 350, 250),
                    (4400, 420, 300),
                    (5000, 360, 260)
                ]

                for x, h, w in buildings:

                    sx = x - cam

                    Color(0.22, 0.24, 0.28)

                    Rectangle(
                        pos=(sx, 140),
                        size=(w, h)
                    )

                    if not self.performance_mode:
                        for wx in range(25, int(w) - 20, 55):
                            for wy in range(25, int(h) - 20, 60):
                                Color(1, 0.75, 0.20)
                                Rectangle(
                                    pos=(sx + wx, 140 + wy),
                                    size=(25, 30)
                                )

                # Street lamps — вимикаються у FPS-режимі.
                if not self.performance_mode:
                    for x in range(200, self.world_width, 500):
                        sx = x - cam
                        Color(0.08, 0.08, 0.08)
                        Rectangle(pos=(sx, 140), size=(8, 120))
                        Color(1, 0.8, 0.25)
                        Ellipse(pos=(sx - 10, 250), size=(28, 28))

            # =========================
            # MOON
            # =========================
            elif self.location == "moon":

                Color(0.035, 0.045, 0.09)
                Rectangle(
                    pos=(0, 0),
                    size=Window.size
                )

                # Земля місяця.
                Color(0.28, 0.29, 0.33)
                Rectangle(
                    pos=(-cam, 0),
                    size=(self.world_width, 145)
                )

                Color(0.38, 0.39, 0.43)
                Rectangle(
                    pos=(-cam, 130),
                    size=(self.world_width, 20)
                )

                # Великі кратери — вимикаються у FPS-режимі.
                if not self.performance_mode:
                    for cx, cy, cw, ch in [
                        (350, 105, 180, 45), (1100, 80, 260, 60),
                        (1900, 110, 150, 40), (2750, 75, 230, 55),
                        (3650, 100, 300, 55), (4550, 80, 220, 50),
                        (5350, 105, 280, 60)
                    ]:
                        sx = cx - cam
                        Color(0.18, 0.19, 0.22)
                        Ellipse(
                            pos=(sx - cw / 2, cy - ch / 2),
                            size=(cw, ch)
                        )

                # Гори — вимикаються у FPS-режимі.
                if not self.performance_mode:
                    Color(0.12, 0.13, 0.18)
                    for x in range(-300, self.world_width + 500, 450):
                        sx = x - cam * 0.55
                        Ellipse(pos=(sx, 120), size=(500, 190))

                # Місяць на небі.
                Color(0.82, 0.84, 0.90)
                Ellipse(
                    pos=(790, 445),
                    size=(125, 125)
                )

                # Зірки — вимикаються у FPS-режимі.
                if not self.performance_mode:
                    Color(0.9, 0.92, 1.0)
                    for sx, sy in [
                        (100, 500), (250, 570), (470, 465), (680, 540),
                        (920, 505), (1120, 575), (1380, 490), (1600, 550),
                        (1850, 500), (2100, 570), (2350, 480), (2600, 535),
                        (2900, 590), (3200, 500), (3500, 565), (3850, 480),
                        (4150, 550), (4450, 505), (4750, 570), (5100, 490),
                        (5450, 550), (5750, 505)
                    ]:
                        px_star = sx - cam * 0.15
                        Ellipse(pos=(px_star, sy), size=(4, 4))

            # =========================
            # ВЕЛИКА ЛУНКА ДЛЯ БОСА
            # =========================
            if self.location == "moon":
                bx = self.moon_boss_pit["x"] - cam
                by = self.moon_boss_pit["y"]

                Color(0.07, 0.06, 0.10)
                Ellipse(
                    pos=(bx - 105, by - 35),
                    size=(210, 70)
                )

                Color(0.16, 0.13, 0.20)
                Ellipse(
                    pos=(bx - 85, by - 25),
                    size=(170, 50)
                )

                Color(0.025, 0.02, 0.04)
                Ellipse(
                    pos=(bx - 65, by - 17),
                    size=(130, 35)
                )

                Color(0.55, 0.18, 0.85, 0.7)
                Line(
                    circle=(bx, by, 105),
                    width=2.5
                )

                self.draw_text(
                    f"ВЕЛИКА ЛУНКА: {self.moon_boss_brains}/5 🧠",
                    bx - 100,
                    by + 65
                )

                if self.selected_moon_boss:
                    boss_names = {
                        "moon_boss1": "МІСЯЧНИЙ ВАРД",
                        "moon_boss2": "ВОЛОДАР ЗАТЕМНЕННЯ"
                    }
                    self.draw_text(
                        "ВИБРАНО: " + boss_names[self.selected_moon_boss],
                        bx - 100,
                        by + 90
                    )

            # =========================
            # SPAWNERS
            # =========================
            for pile in self.piles:

                if self.location == "moon" and abs(pile["x"] - self.moon_boss_pit["x"]) < 1:
                    continue

                if not pile["exists"]:
                    continue

                x = pile["x"] - cam
                y = pile["y"]
                pile_type = pile["type"]

                if self.location == "normal":

                    colors = {
                        "normal": (0.30, 0.16, 0.06),
                        "radioactive": (0.15, 0.85, 0.10),
                        "fast": (0.10, 0.50, 1.0),
                        "mutant": (0.65, 0.10, 0.75),
                        "gold": (1.0, 0.70, 0.05)
                    }

                    Color(*colors.get(
                        pile_type,
                        colors["normal"]
                    ))

                    Ellipse(
                        pos=(x - 45, y - 20),
                        size=(90, 45)
                    )

                    top_colors = {
                        "normal": (0.42, 0.23, 0.10),
                        "radioactive": (0.30, 1.0, 0.15),
                        "fast": (0.20, 0.70, 1.0),
                        "mutant": (0.85, 0.20, 1.0),
                        "gold": (1.0, 0.90, 0.15)
                    }

                    Color(*top_colors.get(
                        pile_type,
                        top_colors["normal"]
                    ))

                    Ellipse(
                        pos=(x - 30, y - 5),
                        size=(60, 35)
                    )

                elif self.location == "city":

                    sewer_colors = {
                        "sewer": (0.22, 0.22, 0.23),
                        "toxic": (0.15, 0.75, 0.15),
                        "shadow": (0.08, 0.05, 0.12),
                        "boss": (0.55, 0.10, 0.10)
                    }

                    Color(*sewer_colors.get(
                        pile_type,
                        sewer_colors["sewer"]
                    ))

                    Ellipse(
                        pos=(x - 48, y - 20),
                        size=(96, 42)
                    )

                    Color(0.35, 0.35, 0.37)

                    Ellipse(
                        pos=(x - 40, y - 13),
                        size=(80, 28)
                    )

                    Color(0.12, 0.12, 0.13)

                    for line_y in [
                        y - 5,
                        y + 2,
                        y + 9
                    ]:
                        Line(
                            points=[
                                x - 25,
                                line_y,
                                x + 25,
                                line_y
                            ],
                            width=2
                        )

                elif self.location == "moon":

                    moon_colors = {
                        "lunar": (0.48, 0.48, 0.55),
                        "crystal": (0.20, 0.65, 0.95),
                        "alien": (0.25, 0.85, 0.55),
                        "meteor": (0.70, 0.25, 0.15)
                    }

                    Color(*moon_colors.get(
                        pile_type,
                        moon_colors["lunar"]
                    ))

                    # Кратер замість купки/люка.
                    Ellipse(
                        pos=(x - 50, y - 22),
                        size=(100, 45)
                    )

                    Color(0.22, 0.23, 0.27)
                    Ellipse(
                        pos=(x - 36, y - 10),
                        size=(72, 27)
                    )

                    if pile_type == "crystal":
                        Color(0.35, 0.80, 1.0)
                        for ox in (-18, 0, 18):
                            Rectangle(
                                pos=(x + ox - 4, y + 4),
                                size=(8, 25)
                            )

                    elif pile_type == "alien":
                        Color(0.40, 1.0, 0.50)
                        Ellipse(
                            pos=(x - 12, y - 5),
                            size=(24, 18)
                        )

                    elif pile_type == "meteor":
                        Color(1.0, 0.35, 0.08)
                        Ellipse(
                            pos=(x - 14, y - 9),
                            size=(28, 18)
                        )

            # =========================
            # FLYING BRAINS
            # =========================
            for brain in self.flying_brains:

                x = brain["x"] - cam
                y = brain["y"]

                Color(1, 0.55, 0.70)

                Ellipse(
                    pos=(x - 13, y - 10),
                    size=(26, 20)
                )

                Color(0.8, 0.25, 0.4)

                Line(
                    points=[
                        x - 7, y,
                        x, y + 7,
                        x + 7, y,
                        x, y - 7
                    ],
                    width=2
                )

            # =========================
            # ZOMBIES
            # =========================
            for zombie in self.zombies:

                x = zombie["x"] - cam
                y = zombie["y"]

                bob = sin(
                    Clock.get_time() * 5 +
                    zombie["bob"]
                ) * 3

                zombie_colors = {
                    "normal": (0.35, 0.75, 0.35),
                    "radioactive": (0.20, 1.0, 0.05),
                    "fast": (0.15, 0.55, 1.0),
                    "mutant": (0.70, 0.15, 0.80),
                    "gold": (1.0, 0.70, 0.05),
                    "sewer": (0.35, 0.40, 0.42),
                    "toxic": (0.20, 0.90, 0.20),
                    "shadow": (0.12, 0.08, 0.18),
                    "shadow_fast": (0.05, 0.02, 0.10),
                    "shadow_mutant_fast": (0.30, 0.04, 0.38),
                    "lunar": (0.65, 0.67, 0.75),
                    "crystal": (0.20, 0.75, 1.0),
                    "alien": (0.20, 0.90, 0.45),
                    "meteor": (0.85, 0.28, 0.10),
                    "lunar_guardian": (0.45, 0.55, 0.80),
                    "moon_hunter": (0.18, 0.20, 0.35),
                    "boss": (0.75, 0.08, 0.08),
                    "moon_boss1": (0.55, 0.70, 1.0),
                    "moon_boss2": (0.65, 0.15, 0.95)
                }

                body_color = zombie_colors.get(
                    zombie["type"],
                    (0.4, 0.7, 0.4)
                )

                Color(*body_color)

                if zombie["type"] in ("moon_boss1", "moon_boss2"):

                    # Великі місячні босси.
                    boss_size = 92 if zombie["type"] == "moon_boss1" else 112

                    Color(*body_color)
                    Rectangle(
                        pos=(x - boss_size / 2, y + bob),
                        size=(boss_size, boss_size * 0.82)
                    )

                    Ellipse(
                        pos=(x - boss_size / 2 - 8,
                             y + boss_size * 0.60 + bob),
                        size=(boss_size + 16, boss_size * 0.85)
                    )

                    # Корона/роги другого боса.
                    if zombie["type"] == "moon_boss2":
                        Color(1.0, 0.25, 0.75)
                        Rectangle(
                            pos=(x - 50, y + 120 + bob),
                            size=(100, 10)
                        )
                        for ox in (-35, 0, 35):
                            Ellipse(
                                pos=(x + ox - 8, y + 122 + bob),
                                size=(16, 28)
                            )

                elif zombie["type"] == "lunar_guardian":

                    Rectangle(
                        pos=(x - 22, y + bob),
                        size=(44, 58)
                    )
                    Ellipse(
                        pos=(x - 28, y + 45 + bob),
                        size=(56, 56)
                    )

                elif zombie["type"] == "moon_hunter":

                    Rectangle(
                        pos=(x - 18, y + bob),
                        size=(36, 52)
                    )
                    Ellipse(
                        pos=(x - 24, y + 42 + bob),
                        size=(48, 48)
                    )

                elif zombie["type"] in ("lunar", "crystal", "alien", "meteor"):

                    Rectangle(
                        pos=(x - 19, y + bob),
                        size=(38, 48)
                    )
                    Ellipse(
                        pos=(x - 25, y + 38 + bob),
                        size=(50, 50)
                    )

                elif zombie["type"] == "boss":

                    Rectangle(
                        pos=(x - 38, y + bob),
                        size=(76, 75)
                    )

                    Ellipse(
                        pos=(x - 45, y + 60 + bob),
                        size=(90, 85)
                    )

                    # Тінь навколо боса.
                    Color(0.12, 0.02, 0.16, 0.45)
                    Ellipse(
                        pos=(x - 58, y - 8 + bob),
                        size=(116, 125)
                    )

                    Color(*body_color)

                elif zombie["type"] == "shadow_fast":

                    # Швидкий тіньовий зомбі.
                    Rectangle(
                        pos=(x - 18, y + bob),
                        size=(36, 52)
                    )

                    Ellipse(
                        pos=(x - 25, y + 40 + bob),
                        size=(50, 50)
                    )

                    Color(0.55, 0.05, 0.80)

                    Ellipse(
                        pos=(x - 13, y + 59 + bob),
                        size=(7, 7)
                    )

                    Ellipse(
                        pos=(x + 6, y + 59 + bob),
                        size=(7, 7)
                    )

                    Color(0.10, 0.02, 0.16, 0.55)
                    Ellipse(
                        pos=(x - 30, y - 4 + bob),
                        size=(60, 18)
                    )

                elif zombie["type"] == "shadow_mutant_fast":

                    # Швидкий мутант-тіньовик: більший, сильніший і темно-фіолетовий.
                    Rectangle(
                        pos=(x - 27, y + bob),
                        size=(54, 62)
                    )

                    Ellipse(
                        pos=(x - 34, y + 48 + bob),
                        size=(68, 68)
                    )

                    Color(0.85, 0.08, 0.95)

                    Ellipse(
                        pos=(x - 16, y + 72 + bob),
                        size=(9, 9)
                    )

                    Ellipse(
                        pos=(x + 7, y + 72 + bob),
                        size=(9, 9)
                    )

                    # Великі руки мутанта.
                    Color(0.30, 0.04, 0.38)
                    Line(
                        points=[x - 22, y + 38 + bob, x - 55, y + 10 + bob],
                        width=9
                    )
                    Line(
                        points=[x + 22, y + 38 + bob, x + 55, y + 10 + bob],
                        width=9
                    )

                    # Тінь під ним.
                    Color(0.08, 0.01, 0.12, 0.70)
                    Ellipse(
                        pos=(x - 42, y - 6 + bob),
                        size=(84, 22)
                    )

                elif zombie["type"] == "mutant":

                    Rectangle(
                        pos=(x - 27, y + bob),
                        size=(54, 60)
                    )

                    Ellipse(
                        pos=(x - 32, y + 45 + bob),
                        size=(64, 64)
                    )

                else:

                    Rectangle(
                        pos=(x - 18, y + bob),
                        size=(36, 45)
                    )

                    Ellipse(
                        pos=(x - 23, y + 35 + bob),
                        size=(46, 46)
                    )

                # Eyes
                Color(0, 0, 0)

                Ellipse(
                    pos=(x - 13, y + 58 + bob),
                    size=(7, 7)
                )

                Ellipse(
                    pos=(x + 6, y + 58 + bob),
                    size=(7, 7)
                )

                # Напис під час появи швидкого тіньового зомбі.
                if zombie.get("emerging", False):
                    Color(0.65, 0.15, 0.95, 1)
                    self.draw_text(
                        "З ПІД ЗЕМЛІ!",
                        x - 45,
                        y + 105
                    )

                # Timer
                if zombie["timer"] is not None:

                    Color(1, 0.1, 0.05)

                    timer_text = str(
                        max(
                            0,
                            int(zombie["timer"] + 0.99)
                        )
                    )

                    self.draw_text(
                        timer_text,
                        x - 5,
                        y + 105
                    )

                # Назва місячного боса.
                if zombie["type"] in ("moon_boss1", "moon_boss2"):
                    Color(1, 1, 1)
                    self.draw_text(
                        zombie.get("boss_name", "БОС"),
                        x - 70,
                        y + 155
                    )

                # Hits
                if zombie["max_hits"] > 1:

                    Color(1, 1, 1)

                    self.draw_text(
                        f"{zombie['hits']}",
                        x - 5,
                        y + 105
                    )

                    if zombie["type"] == "shadow_mutant_fast":
                        Color(0.9, 0.2, 1.0)
                        self.draw_text(
                            "ЛІКУЄ БОСА",
                            x - 42,
                            y + 122
                        )

                # Arms
                Color(*body_color)

                Line(
                    points=[
                        x - 15,
                        y + 30 + bob,
                        x - 38,
                        y + 15 + bob
                    ],
                    width=7
                )

                Line(
                    points=[
                        x + 15,
                        y + 30 + bob,
                        x + 38,
                        y + 15 + bob
                    ],
                    width=7
                )

            # =========================
            # PROJECTILES
            # =========================
            for projectile in self.projectiles:

                x = projectile["x"] - cam
                y = projectile["y"]
                direction = projectile["direction"]

                Color(1, 0.85, 0.15)

                Ellipse(
                    pos=(x - 9, y - 6),
                    size=(18, 12)
                )

                Color(1, 0.55, 0.10)

                Line(
                    points=[
                        x - direction * 8,
                        y,
                        x - direction * 25,
                        y
                    ],
                    width=4
                )

            # =========================
            # PLAYER
            # =========================
            px = self.player_x - cam
            py = self.player_y

            if self.location == "moon":
                # Скафандр — декоративний, механіку гравця не змінює.
                Color(0.82, 0.84, 0.88)

                Rectangle(
                    pos=(px - 27, py - 3),
                    size=(54, 64)
                )

                Color(0.72, 0.76, 0.82)

                Ellipse(
                    pos=(px - 29, py + 38),
                    size=(58, 58)
                )

                Color(0.25, 0.45, 0.60)

                Ellipse(
                    pos=(px - 20, py + 51),
                    size=(40, 28)
                )

                # Шланг/рюкзак.
                Color(0.65, 0.68, 0.72)

                Rectangle(
                    pos=(px - 40, py + 5),
                    size=(12, 55)
                )

                Rectangle(
                    pos=(px + 28, py + 5),
                    size=(12, 55)
                )

                # Візор.
                Color(0.08, 0.16, 0.22)

                Rectangle(
                    pos=(px - 20, py + 55),
                    size=(40, 22)
                )

            else:
                Color(0.15, 0.15, 0.18)

                Rectangle(
                    pos=(px - 20, py),
                    size=(40, 55)
                )

                Color(0.95, 0.75, 0.55)

                Ellipse(
                    pos=(px - 25, py + 40),
                    size=(50, 50)
                )

                # Hat
                Color(0.08, 0.08, 0.08)

                Rectangle(
                    pos=(px - 32, py + 82),
                    size=(64, 10)
                )

                Rectangle(
                    pos=(px - 20, py + 88),
                    size=(40, 20)
                )

            # Weapon
            Color(0.12, 0.12, 0.12)

            if self.player_direction == 1:

                Rectangle(
                    pos=(px + 15, py + 30),
                    size=(65, 12)
                )

                Rectangle(
                    pos=(px + 60, py + 25),
                    size=(20, 22)
                )

            else:

                Rectangle(
                    pos=(px - 80, py + 30),
                    size=(65, 12)
                )

                Rectangle(
                    pos=(px - 80, py + 25),
                    size=(20, 22)
                )

            # =========================
            # HUD BACKGROUND
            # =========================
            Color(0, 0, 0, 0.55)

            Rectangle(
                pos=(15, 555),
                size=(760, 80)
            )

        # HUD
        self.draw_text(
            f"Мозки: {self.brains}",
            30,
            605
        )

        self.draw_text(
            f"Монети: {self.coins}",
            30,
            580
        )

        self.draw_text(
            f"Локація: {self.locations[self.location]['name']}",
            150,
            605
        )

        self.draw_text(
            "A/D РУХ   E МОЗОК   SPACE ПОСТРІЛ   B МАГАЗИН",
            150,
            580
        )

        self.draw_text(
            "1: ЗЕМЛЯ    2: МІСТО    3: МІСЯЦЬ",
            150,
            558
        )

        if self.performance_mode:
            self.draw_text(
                "⚡ FPS РЕЖИМ",
                30,
                558
            )

        # Підказка про особливість боса.
        if any(z["type"] == "boss" for z in self.zombies):
            self.draw_text(
                "БОС: 60% | ТІНЬОВІ: 40% | МУТАНТ: ЛІКУЄ БОСА",
                610,
                605
            )

        if self.location == "moon":
            self.draw_text(
                f"1-го місячного боса переможено: {self.moon_boss1_kills}/2",
                610,
                580
            )

            if self.moon_boss2_unlocked:
                self.draw_text(
                    "★ ДРУГИЙ БОС ВІДКРИТО ★",
                    610,
                    558
                )
            else:
                self.draw_text(
                    "Вбий 1-го боса ще раз, щоб відкрити 2-го",
                    610,
                    558
                )

    # ==================================================
    # TEXT
    # ==================================================

    def draw_text(self, text, x, y):
        label = CoreLabel(
            text=text,
            font_size=18,
            color=(1, 1, 1, 1)
        )

        label.refresh()

        # Примусово повертаємо білий колір перед кожним HUD-текстом,
        # щоб колір не успадковувався від попереднього малювання карти.
        self.canvas.add(Color(1, 1, 1, 1))

        self.canvas.add(
            Rectangle(
                texture=label.texture,
                pos=(x, y),
                size=label.texture.size
            )
        )


class ZombieGame(App):

    def open_console_hotkey(self):
        # Відкриваємо консоль у Game.
        # Якщо вона вже відкрита — закриваємо її.
        if getattr(self, "console_popup", None) is not None:
            self.console_popup.dismiss()
            self.console_popup = None
            return

        game = getattr(self, "game", None)
        if game is not None:
            game.open_console()

    def on_key_down(self, window, keycode, scancode, codepoint, modifiers):
        # Kivy передає 5 аргументів після self:
        # window, keycode, scancode, codepoint, modifiers.
        # Апостроф працює на різних розкладках/клавіатурах.
        if keycode in (39, 222) or codepoint in ("'", "’"):
            self.open_console_hotkey()
            return True

        # ESC закриває консоль.
        if keycode == 27 and getattr(self, "console_popup", None) is not None:
            self.console_popup.dismiss()
            return True

        return False

    def _bind_console_keyboard(self):
        Window.bind(on_key_down=self.on_key_down)

    def build(self):
        self._bind_console_keyboard()
        self.game = Game()
        return self.game


if __name__ == "__main__":
    ZombieGame().run()

