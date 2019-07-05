"""
FeedingFred - main.py
"""

from random import random, randint
from functools import partial
from datetime import datetime

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.gridlayout import GridLayout
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.graphics import Color
from kivy.graphics.vertex_instructions import *
from kivy.properties import BooleanProperty, StringProperty, NumericProperty, ListProperty, ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.core.audio import SoundLoader

from kivy.lang import Builder
from kivy.logger import Logger

from food import Food, Junk, FoodScoreFeedback
from fish import Fish
from ship import Ship


class FredLifeIntro(Image):
    help_on = BooleanProperty(False)

    def __init__(self, **kwargs):
        super(FredLifeIntro, self).__init__(source="images/welcome.png", **kwargs)
        self.help_btn.bind(on_press=self.toggle_help)
        self.defaults = {"help_btn": self.help_btn.center, "go_btn": self.go_btn.center}

    def toggle_help(self, *largs):
        self.help_on = not self.help_on
        self.source = "images/howto.png" if self.help_on else "images/welcome.png"

        self.go_btn.center = (600, 110)
        self.go2_btn.center = (400, 110)
        self.go3_btn.center = (200, 110)


class FredLifeScore(Popup):
    def __init__(self):
        super(FredLifeScore, self).__init__()
        self.pos = (Window.width / 2 - self.width / 2, Window.height / 2 - self.height / 2)
        self.box_layout.pos = self.pos
        self.box_layout.size = self.size

class FredLifeGame(Widget):
    ships = ListProperty([])
    fish = ObjectProperty(None)
    start_time = ObjectProperty(None)

    def __init__(self, *args, **kwargs):
        self.size = (Window.width, Window.height)

        super(FredLifeGame, self).__init__(*args, **kwargs)

        self.victory_screen = FredLifeScore()
        self.manufacture_ships(3)

        self.fish = Fish(
            box=[self.game_area.x, self.game_area.y + 65, self.game_area.width, self.game_area.height - 175])
        self.fish.bind(pos=lambda instance, value: self.check_for_smthing_to_eat(value))
        self.fish.bind(calories=self.update_calories_bar)
        self.fish.bind(on_death=self.the_end)

    def play(self, *largs):
        for ship in self.ships:
            self.drop_ship_onto_sea(ship)

        self.game_area.add_widget(self.fish, index=1)
        self.fish.active = True

        Clock.schedule_interval(self.drop_food, 4)
        Clock.schedule_interval(self.sail_ships, 4)
        Clock.schedule_interval(self.check_for_smthing_to_eat, 0.2)

        self.start_time = datetime.now()

    def pause(self):
        Clock.unschedule(self.drop_food)
        Clock.unschedule(self.sail_ships)
        Clock.unschedule(self.check_for_smthing_to_eat)

    def the_end(self, instance):
        self.pause()
        self.victory_screen.calories_score.text = str(self.fish.total_calories)
        self.victory_screen.junk_score.text = str(self.fish.junk_swallowed)
        self.victory_screen.open()

    def manufacture_ships(self, count=1):

        for n in range(0, count):
            ship = Ship(horison=self.horison)
            self.ships.append(ship)

        self.ships[0].bind(on_start_sailing=lambda instance: Clock.schedule_interval(self.drop_junk, 1))
        self.ships[0].bind(on_stop_sailing=lambda instance: Clock.unschedule(self.drop_junk))

    def drop_ship_onto_sea(self, ship):
        try:
            if not ship:
                ship = self.ships.pop()
            self.game_area.add_widget(ship)

            ship.center_x = randint(0, Window.width - ship.width / 4)
            ship.y = self.game_area.height
            ship.active = True
        except IndexError:
            Logger.debug("No ships left in dock.")

    def check_for_smthing_to_eat(self, dt):
        """Collision detection"""
        to_eat = []
        for stuff in self.game_area.children:
            if stuff.collide_widget(self.fish):
                if isinstance(stuff, Food) or isinstance(stuff, Junk):
                    to_eat.append(stuff)

        for shit in to_eat:
            self.game_area.remove_widget(shit)
            self.game_area.add_widget(FoodScoreFeedback(calories=shit.calories, center=shit.center))

            self.fish.eat(shit)

    def drop_food(self, td):
        """Periodically drop food from the ships"""

        for ship in self.ships:
            food = Food(what="bottle", lvl=self.fish.obese_lvl, x=ship.center_x + randint(-50, 50),
                        y=ship.y + randint(-5, 5))

            def really_drop_food(food, td):
                self.game_area.add_widget(food)
                food.active = True

            Clock.schedule_once(partial(really_drop_food, food), random() * 2)

    def drop_junk(self, *args):
        """Periodically drop junk from the ships"""

        for ship in self.ships:
            junk = Junk(lvl=self.fish.obese_lvl, x=ship.center_x + randint(-50, 50), y=ship.y + randint(-5, 5))
            self.game_area.add_widget(junk)
            junk.active = True

    def sail_ships(self, timer):
        for ship in self.ships:
            ship.sail()

    def update_calories_bar(self, instance, new_value):
        self.calories_bar.value = new_value


