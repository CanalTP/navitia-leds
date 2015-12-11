# -*- coding: utf-8 -*-
import time
import RPi.GPIO as GPIO
import re
import logging

class Gpio(object):
    def __init__(self, config):
        self.config = config
        self.interval = time.time()
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        self.initialize()

    def initialize(self):
	print "init"
        for key, value in self.config.regions.items():
            GPIO.setup(value["channel"], GPIO.OUT)
            self.config.regions[key]["pi"] = GPIO.PWM(value["channel"], 100)
            self.config.regions[key]["duty"] = 0
            value["pi"].start(0)
	    value["pi"].ChangeDutyCycle(0)

    def finalize(self):
        for key, value in self.config.regions.items():
            value["pi"].stop()
        GPIO.cleanup()

    def get_region_is_journeys(self, message):
        # Il faut parser le message pour savoir si une recherche d'iti et récupérer le coverage et par la suite la région
        mapped_region_ids = []

        if message.api == "v1.journeys":
            # coverages is a list
            region_ids = [c.region_id for c in message.coverages]
            for key, value in self.config.regions.items():
                for region_id in region_ids:
                    if region_id in value["coverages"]:
                         mapped_region_ids.append(key)

        return mapped_region_ids

    def reinitialize(self):
        # self.config.gpio["delay"] est en minute
        if (time.time() - self.interval) > (self.config.gpio["delay"]*10):
            for key, value in self.config.regions.items():
                value["duty"] = 0
                value["pi"].ChangeDutyCycle(value["duty"])
            self.interval = time.time()

    def manage_lights(self, message):
        self.reinitialize()
        # region_ids is list
        region_ids = self.get_region_is_journeys(message)

        for region_id in region_ids:
            if region_id in self.config.regions:
                self.config.regions[region_id]["duty"] = self.config.regions[region_id]["duty"] + 1
                duty = self.config.regions[region_id]["duty"] * 100 / self.config.regions[region_id]["max_hits"]
                if duty > 100:
                    duty = 100
                logging.getLogger(__name__).info(self.config.regions[region_id]["duty"])
                self.config.regions[region_id]["pi"].ChangeDutyCycle(duty)


