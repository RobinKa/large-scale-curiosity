from gym.envs.registration import register
import gym
#from .vmenv import VirtualBoxEnv

register(
    id="virtualbox-v1",
    entry_point="curiousvmenvs.vmenv:VirtualBoxEnv",
)

def make_virtualbox():
    return gym.make("virtualbox-v1")