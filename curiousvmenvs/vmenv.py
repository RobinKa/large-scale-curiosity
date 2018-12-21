import virtualbox as vb
import gym
from gym import spaces
import gym.utils
import gym.utils.seeding
from time import sleep
from collections import namedtuple
import numpy as np

VirtualBoxVariables = namedtuple("VirtualBoxVariables", "session, virtual_machine, snapshot")

class VirtualBoxEnv(gym.Env):
    def __init__(self):
        self.current_step = 0
        self.max_steps = 1000
        self.vm = None
        self.action_space = spaces.Box(0.0, 1.0, shape=(2,), dtype=np.float32)
        self._seed()

    def _seed(self, seed=None):
        self.np_random, seed = gym.utils.seeding.np_random(seed)
        return [seed]

    def step(self, action):
        # Left click at the position determined by action
        pos_x, pos_y = action
        pos_x = 1 + int(self.screen_width * pos_x)
        pos_y = 1 + int(self.screen_height * pos_y)

        print("Click at", pos_x, pos_y)

        self.vm.session.console.mouse.put_mouse_event_absolute(pos_x, pos_y, 0, 0, 1)
        self.vm.session.console.mouse.put_mouse_event_absolute(pos_x, pos_y, 0, 0, 0)

        # Wait for the action to take effect
        sleep(0.2)

        image = self._get_screenshot()

        self.current_step += 1

        reward = 0

        return image, reward, self.current_step >= self.max_steps, {}

    def _get_screenshot(self):
        image = self.vm.session.console.display.take_screen_shot_to_array(0, self.screen_height, self.screen_width, vb.library.BitmapFormat.rgba)
        image = np.asarray(image).reshape(self.screen_width, self.screen_height, 4)[:, :, :3] / 255.
        return image

    def reset(self):
        machine_name = "Xubuntu 1"
        snapshot_name = "Initial"

        self.current_step = 0

        if self.vm is not None:
            self.vm.session.console.power_down().wait_for_completion(-1)

        sleep(1)

        # Load VM
        virtual_box = vb.VirtualBox()
        virtual_machine = virtual_box.find_machine(machine_name)
        session = vb.Session()

        # Restore snapshot
        snapshot = virtual_machine.find_snapshot(snapshot_name)
        virtual_machine.lock_machine(session, vb.library.LockType(1))
        session.machine.restore_snapshot(snapshot).wait_for_completion(-1)
        session.unlock_machine()

        # Start VM
        progress = virtual_machine.launch_vm_process(session, "gui")
        progress.wait_for_completion(-1)
        sleep(30)

        # Get screen resolution
        self.screen_height, self.screen_width, _, _, _, _ = session.console.display.get_screen_resolution(0)

        self.state_space = spaces.Box(0, 1.0, shape=(self.screen_width, self.screen_height, 3), dtype=np.float32)

        self.vm = VirtualBoxVariables(session=session, virtual_machine=virtual_machine, snapshot=snapshot)

        return self._get_screenshot()

    def _render(self, mode='human', close=False):
        pass