class FeedingFred(App):
    def __init__(self, *args, **kwargs):
        super(FeedingFred, self).__init__(*args, **kwargs)

    def build_config(self, config):
        config.setdefaults('aquarium', {"waterline": 200})
        # config.setdefaults('graphics', {"width":1280, "height": 726})

    def build(self):
        Builder.load_file("home.kv")
        self.intro = FredLifeIntro()
        self.intro.go_btn.bind(on_release=self._beginner_start)
        self.intro.go2_btn.bind(on_release=self._normal_start)
        self.intro.go3_btn.bind(on_release=self._expert_start)
        return self.intro

    def begin_game(self, *largs, **kwargs):
        Builder.load_file("main.kv")
        self.root = self.fishlife = FredLifeGame()
        self.fishlife.victory_screen.restart_btn.bind(on_press=self.restart_game)

        try:
            Window.remove_widget(self.intro)
        except:
            pass

        Window.add_widget(self.root)

        # Fade in
        Window.remove_widget(self.fader)
        Window.add_widget(self.fader)
        anim = Animation(alpha=0.0, d=0.8)
        anim.bind(on_complete=lambda instance, value: Window.remove_widget(self.fader))
        anim.start(self.fader)

        # Timing game start with fade in
        if not kwargs.get("restart", False):
            Clock.schedule_once(self.root.play, 0.85)
        else:
            self.root.play()

    def restart_game(self, *args):
        self.fishlife.victory_screen.restart_btn.unbind(on_press=self.restart_game)
        Window.remove_widget(self.fishlife)
        Builder.unload_file("main.kv")
        self.begin_game(restart=True)

    def _beginner_start(self, *args):
        self.fader = ScreenFader(size=Window.size)
        Window.add_widget(self.fader)
        anim = Animation(alpha=1.0, d=0.6)
        anim.bind(on_complete=self.begin_game)
        anim.start(self.fader)

    def _normal_start(self, *args):
        self.fader = ScreenFader(size=Window.size)
        Window.add_widget(self.fader)
        anim = Animation(alpha=1.0, d=0.6)
        anim.bind(on_complete=self.begin_game)
        anim.start(self.fader)

    def _expert_start(self, *args):
        self.fader = ScreenFader(size=Window.size)
        Window.add_widget(self.fader)
        anim = Animation(alpha=1.0, d=0.6)
        anim.bind(on_complete=self.begin_game)
        anim.start(self.fader)

class ScreenFader(Widget):
    alpha = NumericProperty(0.0)

    def __init__(self, alpha=0, **kwargs):
        super(ScreenFader, self).__init__(**kwargs)
        self.bind(alpha=self.on_alpha)
        self.alpha = alpha

    def on_alpha(self, instance, value):
        self.canvas.clear()
        with self.canvas:
            Color(0, 0, 0, value)
            Rectangle(pos=self.pos, size=self.size)		

if __name__ == '__main__':
    FeedingFred().run()
	
"""   
    sound = SoundLoader.load('images/bgm.mp3')
    sound.loop = True
    sound.play()  
"""
