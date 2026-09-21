"""TD3 on Pendulum-v1 — a single-file learning demo.

Deliberately ONE self-contained file: this is a teaching artifact and a smoke test, not the port.
The shipped agent is jlab_opt_control/agents/torch_td3.py in the SciOptControlToolkit clone, with
its hyperparameters in cfgs/torch_td3.cfg, per CLAUDE.md. Hyperparameters are inline constants here
so you can read the whole algorithm top to bottom in one sitting.

Run:
    python td3_pendulum_demo.py                 # ~50 episodes, should reach about -200
    python td3_pendulum_demo.py --episodes 30   # shorter
    python td3_pendulum_demo.py --seed 1        # different seed

Reference that was ported: <PROJECT_ROOT>/SciOptControlToolkit/jlab_opt_control/agents/keras_td3.py
Companion notes: 1-rl-and-td3.md
"""

from __future__ import annotations

import argparse

import gymnasium as gym
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

# ---------------------------------------------------------------------------------------------
# Hyperparameters. In the shipped agent these live in cfgs/torch_td3.cfg — never in code.
# ---------------------------------------------------------------------------------------------
GAMMA = 0.99          # discount: how much a future reward is worth relative to an immediate one
TAU = 0.005           # soft-update rate for target networks (0.5% of the online net per update)
ACTOR_LR = 3e-4
CRITIC_LR = 3e-4
BATCH_SIZE = 256
BUFFER_CAPACITY = 100_000
WARMUP_STEPS = 1_000  # uniform random actions before the policy takes over (reference uses 2500)
EXPLORE_NOISE = 0.1   # stddev of exploration noise, as a fraction of the action scale
POLICY_NOISE = 0.2    # stddev of target-policy smoothing noise, same units
NOISE_CLIP = 0.5      # target-policy noise is clipped to +/- this, same units
POLICY_DELAY = 2      # actor (and all target nets) update once every N critic updates
HIDDEN = (256, 256)


# ---------------------------------------------------------------------------------------------
# Networks
# ---------------------------------------------------------------------------------------------
class Actor(nn.Module):
    """Deterministic policy: state -> action. TD3's actor outputs one action, not a distribution.

    tanh bounds the output to [-1, 1]; we then rescale to the environment's actual action range.
    Registering scale/bias as buffers (not plain tensors) means .to(device) moves them and
    state_dict() saves them.
    """

    def __init__(self, obs_dim: int, act_dim: int, low: np.ndarray, high: np.ndarray) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(obs_dim, HIDDEN[0]), nn.ReLU(),
            nn.Linear(HIDDEN[0], HIDDEN[1]), nn.ReLU(),
            nn.Linear(HIDDEN[1], act_dim), nn.Tanh(),
        )
        self.register_buffer("action_scale", torch.tensor((high - low) / 2.0, dtype=torch.float32))
        self.register_buffer("action_bias", torch.tensor((high + low) / 2.0, dtype=torch.float32))

    def forward(self, obs: torch.Tensor) -> torch.Tensor:
        return self.net(obs) * self.action_scale + self.action_bias


class Critic(nn.Module):
    """Q-function: (state, action) -> a single scalar estimate of expected discounted return."""

    def __init__(self, obs_dim: int, act_dim: int) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(obs_dim + act_dim, HIDDEN[0]), nn.ReLU(),
            nn.Linear(HIDDEN[0], HIDDEN[1]), nn.ReLU(),
            nn.Linear(HIDDEN[1], 1),
        )

    def forward(self, obs: torch.Tensor, act: torch.Tensor) -> torch.Tensor:
        return self.net(torch.cat([obs, act], dim=1))


# ---------------------------------------------------------------------------------------------
# Replay buffer
# ---------------------------------------------------------------------------------------------
class ReplayBuffer:
    """Fixed-capacity ring buffer of transitions, sampled uniformly at random.

    Random sampling is the point: consecutive steps in an episode are highly correlated, and
    training a network on correlated batches destabilises it. The buffer decorrelates them.

    NOTE the `done` argument is `terminated` ONLY, never `terminated or truncated` — see
    the train() docstring and 1-rl-and-td3.md, Part 1.
    """

    def __init__(self, capacity: int, obs_dim: int, act_dim: int) -> None:
        self.capacity = capacity
        self.obs = np.zeros((capacity, obs_dim), dtype=np.float32)
        self.act = np.zeros((capacity, act_dim), dtype=np.float32)
        self.rew = np.zeros((capacity, 1), dtype=np.float32)
        self.next_obs = np.zeros((capacity, obs_dim), dtype=np.float32)
        self.done = np.zeros((capacity, 1), dtype=np.float32)
        self.ptr = 0          # total transitions ever written (not the write index)
        self.full = False

    def add(self, obs, act, rew, next_obs, done) -> None:
        i = self.ptr % self.capacity
        self.obs[i], self.act[i], self.rew[i], self.next_obs[i], self.done[i] = (
            obs, act, rew, next_obs, float(done),
        )
        self.ptr += 1
        if self.ptr >= self.capacity:
            self.full = True

    def __len__(self) -> int:
        return self.capacity if self.full else self.ptr

    def sample(self, batch_size: int, device: torch.device, rng: np.random.Generator):
        idx = rng.integers(0, len(self), size=batch_size)
        as_t = lambda a: torch.as_tensor(a[idx], device=device)  # noqa: E731
        return as_t(self.obs), as_t(self.act), as_t(self.rew), as_t(self.next_obs), as_t(self.done)


