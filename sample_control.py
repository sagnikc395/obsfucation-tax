from inspect_ai import eval 

from control_arena import EvalMode
from control_arena.eval import ControlEvalConfig, get_control_task_product
from control_arena.micro_protocol import defer_to_trusted_builder
from control_arena.scorers import max_suspicion_scorer
from control_arena.settings.apps.apps_setting import AppsSetting


config = ControlEvalConfig(
    trusted_model="hf/Qwen/Qwen2.5-7B-Instruct",
    untrusted_model="hf/Qwen/Qwen2.5-7B-Instruct",
    limit=10,
)

eval_tasks = get_control_task_product(
    setting=AppsSetting(),
    micro_protocols=defer_to_trusted_builder(defer_threshold=0.5),
    modes=[EvalMode.HONEST, EvalMode.ATTACK],
    eval_config=config,
    monitoring_scorers=[max_suspicion_scorer()],
)
print(eval(tasks=eval_tasks,limit=1))