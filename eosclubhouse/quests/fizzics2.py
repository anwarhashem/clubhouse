from eosclubhouse.utils import QS
from eosclubhouse.libquest import Quest
from eosclubhouse.system import Desktop, App


class Fizzics2(Quest):

    TARGET_APP_DBUS_NAME = 'com.endlessm.Fizzics'

    def __init__(self):
        super().__init__('Fizzics 2', 'ricky', QS('FIZZICS2_QUESTION'))
        self._app = App(self.TARGET_APP_DBUS_NAME)
        self._hint0 = False
        self._hint1 = False
        self._initialized = False

    # STEP 0
    def step_first(self, time_in_step):
        if time_in_step == 0:
            if not Desktop.app_is_running(self.TARGET_APP_DBUS_NAME):
                self.show_message(QS('FIZZICS2_LAUNCH'))
                Desktop.show_app_grid()
            else:
                return self.step_alreadyrunning

        if Desktop.app_is_running(self.TARGET_APP_DBUS_NAME):
            return self.step_delay1

        if time_in_step > 20 and not self._hint0:
            self.show_message(QS('FIZZICS2_HINT1'))
            self._hint0 = True

    def step_delay1(self, time_in_step):
        if time_in_step > 2:
            return self.step_set_level

    def step_alreadyrunning(self, time_in_step):
        if time_in_step == 0:
            self.show_question(QS('FIZZICS2_ALREADY_RUNNING'))

        if self.confirmed_step():
            return self.step_set_level

    def step_set_level(self, time_in_step):
        try:
            if not self._initialized:
                self._app.set_object_property('view.JSContext.globalParameters',
                                              'preset', ('i', 12))
                self._initialized = True
        except Exception as ex:
            print(ex)

        if self._initialized:
            return self.step_goal

    def step_goal(self, time_in_step):
        if time_in_step == 0:
            self.show_message(QS('FIZZICS2_GOAL'))

        try:
            if self._app.get_object_property('view.JSContext.globalParameters', 'quest1Success'):
                return self.step_reward
        except Exception as ex:
            print(ex)

        if time_in_step > 60 and not self._hint1:
            self.show_message(QS('FIZZICS2_HINT2'))
            self._hint1 = True

        if not Desktop.app_is_running(self.TARGET_APP_DBUS_NAME):
            return self.step_abort

    # STEP 2
    def step_reward(self, time_in_step):
        if time_in_step == 0:
            self.show_question(QS('FIZZICS2_SUCCESS'))
            self.conf['complete'] = True
            self.available = False
            self.give_item('item.key.hackdex1.1')

        if self.confirmed_step():
            self.stop()

    # STEP Abort
    def step_abort(self, time_in_step):
        if time_in_step == 0:
            self.show_message(QS('FIZZICS2_ABORT'))

        if time_in_step > 5:
            self.stop()
