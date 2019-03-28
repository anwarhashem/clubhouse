from eosclubhouse.libquest import Quest
from eosclubhouse.system import Sound


class ActivateTrap(Quest):

    __available_after_completing_quests__ = ['ApplyFob3']

    def __init__(self):
        super().__init__('ActivateTrap', 'saniel')

    def step_begin(self):
        return self.step_success

    def step_success(self):
        self.show_confirm_message('END', confirm_label='End of Episode 3').wait()
        if not self.confirmed_step():
            return

        Sound.play('quests/quest-complete')
        self.complete = True
        self.available = False
        self.complete_current_episode()
        self.stop()