# ---------------------------------------------------------------------------------------------
# TD3 agent
# ---------------------------------------------------------------------------------------------
class TD3:
    """Twin Delayed DDPG. Three additions to DDPG, each fixing an overestimation failure mode:

    1. Clipped double-Q  — two critics, take the MINIMUM for the target. A single critic's
       overestimation errors get baked into its own target and compound.
    2. Target policy smoothing — add clipped noise to the target action, so the critic cannot
       exploit a sharp spurious peak in its own Q landscape.
    3. Delayed policy updates — update the actor every other critic step, so the policy chases a
       critic that has had time to settle.
    """

    def __init__(self, obs_dim, act_dim, low, high, device, seed: int) -> None:
        self.device = device
        self.low = torch.as_tensor(low, dtype=torch.float32, device=device)
        self.high = torch.as_tensor(high, dtype=torch.float32, device=device)
        self.rng = np.random.default_rng(seed)

        self.actor = Actor(obs_dim, act_dim, low, high).to(device)
        self.critic1 = Critic(obs_dim, act_dim).to(device)
        self.critic2 = Critic(obs_dim, act_dim).to(device)

        # Target networks: frozen-ish copies that provide a slow-moving regression target.
        # Without them the critic chases its own output and diverges.
        import copy
        self.actor_target = copy.deepcopy(self.actor)
        self.critic1_target = copy.deepcopy(self.critic1)
        self.critic2_target = copy.deepcopy(self.critic2)
        for p in [*self.actor_target.parameters(),
                  *self.critic1_target.parameters(),
                  *self.critic2_target.parameters()]:
            p.requires_grad_(False)  # targets are updated by soft-copy, never by gradients

        self.actor_opt = torch.optim.Adam(self.actor.parameters(), lr=ACTOR_LR)
        # Separate optimizers per critic. The reference shares ONE optimizer across both critics
        # by summing their losses; identical gradients, but Adam's per-parameter moments are then
        # kept in one state blob. Standard TD3 keeps them separate, so we do too.
        self.critic1_opt = torch.optim.Adam(self.critic1.parameters(), lr=CRITIC_LR)
        self.critic2_opt = torch.optim.Adam(self.critic2.parameters(), lr=CRITIC_LR)

        self.action_scale = self.actor.action_scale
        self.total_updates = 0

    @torch.no_grad()  # inference only: don't build an autograd graph
    def act(self, obs: np.ndarray, noise: bool) -> np.ndarray:
        obs_t = torch.as_tensor(obs, dtype=torch.float32, device=self.device).unsqueeze(0)
        action = self.actor(obs_t).squeeze(0)
        if noise:
            action = action + torch.randn_like(action) * self.action_scale * EXPLORE_NOISE
        return action.clamp(self.low, self.high).cpu().numpy()

    def train_step(self, buffer: ReplayBuffer) -> None:
        obs, act, rew, next_obs, done = buffer.sample(BATCH_SIZE, self.device, self.rng)
        self.total_updates += 1

        # ---- critic update ----
        with torch.no_grad():  # the target is a constant; no gradient flows into target nets
            # Trick 2: target policy smoothing.
            noise = (torch.randn_like(act) * self.action_scale * POLICY_NOISE).clamp(
                -NOISE_CLIP * self.action_scale, NOISE_CLIP * self.action_scale
            )
            next_act = (self.actor_target(next_obs) + noise).clamp(self.low, self.high)

            # Trick 1: clipped double-Q — pessimism via the minimum.
            target_q = torch.min(self.critic1_target(next_obs, next_act),
                                 self.critic2_target(next_obs, next_act))

            # Bellman target. (1 - done) cuts the bootstrap at a TRUE terminal state only.
            # `done` here is `terminated`; on truncation we must still bootstrap, because the
            # state was fine and has real future value. Pendulum only ever truncates, so this
            # factor is always 1.0 here -- the terminal path is NOT exercised by this test.
            target = rew + GAMMA * (1.0 - done) * target_q

        critic1_loss = F.mse_loss(self.critic1(obs, act), target)
        critic2_loss = F.mse_loss(self.critic2(obs, act), target)

        self.critic1_opt.zero_grad(set_to_none=True)  # gradients ACCUMULATE in torch; clear first
        critic1_loss.backward()
        self.critic1_opt.step()

        self.critic2_opt.zero_grad(set_to_none=True)
        critic2_loss.backward()
        self.critic2_opt.step()

        # ---- actor update, delayed (trick 3) ----
        if self.total_updates % POLICY_DELAY == 0:
            # Maximise Q(s, pi(s)) == minimise -Q. Gradients flow through critic1 into the actor,
            # which is why critic1's parameters must not be stepped by the actor's optimizer --
            # actor_opt only holds actor params, so they aren't.
            actor_loss = -self.critic1(obs, self.actor(obs)).mean()
            self.actor_opt.zero_grad(set_to_none=True)
            actor_loss.backward()
            self.actor_opt.step()

            for net, target_net in [(self.actor, self.actor_target),
                                    (self.critic1, self.critic1_target),
                                    (self.critic2, self.critic2_target)]:
                soft_update(net, target_net, TAU)


