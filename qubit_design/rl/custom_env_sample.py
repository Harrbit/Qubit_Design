import gymnasium as gym
from gymnasium import spaces
import numpy as np

class TransmonDesignEnv(gym.Env):
    def __init__(self, sim_function, target_params):
        super().__init__()

        self.low = np.array([2.0, 5.0, 1.0, 5.0, 5.0, 1.0])
        self.high = np.array([20.0, 100.0, 10.0, 50.0, 100.0, 10.0])
        self.observation_space = spaces.Box(low=self.low, high=self.high, dtype=np.float32)
        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(6,), dtype=np.float32)

        self.sim_function = sim_function
        self.target = target_params

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.state = np.random.uniform(self.low, self.high)
        return self.state, {}

    def step(self, action):
        # Scale action to actual geometry space
        scaled_action = np.clip(self.state + action * (self.high - self.low) * 0.1, self.low, self.high)
        self.state = scaled_action

        # Run HFSS simulation (or load from surrogate model)
        result = self.sim_function(self.state)  # returns dict with f_q, alpha, chi, kerr

        # Calculate reward (negative error)
        reward = -(
            abs(result["f_q"] - self.target["f_q"])**2 +
            abs(result["alpha"] - self.target["alpha"])**2 +
            abs(result["chi"] - self.target["chi"])**2 +
            0.5 * abs(result["kerr"])  # regularize Kerr nonlinearity
        )

        done = False  # Set to True if you want episodic behavior
        return self.state, reward, done, False, {"result": result}
