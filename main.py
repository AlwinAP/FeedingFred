"""
@Project: Feeding Fred
@Author: Alwin Prabu
"""
#Dependencies:
#   users.txt  - user database
#   score.txt  - score database
#   leaguetable.txt - league database
#   rank.txt - ranks database
#   FeedingFred.kv - Kivy UI file
#   comic.ttf  - fonts

# Python imports required 
from kivy.app import App
from kivy.base import runTouchApp
from kivy.config import Config
from kivy.core.text import Label 
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition

# More imports
from random import random, randint
from functools import partial
from datetime import datetime
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

# Screen size configuration 
Config.set('graphics', 'width', '852')
Config.set('graphics', 'height', '480')
Config.write()

# FF classes
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


class GameScreen(Screen):
    def __init__(self, *args, **kwargs):
        super(GameScreen, self).__init__(*args, **kwargs)

    def build_config(self, config):
        config.setdefaults('aquarium', {"waterline": 200})
        # config.setdefaults('graphics', {"width":1280, "height": 726})

    def build(self):
        Builder.load_file("home.kv")
        self.intro = FredLifeIntro()
        self.intro.go_btn.bind(on_release=self._beginner_start)
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

# End FF classes


# Add score to the score.txt file
def add_score(self, flag, *args):
    file = open("score.txt","a")  
    if flag == "1" :
        file.write("1+")
    file.close()  
    return 

# First screen class with check login function
class FirstScreen(Screen):
    text = ObjectProperty("afdas")
    def __init__(self, **kwargs):
        super(FirstScreen, self).__init__(**kwargs) 
  
    def check_login(self, un, pw, *args):
        auth = "0"
        file = open('users.txt','r')
        name_in = un
        pass_in = pw
        for line in file: 
            if line != "\n" or "":                  
                entry = line.split(',')         
                name = entry[0]                 
                pass_raw = entry[1].split('\n') 
                password = pass_raw[0]          
                if name == name_in:
                    if pass_in == password:
                        auth = "1"          
        file.close()
        self.text = auth
        return self.text

# Registration screen class with create user account function
class RegistrationScreen(Screen):
    text = ObjectProperty("afdas")
    def __init__(self, **kwargs):
        super(RegistrationScreen, self).__init__(**kwargs) 
  
    def create_account(self, un, pw, *args):
        prefix = "\n"
        if un == "" or pw == "":
            self.text = "0"
        else:
            file = open('users.txt','a')
            file.write(prefix + un +','+ pw + '\n')           
            file.close()
            self.text = "1"
        return self.text

# Error Screen class - no functions needed (auto generated by Kivy UI definitions)
class ErrorScreen(Screen):
    pass

# Error Level class - no functions needed (auto generated by Kivy UI definitions)
class LevelScreen(Screen):
    pass	

# Feedback Screen class - with 5 function	
class FeedbackScreen(Screen):   
    pass

# Score Screen class - with 4 function	
class ScoreScreen(Screen):
    text = ObjectProperty("afdas")
    def __init__(self, **kwargs):
        super(ScoreScreen, self).__init__(**kwargs) 

    def get_score(self, qn, *args):
	    file = open("score.txt","r")  
	    scorelist= file.readline()
	    score = scorelist.strip()
	    score = scorelist.split('+')
	    score = score[ : -1]
	    myscore = 0
	    for i in range(len(score)):
		    myscore = myscore + int(score[i])
	    file.close()             
	    return str(int(int(myscore)/2))

    def write_score(self, un, scr, *args):
        prefix = "\n"
        if un == "" or scr == "":
            self.text = "0"            
        else:
            file = open('leaguetable.txt','a')             
            file.write(prefix + un +','+ scr + '\n')           
            file.close()
            self.text = "1"
        return self.text

    def reset_score(self, *args):
	    open("score.txt","w").close()          
	    return 

# Score Screen class - with create and get rank functions	
class RankScreen(Screen):
    text = ObjectProperty("afdas")
    def __init__(self, **kwargs):
        super(RankScreen, self).__init__(**kwargs) 	
    
    def create_rank(self, *args):
        out = open('leaguetable.txt','r')
        scores = []
        for line in out:
            if line != "\n":
                split = line.split(',')
                split2 = split[1].split('\n')
                scores.append((split[0],int(split2[0])))
        sort_scores = sorted(scores,reverse = True, key= lambda l: (float(l[1])))
        out.close()
        top5 = 0
        ranks = ""
        if len(sort_scores) >= 5:
            while top5 < 5:
                nstring = str(top5+1)+'.  Name: '+ sort_scores[top5][0] + ',   Score: ' +  str(sort_scores[top5][1]) + '|'
                ranks = ranks + nstring
                top5+=1
        else:
            for score in range(len(sort_scores)):
                nstring = str(top5+1)+'.  Name: '+sort_scores[top5][0] + ',   Score: '+ str(sort_scores[top5][1]) + '|'
                ranks = ranks + nstring
                top5+=1
        file = open('ranks.txt','w')  
        file.write(ranks)
        file.close() 
        self.text = "done"       
        return self.text     
    
    def get_rank(self, ro, *args):
        out = open('ranks.txt','r')
        for line in out:
            if line != "\n":
                split = line.split('|')
                splito = split[ro-1].split('\n')
                rankout = str(splito)
                self.text = rankout[2:-2]
        out.close()
        return self.text  

# Kivy Screen manager that manages all screens and has global variables
class ScreenManagement(ScreenManager):
    UNAME = StringProperty('')
    UPASS = StringProperty('Eask92')
    ULEVEL = StringProperty('0')
    UINPUT = StringProperty('0')
    UCHOICE = StringProperty('1')
    QNUM = StringProperty('1')
    SCORE = StringProperty('0')
    FULLINPUT = StringProperty('0')

# Main game starter class with build UI from .kv file
class FeedingFredApp(App):
    def build(self):
        return Builder.load_file("FeedingFred.kv")
		
if __name__ == "__main__":
	FeedingFredApp().run()
