import virtualbox as vb
import gym
from gym import spaces
import gym.utils
import gym.utils.seeding
from time import sleep
from collections import namedtuple
import numpy as np
from multiprocessing import Array

VirtualBoxVariables = namedtuple("VirtualBoxVariables", "session, virtual_machine, snapshot, machine_name")

virtual_box = vb.VirtualBox()

class VirtualBoxEnv(gym.Env):
    def __init__(self):
        self.machine_name = "Xubuntu 1"
        self.current_step = 0
        self.max_steps = 1500
        self.screenshot_width = 84
        self.screenshot_height = 84
        self.vm = None
        self.action_space = spaces.Box(0.0, 1.0, shape=(3,), dtype=np.float32)
        self.observation_space = spaces.Box(0, 255, shape=(self.screenshot_width, self.screenshot_height, 3), dtype=np.uint8)
        self._seed()

    def _seed(self, seed=None):
        print("Seed")
        self.np_random, seed = gym.utils.seeding.np_random(seed)
        return [seed]

    def step(self, action):
        print("Step", self.current_step, self.max_steps)
        # Left click at the position determined by action
        pos_x, pos_y, click_action = action
        pos_x = 1 + int(self.screen_width * pos_x)
        pos_y = 1 + int(self.screen_height * pos_y)

        print("Click at", pos_x, pos_y, click_action)

        if click_action < 0.5:
            self.vm.session.console.mouse.put_mouse_event_absolute(pos_x, pos_y, 0, 0, 1)
            self.vm.session.console.mouse.put_mouse_event_absolute(pos_x, pos_y, 0, 0, 0)
        elif click_action < 0.8:
            self.vm.session.console.mouse.put_mouse_event_absolute(pos_x, pos_y, 0, 0, 1)
            self.vm.session.console.mouse.put_mouse_event_absolute(pos_x, pos_y, 0, 0, 0)
            self.vm.session.console.mouse.put_mouse_event_absolute(pos_x, pos_y, 0, 0, 1)
            self.vm.session.console.mouse.put_mouse_event_absolute(pos_x, pos_y, 0, 0, 0)
        else:
            self.vm.session.console.mouse.put_mouse_event_absolute(pos_x, pos_y, 0, 0, 2)
            self.vm.session.console.mouse.put_mouse_event_absolute(pos_x, pos_y, 0, 0, 0)


        # Wait for the action to take effect
        sleep(0.1)

        image = self._get_screenshot()

        self.current_step += 1

        reward = 0

        return image, reward, self.current_step >= self.max_steps, {}

    def _get_screenshot(self):
        image = self.vm.session.console.display.take_screen_shot_to_array(0, self.screenshot_height, self.screenshot_width, vb.library.BitmapFormat.rgba)
        image = np.asarray(image).reshape(self.screenshot_width, self.screenshot_height, 4)[:, :, :3]
        return image

    def close(self):
        if self.vm is not None:
            self.vm.session.console.power_down().wait_for_completion(-1)
        sleep(1)

    def reset(self):
        print("Reset")
        snapshot_name = "Initial"

        self.current_step = 0

        if self.vm is not None:
            self.vm.session.console.power_down().wait_for_completion(-1)

        sleep(1)

        """
        machine_name = None
        while machine_name is None:
            
            print("Available:", available_machines)
            if len(available_machines) > 0:
                machine_name = available_machines[0]
            else:
                sleep(1)
        """
        machine_name = self.machine_name

        print("Starting", machine_name)
        import traceback
        import sys
        traceback.print_stack(file=sys.stdout)

        # Load VM
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
        sleep(40)

        # Get screen resolution
        self.screen_height, self.screen_width, _, _, _, _ = session.console.display.get_screen_resolution(0)

        self.vm = VirtualBoxVariables(session=session, virtual_machine=virtual_machine, snapshot=snapshot, machine_name=machine_name)

        return self._get_screenshot()

    def render(self, mode='human', close=False):
        return self._get_screenshot()