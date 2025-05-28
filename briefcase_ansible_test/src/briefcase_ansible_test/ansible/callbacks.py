"""
Ansible callback implementations for briefcase_ansible_test.

This module contains callback classes for handling Ansible execution output.
"""

import threading
from ansible.plugins.callback import CallbackBase


class SimpleCallback(CallbackBase):
    """Simple callback for capturing and displaying Ansible output."""

    def __init__(self, output_callback):
        super().__init__()
        self.output_callback = output_callback
        self.host_ok = {}
        self.host_failed = {}
        self.host_unreachable = {}
        # Thread debugging
        self.main_thread_id = threading.get_ident()
        self.output_callback(f"🧵 Callback created on thread: {self.main_thread_id}\n")

    def v2_playbook_on_start(self, playbook):
        self.output_callback("📖 Playbook started\n")

    def v2_playbook_on_play_start(self, play):
        self.output_callback(f"🎭 Play started: {play.get_name()}\n")

    def v2_playbook_on_task_start(self, task, is_conditional):
        self.output_callback(f"🔧 Task started: {task.get_name()}\n")

    def v2_runner_on_start(self, host, task):
        self.output_callback(f"🚀 Starting task on {host}: {task.get_name()}\n")

    def v2_runner_on_ok(self, result):
        host = result._host.get_name()
        self.host_ok[host] = result
        self.output_callback(f"✅ {host} | PING => SUCCESS\n")

    def v2_runner_on_failed(self, result, ignore_errors=False):
        host = result._host.get_name()
        self.host_failed[host] = result
        msg = result._result.get("msg", "unknown error")
        self.output_callback(f"❌ {host} | PING => FAILED: {msg}\n")

    def v2_runner_on_unreachable(self, result):
        host = result._host.get_name()
        self.host_unreachable[host] = result
        msg = result._result.get("msg", "unreachable")
        self.output_callback(f"🔌 {host} | PING => UNREACHABLE: {msg}\n")

    def v2_runner_on_skipped(self, result):
        host = result._host.get_name()
        self.output_callback(f"⏭️  {host} | PING => SKIPPED\n")

    def v2_playbook_on_stats(self, stats):
        self.output_callback("📊 Final stats:\n")
        hosts = sorted(stats.processed.keys())
        for host in hosts:
            s = stats.summarize(host)
            self.output_callback(
                f"  {host}: ok={s['ok']}, changed={s['changed']}, unreachable={s['unreachable']}, failed={s['failures']}\n"
            )
