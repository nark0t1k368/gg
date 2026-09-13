from kivymd.app import MDApp
from kivymd.uix.widget import MDWidget
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.screen import MDScreen
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.core.window import Window
from kivy import platform
from kivy.uix.image import Image
from random import randint, random
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivy.core.window import Keyboard
from kivy.properties import NumericProperty
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.fitimage import FitImage


FPS = 60
BULLET_SPEED = dp(10)
SHIP_SPEED = dp(5)
DIR_UP = 1
DIR_DOWN = -1
SPAWN_ENEMY_TIME = 2
HP_DEF = 3
FIRE_RATE_MIN = 0.5
FIRE_RATE_MEDIUM = 2
FIRE_RATE_DEF = FIRE_RATE_MIN

class Shot(MDWidget):
    def __init__(self, direction, owner, **kwargs):
        super().__init__(**kwargs)
        self.direction = direction
        self.owner = owner  # хто стріляв (гравець або ворог)


class Ship(Image):
    hp = NumericProperty()
    max_hp = NumericProperty()

    def __init__(self, direction=DIR_UP, hp=HP_DEF,
                 fire_rate = FIRE_RATE_MEDIUM,**kwargs):
        super().__init__(**kwargs)
        self.direction = direction
        self.hp = self.max_hp = hp
        # Швидкострільність
        self.fire_rate = fire_rate
        self._last_shot = self.fire_rate
        
        self.anim_delay = 0.05
        self._lastAnim = self.anim_delay
        self._currentAnim = 0
    
    def on_kv_post(self, base_widget):
        self.images = [self.source]
        return super().on_kv_post(base_widget)
    
    def moveLeft(self):
        self.pos[0] -= SHIP_SPEED

    def moveRight(self):
        self.pos[0] += SHIP_SPEED

    def shot(self):
        shot = Shot(self.direction, owner=self)
        shot.center_x = self.center_x
        shot.y = (
            self.top
            if self.direction == DIR_UP
            else self.y - shot.height
        )
        self.parent.parent.parent.parent.bullets.append(shot)
        self.parent.add_widget(shot)
        self._last_shot = 0

    def update(self, dt):
        self._last_shot += dt
        self.animation(dt)
        
    def animation(self, dt):
        if len(self.images) > 1:
            if self._lastAnim > self.anim_delay:
                self.source = self.images[self._currentAnim]
                if len(self.images) > self._currentAnim + 1:
                    self._currentAnim += 1
                else:
                    self._currentAnim = 0
                self._lastAnim = 0
            self._lastAnim += dt


class PlayerShip(Ship):
    def __init__(self, **kwargs):
        super().__init__(direction=DIR_UP, fire_rate=FIRE_RATE_MIN, **kwargs)
    
    def on_kv_post(self, base_widget):
        super().on_kv_post(base_widget)
        self.images.extend(['assets/images/rocket_2.png','assets/images/rocket_3.png','assets/images/rocket_4.png'])

    def update(self, dt, keys):
        super().update(dt)
        for key in keys:
            if keys[key]:
                if key == 'left' and self.center_x > 0:
                    self.moveLeft()
                if key == 'right' and self.center_x < Window.width:
                    self.moveRight()
                if key == 'shot':
                    if self._last_shot >= self.fire_rate:
                        self.shot()
                    keys[key] = False


class EnemyShip(Ship):
    def __init__(self, **kwargs):
        super().__init__(direction=DIR_DOWN, **kwargs)
        self.frame = 0

    def update(self, dt):
        super().update(dt)
        self.y -= dp(3)
        # if self.frame % 100 == 0:
        if self._last_shot >= self.fire_rate:
            self.shot()
        # self.frame += 1

