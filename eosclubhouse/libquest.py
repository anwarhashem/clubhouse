# Copyright (C) 2018 Endless Mobile, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Authors:
#       Joaquim Rocha <jrocha@endlessm.com>
#

import pkgutil
import sys
import time

from eosclubhouse import logger
from eosclubhouse.system import GameStateService
from gi.repository import GObject, GLib


class Registry:

    _quests = []
    _quest_sets = []

    @staticmethod
    def load(quest_folder):
        sys.path.append(quest_folder)

        for _unused, modname, _unused in pkgutil.walk_packages([quest_folder]):
            __import__(modname)

        del sys.path[sys.path.index(quest_folder)]

    @classmethod
    def register_quest_set(class_, quest_set):
        if not issubclass(quest_set, QuestSet):
            raise TypeError('{} is not a of type {}'.format(quest_set, QuestSet))
        class_._quest_sets.append(quest_set())
        logger.info('QuestSet registered: %s', quest_set)

    @classmethod
    def get_quests(class_):
        return class_._quests

    @classmethod
    def get_quest_sets(class_):
        return class_._quest_sets

    @classmethod
    def get_quest_set_by_name(class_, name):
        for quest_set in class_.get_quest_sets():
            if quest_set.get_id() == name:
                return quest_set

        return None

    @classmethod
    def get_quest_by_name(class_, name):
        quest_set_name = None
        name_split = name.split('.', 1)

        if len(name_split) > 1:
            quest_set_name, quest_name = name_split
        else:
            quest_name = name

        for quest_set in class_.get_quest_sets():
            if quest_set_name is not None and quest_set_name != quest_set.get_id():
                continue

            for quest in quest_set.get_quests():
                if quest.get_id() == quest_name:
                    return quest

        return None


class Quest(GObject.GObject):

    __gsignals__ = {
        'message': (
            GObject.SignalFlags.RUN_FIRST, None, (str, GObject.TYPE_PYOBJECT, str, str)
        ),
        'item-given': (
            GObject.SignalFlags.RUN_FIRST, None, (str, str)
        ),
    }

    available = GObject.Property(type=bool, default=True)
    skippable = GObject.Property(type=bool, default=False)

    def __init__(self, name, main_character_id, initial_msg):
        super().__init__()
        self._name = name
        self._initial_msg = initial_msg
        self._characters = {}
        self._main_character_id = main_character_id
        self._cancellable = None

        self.gss = GameStateService()

        self.conf = {}
        self.load_conf()

        self.key_event = False
        self._debug_skip = False

        self._confirmed_step = False

    def start(self):
        '''Start the quest's main function

        This method runs the quest as a step-by-step approach, so a method called 'step_first'
        needs to be defined in any Quest subclasses that want to follow this approach.

        As an alternative, subclasses can override this very method in order to follow any
        approach needed.
        '''

        time_in_step = 0
        step_func = self.step_first

        while not self.is_cancelled():
            new_func = step_func(time_in_step)
            if new_func is None:
                time.sleep(1)
                time_in_step += 1
            else:
                step_func = new_func
                time_in_step = 0

    def step_first(self, time_in_step):
        raise NotImplementedError

    def _confirm_step(self):
        self._confirmed_step = True

    def confirmed_step(self):
        confirmed = self._confirmed_step
        self._confirmed_step = False
        return confirmed

    def stop(self):
        if not self.is_cancelled() and self._cancellable is not None:
            self._cancellable.cancel()

    def get_main_character(self):
        return self._main_character_id

    def show_message(self, txt, character_id=None, mood=None, choices=[], use_confirm=False):
        possible_answers = [(text, callback) for text, callback in choices]

        if use_confirm:
            possible_answers = [('>', self._confirm_step)] + possible_answers

        self._emit_signal('message', txt, possible_answers,
                          character_id or self._main_character_id, mood)

    def show_question(self, txt, character_id=None, mood=None):
        self.show_message(txt, character_id=character_id, mood=mood, choices=[],
                          use_confirm=True)

    def get_initial_message(self):
        return self._initial_msg

    def give_item(self, item_name, notification_text=None):
        variant = GLib.Variant('a{sb}', {'used': False})
        self.gss.set(item_name, variant)
        self._emit_signal('item-given', item_name, notification_text)

    # @todo: Obsolete. Delete when quests no longer use it.
    def set_keyboard_request(self, wants_keyboard_events):
        pass

    def on_key_event(self, event):
        self.key_event = True

    def debug_skip(self):
        skip = self.key_event or self._debug_skip
        self.key_event = None
        self._debug_skip = False
        return skip

    def set_debug_skip(self, debug_skip):
        self._debug_skip = debug_skip

    def __repr__(self):
        return self._name

    def _emit_signal(self, signal_name, *args):
        # The quest runs in a separate thread, but we need to emit the
        # signal from the main one
        GLib.idle_add(self.emit, signal_name, *args)

    def set_cancellable(self, cancellable):
        self._cancellable = cancellable

    def is_cancelled(self):
        return self._cancellable is not None and self._cancellable.is_cancelled()

    @classmethod
    def _get_conf_key(class_):
        return class_._get_quest_conf_prefix() + class_.__name__

    @staticmethod
    def _get_quest_conf_prefix():
        return 'quest.'

    def load_conf(self):
        self.conf['complete'] = self.is_named_quest_complete(self.__class__.__name__)

    def save_conf(self):
        key = self._get_conf_key()
        variant = GLib.Variant('a{sb}', {'complete': self.conf['complete']})
        self.gss.set(key, variant)

    def set_conf(self, key, value):
        self.conf[key] = value

    def get_conf(self, key):
        return self.conf.get(key)

    def is_named_quest_complete(self, class_name):
        key = self._get_quest_conf_prefix() + class_name
        data = self.gss.get(key)
        return data is not None and data['complete']

    @classmethod
    def get_id(class_):
        return class_.__name__


class QuestSet(GObject.GObject):

    __quests__ = []
    # @todo: Default character; should be set to None in the future
    __character_id__ = 'aggretsuko'
    __position__ = (0, 0)
    __empty_message__ = 'Nothing to see here!'

    __gsignals__ = {
        'nudge': (
            GObject.SignalFlags.RUN_FIRST, None, ()
        ),
    }

    visible = GObject.Property(type=bool, default=True)

    def __init__(self):
        super().__init__()
        self._position = self.__position__
        for quest in self.get_quests():
            quest.connect('notify',
                          lambda quest, param: self.on_quest_properties_changed(quest, param.name))

    @classmethod
    def get_character(class_):
        return class_.__character_id__

    @classmethod
    def get_quests(class_):
        return class_.__quests__

    @classmethod
    def get_id(class_):
        return class_.__name__

    def get_next_quest(self):
        for quest in self.get_quests():
            if not quest.conf['complete']:
                if quest.available:
                    logger.info("Quest available: %s", quest)
                    return quest
                if not quest.skippable:
                    break
        return None

    def get_empty_message(self):
        return self.__empty_message__

    def get_position(self):
        return self._position

    def nudge(self):
        self.emit('nudge')

    def on_quest_properties_changed(self, quest, prop_name):
        logger.debug('Quest "%s" property changed: %s', quest, prop_name)
        if prop_name == 'available' and quest.get_property(prop_name):
            logger.info('Turning QuestSet "%s" visible from quest %s', self, quest)
            self.visible = True
            self.nudge()

    def is_active(self):
        return self.visible and self.get_next_quest() is not None