@torch.no_grad()
def soft_update(net: nn.Module, target_net: nn.Module, tau: float) -> None:
    """target = tau * online + (1 - tau) * target, in place (Polyak averaging)."""
    for p, tp in zip(net.parameters(), target_net.parameters()):
        tp.mul_(1.0 - tau).add_(tau * p)


# ---------------------------------------------------------------------------------------------
# Training loop
# ---------------------------------------------------------------------------------------------
def evaluate(env: gym.Env, agent: TD3, episodes: int = 3) -> float:
    """Greedy (no exploration noise) return, averaged over a few episodes."""
    returns = []
    for _ in range(episodes):
        obs, _ = env.reset()
        done, total = False, 0.0
        while not done:
            obs, reward, terminated, truncated, _ = env.step(agent.act(obs, noise=False))
            total += reward
            done = terminated or truncated
        returns.append(total)
    return float(np.mean(returns))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", default="Pendulum-v1")
    parser.add_argument("--episodes", type=int, default=60)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--eval-every", type=int, default=5)
    args = parser.parse_args()

    # Seed everything. Three independent RNGs: torch (weight init), the env (start states), and
    # the action space (warm-up sampling). The reference toolkit seeds from wall-clock time and
    # never seeds the action space, so it cannot reproduce a run. Don't copy that.
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)

    env = gym.make(args.env)
    eval_env = gym.make(args.env)
    env.action_space.seed(args.seed)
    eval_env.action_space.seed(args.seed + 10_000)

    assert isinstance(env.action_space, gym.spaces.Box), "TD3 is continuous-control only"
    obs_dim = env.observation_space.shape[0]
    act_dim = env.action_space.shape[0]
    low, high = env.action_space.low, env.action_space.high

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"env={args.env} obs_dim={obs_dim} act_dim={act_dim} "
          f"action_range=[{low[0]:.1f}, {high[0]:.1f}]")
    print(f"device={device}  torch={torch.__version__}  gymnasium={gym.__version__}  "
          f"seed={args.seed}\n")

    agent = TD3(obs_dim, act_dim, low, high, device, args.seed)
    buffer = ReplayBuffer(BUFFER_CAPACITY, obs_dim, act_dim)

    # seed=... passed ONCE: it seeds the env's generator. Passing it every reset would give the
    # identical start state every episode -- a degenerate training distribution.
    obs, _ = env.reset(seed=args.seed)
    total_steps = 0
    best_eval = -float("inf")
    recent: list[float] = []

    for ep in range(1, args.episodes + 1):
        ep_return, ep_steps, done = 0.0, 0, False
        while not done:
            if total_steps < WARMUP_STEPS:
                # An untrained actor emits near-constant actions, which teaches the critic almost
                # nothing. Uniform random actions fill the buffer with diverse experience first.
                action = env.action_space.sample()
            else:
                action = agent.act(obs, noise=True)

            next_obs, reward, terminated, truncated, _ = env.step(action)

            # `terminated` alone goes in the buffer -- NOT `terminated or truncated`.
            buffer.add(obs, action, reward, next_obs, terminated)
            obs = next_obs
            ep_return += reward
            ep_steps += 1
            total_steps += 1
            done = terminated or truncated

            if total_steps >= WARMUP_STEPS and len(buffer) >= BATCH_SIZE:
                agent.train_step(buffer)

        obs, _ = env.reset()
        recent.append(ep_return)
        avg10 = float(np.mean(recent[-10:]))
        phase = "warmup" if total_steps <= WARMUP_STEPS else "train "
        line = (f"ep {ep:3d} | {phase} | steps {total_steps:6d} | "
                f"return {ep_return:8.1f} | avg10 {avg10:8.1f}")

        if ep % args.eval_every == 0:
            eval_return = evaluate(eval_env, agent)
            best_eval = max(best_eval, eval_return)
            line += f" | EVAL {eval_return:8.1f} (best {best_eval:8.1f})"
        print(line)

    print(f"\nfinal avg10={float(np.mean(recent[-10:])):.1f}  best_eval={best_eval:.1f}")
    print("Reference points: random ~= -1200, do-nothing ~= -1900, solved <= -200.")
    print("SOLVED" if best_eval >= -250 else "not yet at the -200 bar")


if __name__ == "__main__":
    main()