# Фон з прокруткою для створення паралакс-ефекту
class MoveBackground(MDFloatLayout):
    def __init__(self, source, speed=dp(1), scale=1, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.speed = speed
        self.add_widget(FitImage(source=source, size_hint_y=scale))
        self.add_widget(FitImage(source=source, size_hint_y=scale,
                                 pos=(0, Window.size[1] * scale)))

    def move(self):
        for img in self.children:
            img.pos[1] -= self.speed
            if img.top <= 0:
                img.pos[1] = img.size[1]


class GameScreen(MDScreen):
    game_time = NumericProperty(0) # Таймер гри
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.eventkeys = {}
        self.ship = None
        self.enemyShips = []
        self.bullets = []
        self.pauseMenu = None
        # Пародійна реклама після смерті
        self.ad_index = 0
        self.ad_dialogs = []
        self.ad_type = "casino"
        self.updateEvent = None
        # Для генерування ворожих кораблів
        self.spawn_delay = SPAWN_ENEMY_TIME
        self.time_last_spawn = 0
        # Додавання на задній план картинок з прокруткою
        self.backBack = MoveBackground(source='assets/images/cosmos.jpg',
                                       speed=0.2)
        self.backFront = MoveBackground(source='assets/images/planets.png',
                                        speed=1, scale=3)
        self.ids.back.add_widget(self.backBack)
        self.ids.back.add_widget(self.backFront)
        # Керування з клавіатури під час тестування з комп'ютера
        Window.bind(on_key_down=self._on_key_down)
        Window.bind(on_key_up=self._on_key_up)

    def on_enter(self, *args):
        self.updateEvent = Clock.schedule_interval(self.update, 1/FPS)
        # головний корабель
        self.ship = self.ids.ship
        self.ship.hp = self.ship.max_hp
        self.game_time = 0
        return super().on_enter(*args)

    def spawn_enemy(self):
        enemy = EnemyShip()  
        enemy.pos = (randint(0, int(Window.width - enemy.width)),
                     Window.height)
        self.enemyShips.append(enemy)
        self.ids.front.add_widget(enemy)

    def update(self, dt):
        self.game_time += dt
        # головний корабель
        self.ship.update(dt, self.eventkeys)
        # вороги - генерування кожні [self.spawn_delay] секунд
        self.time_last_spawn += dt
        if self.time_last_spawn >= self.spawn_delay:
            self.spawn_enemy()
            self.time_last_spawn = 0
        # вороги - рух
        for ship in self.enemyShips:
            ship.update(dt)
            if ship.top < 0:
                self.enemyShips.remove(ship)
                self.ids.front.remove_widget(ship)
            # зіткнення з гравцем 
            if ship.collide_widget(self.ship):
                self.game_over()
        # кулі
        self.manage_bullets()
        # Прокрутка фону
        self.backBack.move()
        self.backFront.move()

    def manage_bullets(self):
        for bullet in self.bullets:
            bullet.y += BULLET_SPEED * bullet.direction
            # Перевірка зіткнення
            self.check_collisions(bullet)
            # Перевірка виходу за рамки вікна
            if bullet.top < 0 or bullet.y > Window.height:
                self.remove_bullet(bullet)

    def check_collisions(self, bullet):
        if bullet.owner == self.ship:
            # перевіряємо влучання у ворога
            for enemy in self.enemyShips:
                if bullet.collide_widget(enemy):
                    '''
                    self.enemyShips.remove(enemy)
                    self.ids.front.remove_widget(enemy)
                    self.remove_bullet(bullet)
                    break
                    '''
                    enemy.hp -= 1
                    if enemy.hp <= 0:
                        self.enemyShips.remove(enemy)
                        self.ids.front.remove_widget(enemy)
                    self.remove_bullet(bullet)
                    break
                    
        else:
            # перевіряємо влучання у гравця
            if bullet.collide_widget(self.ship):
                self.ship.hp -= 1
                if self.ship.hp <= 0:
                    self.game_over()
                self.remove_bullet(bullet)

    def remove_bullet(self, bullet):
        if bullet in self.bullets:
            self.bullets.remove(bullet)
            self.ids.front.remove_widget(bullet)

    def game_over(self):
        if not self.updateEvent:
            return

        self.updateEvent.cancel()
        self.updateEvent = None

        # Безпечно очищаємо ворогів та кулі.
        for enemy in list(self.enemyShips):
            if enemy.parent:
                enemy.parent.remove_widget(enemy)
        self.enemyShips.clear()

        for bullet in list(self.bullets):
            if bullet.parent:
                bullet.parent.remove_widget(bullet)
        self.bullets.clear()

        # Після кожної смерті показуємо 10 пародійних реклам.
        self.ad_index = 0
        # "You an a idiot" дуже рідкісна — приблизно 1%.
        self.ad_type = "idiot" if random() < 0.01 else "casino"
        self.show_next_ad()

    def show_next_ad(self, *args):
        if self.ad_index >= 10:
            self.manager.current = 'game_over'
            return

        self.ad_index += 1

        if self.ad_type == "idiot":
            self.show_idiot_ad()
        else:
            self.show_casino_ad()

    def _ad_close_to_next(self, *args):
        if self.ad_dialogs:
            dialog = self.ad_dialogs.pop()
            try:
                dialog.dismiss()
            except Exception:
                pass
        Clock.schedule_once(self.show_next_ad, 0.08)

    def show_casino_ad(self):
        content = MDBoxLayout(
            orientation="vertical",
            spacing=dp(8),
            padding=dp(12),
            size_hint_y=None,
            height=dp(245),
        )

        content.add_widget(MDLabel(
            text="КАЗИНО ІЛЮХА",
            halign="center",
            font_style="H5",
            size_hint_y=None,
            height=dp(45),
        ))

        content.add_widget(MDLabel(
            text="Колесо удачі\\n\\n"
                 "Крути колесо та перевір свою удачу!",
            halign="center",
            valign="middle",
        ))

        content.add_widget(MDLabel(
            text="Поточний шанс виграшу: 0%",
            halign="center",
            theme_text_color="Secondary",
            size_hint_y=None,
            height=dp(30),
        ))

        dialog = MDDialog(
            title=f"Реклама • {self.ad_index}/10",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(
                    text="КРУТИТИ",
                    theme_text_color="Custom",
                    text_color=app.theme_cls.primary_color,
                    on_release=self._casino_lose,
                ),
                MDFlatButton(
                    text="ЗАКРИТИ",
                    on_release=self._ad_close_to_next,
                ),
            ],
        )
        self.ad_dialogs.append(dialog)
        dialog.open()

    def _casino_lose(self, *args):
        if self.ad_dialogs:
            dialog = self.ad_dialogs.pop()
            try:
                dialog.dismiss()
            except Exception:
                pass
        Clock.schedule_once(self.show_next_ad, 0.08)

    def show_idiot_ad(self):
        content = MDBoxLayout(
            orientation="vertical",
            spacing=dp(12),
            padding=dp(16),
            size_hint_y=None,
            height=dp(280),
        )

        content.add_widget(MDLabel(
            text="YOU AN AN IDIOT",
            halign="center",
            font_style="H4",
            size_hint_y=None,
            height=dp(55),
        ))

        content.add_widget(MDLabel(
            text="Congratulations!\\n\\n"
                 "You've been selected for a very special offer.\\n"
                 "Click the button below to continue.",
            halign="center",
            valign="middle",
        ))

        content.add_widget(MDLabel(
            text="ADVERTISEMENT",
            halign="center",
            theme_text_color="Secondary",
            size_hint_y=None,
            height=dp(28),
        ))

        # Немає кнопки закриття. "SKIP AD" лише створює ще одне вікно.
        dialog = MDDialog(
            title=f"Advertisement • {self.ad_index}/10",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(
                    text="SKIP AD",
                    theme_text_color="Custom",
                    text_color=app.theme_cls.primary_color,
                    on_release=self._duplicate_idiot_ad,
                ),
            ],
            auto_dismiss=False,
        )
        self.ad_dialogs.append(dialog)
        dialog.open()

    def _duplicate_idiot_ad(self, *args):
        self.show_idiot_ad()

    def pressKey(self, key):
        self.eventkeys[key] = True

    def releaseKey(self, key):
        self.eventkeys[key] = False

    def show_menu(self):
        self.updateEvent.cancel()
        if not self.pauseMenu:
            self.pauseMenu = MDDialog(
                title="Game Paused",
                text="Resume the game?",
                on_dismiss=self.resumeGame,
                buttons=[
                    MDFlatButton(
                        text="RESUME",
                        theme_text_color="Custom",
                        text_color=app.theme_cls.primary_color,
                        on_press=self.pauseStop
                    )
                ],
            )
        self.pauseMenu.open()

    def pauseStop(self, *args):
        self.pauseMenu.dismiss()

    def resumeGame(self, *args):
        self.updateEvent = Clock.schedule_interval(self.update, 1/FPS)
    
    # Керування з клавіатури під час тестування з комп'ютера
    def _on_key_down(self, window, keycode, *args, **kwargs):
        key = (
            key
            if (key:=Keyboard.keycode_to_string(window, keycode))!='spacebar'
            else 'shot'
        )
        self.eventkeys[key] = True

    def _on_key_up(self, window, keycode, *args, **kwargs):
        key = (
            key
            if (key:=Keyboard.keycode_to_string(window, keycode))!='spacebar'
            else 'shot'
        )
        self.eventkeys[key] = False


class GameOverScreen(MDScreen):
    pass


class MainScreen(MDScreen):
    pass


class ShooterApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Orange"
        self.theme_cls.accent_palette = "Purple"
        self.sm = MDScreenManager()
        self.sm.add_widget(MainScreen(name='main'))
        self.sm.add_widget(GameScreen(name='game'))
        self.sm.add_widget(GameOverScreen(name='game_over'))
        return self.sm


if platform != 'android':
    Window.size = (450, 700)
    Window.top = 100
    Window.left = 600

app = ShooterApp()
app.run()
