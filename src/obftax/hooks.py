"""Forward hooks on one decoder block, and a context manager that always removes them.

Every intervention in the project is one of four things done to a decoder layer's
output: subtract a fixed multiple of a direction (steering, step 4), remove the
component along a direction (projection, mech A), overwrite one position (patching,
mech C), or just look (capture). A left-behind handle silently contaminates every later
generation, so they are attached through `attach`, never by hand.
"""

from contextlib import contextmanager

import numpy as np
import torch


def _as_tensor(vec):
    return None if vec is None else torch.tensor(np.asarray(vec), dtype=torch.float32)


def _unwrap(output):
    return output[0] if isinstance(output, tuple) else output


def _rewrap(output, h):
    return (h,) + tuple(output[1:]) if isinstance(output, tuple) else h


class Steer:
    """Subtract `alpha * direction` from the layer output, and keep the result.

    scope="all" steers every position, including the prompt. scope="answer" steers only
    the generated positions, which is closer to an attacker who controls its own
    behaviour rather than its own prompt processing. `n_prompt` is only read for
    scope="answer"; the hook tracks absolute position itself because generation calls it
    once per step.
    """

    def __init__(self, direction, alpha, scope="all", n_prompt=0):
        self.v = _as_tensor(direction)
        self.alpha, self.scope, self.n_prompt = alpha, scope, n_prompt
        self.pos = 0
        self.captured = None

    def __call__(self, module, args, output):
        h = _unwrap(output)
        n = h.shape[1]
        if self.alpha != 0.0:
            v = self.v.to(h.device, h.dtype)
            if self.scope == "all":
                h = h - self.alpha * v
            else:
                start = max(0, self.n_prompt - self.pos)
                if start < n:
                    h = h.clone()
                    h[:, start:] = h[:, start:] - self.alpha * v
        self.pos += n
        self.captured = h.detach()
        return _rewrap(output, h)


class Project:
    """Remove the component along a unit-norm direction, leaving the rest alone."""

    def __init__(self, direction):
        self.v = _as_tensor(direction)
        self.captured = None

    def __call__(self, module, args, output):
        h = _unwrap(output)
        v = self.v.to(h.device, h.dtype)
        h = h - (h @ v).unsqueeze(-1) * v
        self.captured = h.detach()
        return _rewrap(output, h)


class Patch:
    """Overwrite the last prefill position with a donor residual, then stand aside.

    Only the prefill pass is touched (h.shape[1] > 1): the decision position is the last
    prompt token, and the decode steps that follow must run on the patched state rather
    than be patched again.
    """

    def __init__(self, vector):
        self.v = _as_tensor(vector)

    def __call__(self, module, args, output):
        h = _unwrap(output)
        if h.shape[1] == 1:
            return output
        h = h.clone()
        h[0, -1] = self.v.to(h.device, h.dtype)
        return _rewrap(output, h)


class Capture:
    """Read-only. `last_prompt_only` keeps just the final prefill position, which is the
    state the model has computed before it answers."""

    def __init__(self, last_prompt_only=False):
        self.last_prompt_only = last_prompt_only
        self.captured = None

    def __call__(self, module, args, output):
        h = _unwrap(output)
        if self.last_prompt_only:
            if h.shape[1] > 1:
                self.captured = h[0, -1].detach().float().cpu().numpy()
        else:
            self.captured = h.detach()
        return output


@contextmanager
def attach(hooks, layers_mod=None):
    """`hooks` is an iterable of (target, hook). A target is a module, or a layer index
    when `layers_mod` is given. Hooks fire in the order listed, so a Capture after a
    Steer on the same layer sees the steered output."""
    handles = []
    try:
        for target, hk in hooks:
            mod = layers_mod[target] if isinstance(target, int) else target
            handles.append(mod.register_forward_hook(hk))
        yield
    finally:
        for h in handles:
            h.remove()
