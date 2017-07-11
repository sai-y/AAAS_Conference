#!/usr/bin/python3
"""
    Personal health improvement example
"""

import fitbit
import datetime
import time
import configparser
from Adafruit_LED_Backpack import SevenSegment

NUM_PLAYERS = 1


class VisualAid(object):
    """
    A wrapper around the Fitbit API and different functions.
    """

    def __init__(
        self, player, consumer_key, consumer_secret,
        access_token, refresh_token, address_1, address_2
    ):
        self.player = player
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.display_1 = self.init_display(address_1)
        self.display_2 = self.init_display(address_2)

        self.client = fitbit.Fitbit(
            self.consumer_key,
            self.consumer_secret,
            access_token=self.access_token,
            refresh_token=self.refresh_token,
            refresh_cb=self.update_tokens)
        self.goal = self.get_goal()

    def init_display(self, address):
        display = SevenSegment.SevenSegment(address=address)
        display.begin()
        return display

    def update_display(self, steps):
        self.display_1.clear()
        self.display_1.print_number_str(str(steps % 10000).zfill(4))
        self.display_1.write_display()

        self.display_2.clear()
        if int(steps / 10000):
            self.display_2.print_number_str(str(steps / 10000))
        self.display_2.write_display()

    def update_tokens(self, token):
        """
        Callback to update token
        """
        config = configparser.ConfigParser()
        config.read(CONFIG_FILE)
        config.set(self.player, "REFRESH_TOKEN", token['refresh_token'])
        config.set(self.player, "ACCESS_TOKEN", token['access_token'])

        with open(CONFIG_FILE, "w") as config_file:
            config.write(config_file)

    def get_steps(self):
        """
            Return the steps logged
        """
        num_steps = 0        
        now = datetime.datetime.now()
        end_time = now.strftime("%H:%M")
        try:
            response = self.client.intraday_time_series(
                'activities/steps',
                detail_level='15min',
                start_time="00:00",
                end_time=end_time
            )
        except Exception as error:
            print(error)
        else:
            str_steps = response['activities-steps'][0]['value']
            try:
                num_steps = int(str_steps)
            except ValueError:
                pass
        return num_steps

    def get_goal(self):
        """
            Determine Daily step goal
        """
        num_steps = 0

        try:
            response = self.client.activities_daily_goal()
        except Exception as error:
            print(error)

        return response['goals']['steps']

    def display_name(self):
        """
        Returns user's name to be displayed on the screen
        """
        display_name = ""
        try:
            response = self.client.user_profile_get()
        except Exception as error:
            print(error)

        display_name = response['user']['displayName']
        return display_name

if __name__ == "__main__":
    scoreboard = list()
    players = list()
    names = list()

    # config is loaded from config file
    # alternatively you may store them as constants in your program
    CONFIG_FILE = '/home/pi/score_board.ini'
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)

    for index in range(NUM_PLAYERS):
        players.append("PLAYER_" + str(index + 1))

    for index in range(NUM_PLAYERS):
        consumer_key = config.get(players[index], "CONSUMER_KEY")
        consumer_secret = config.get(players[index], "CONSUMER_SECRET")
        refresh_token = config.get(players[index], "REFRESH_TOKEN")
        access_token = config.get(players[index], "ACCESS_TOKEN")
        address_1 = config.get(players[index], "DISPLAY_1")
        address_2 = config.get(players[index], "DISPLAY_2")
        scoreboard.append(VisualAid(
            players[index],
            consumer_key,
            consumer_secret,
            access_token=access_token,
            refresh_token=refresh_token,
            address_1=int(address_1, 16),
            address_2=int(address_2, 16)
        ))

        

    current_time = time.time()

    for index in range(NUM_PLAYERS):
        names.append(scoreboard[index].display_name())

    for index in range(NUM_PLAYERS):
        steps = scoreboard[index].get_steps()
        print("{0}:{1}".format(names[index], steps))
        scoreboard[index].update_display(steps)

    while True:
        if (time.time() - current_time) > 900:
            current_time = time.time()
            for index in range(NUM_PLAYERS):
                steps = scoreboard[index].get_steps()
                print("{0}:{1}".format(name[index], steps))
                scoreboard[index].update_display(steps)
