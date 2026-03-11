import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CLI_MAIN = REPO_ROOT / "tools" / "nx-collect" / "main.py"


def write_jsonl(path: Path, records) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False))
            handle.write("\n")


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False)


class NxCollectTests(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(CLI_MAIN), *args],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_latest_selects_newest_canonical_file_and_extracts_messages(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            codex_root = root / "codex"
            qwen_root = root / "qwen"
            pi_root = root / "pi"

            codex_file = codex_root / "2026" / "03" / "10" / "rollout-older.jsonl"
            qwen_file = qwen_root / "project" / "chats" / "latest.jsonl"
            pi_file = pi_root / "workspace" / "active.jsonl"
            write_jsonl(codex_file, [{"role": "user", "content": "older task"}])
            write_jsonl(
                qwen_file,
                [
                    {"role": "user", "content": "find the newest session"},
                    {"role": "assistant", "content": "working"},
                    {"role": "user", "content": "return the exact file path"},
                ],
            )
            write_jsonl(pi_file, [{"role": "user", "content": "this should not appear in latest matches"}])
            os.utime(codex_file, (1_700_000_000, 1_700_000_000))
            os.utime(qwen_file, (1_800_000_000, 1_800_000_000))
            os.utime(pi_file, (1_850_000_000, 1_850_000_000))

            config_path = root / "providers.json"
            write_json(
                config_path,
                {
                    "default_providers": ["codex", "qwen", "pi"],
                    "providers": {
                        "codex": {
                            "root": str(codex_root),
                            "include": ["**/rollout-*.jsonl"],
                            "exclude": [],
                        },
                        "qwen": {
                            "root": str(qwen_root),
                            "include": ["**/chats/*.jsonl"],
                            "exclude": [],
                        },
                        "pi": {
                            "root": str(pi_root),
                            "include": ["**/*.jsonl"],
                            "exclude": [],
                        },
                    },
                },
            )

            completed = self.run_cli(
                "--latest",
                "--providers",
                "codex,qwen,pi",
                "--providers-config",
                str(config_path),
                "--timezone",
                "UTC",
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["latest"]["provider"], "pi")
            self.assertEqual(payload["latest"]["path"], str(pi_file.resolve()))
            self.assertEqual(payload["latest"]["first_user_message"], "this should not appear in latest matches")
            self.assertEqual(payload["latest"]["last_user_message"], "this should not appear in latest matches")
            self.assertNotIn("matches", payload)
            self.assertNotIn("provider_latest", payload)

    def test_positional_latest_marks_recent_file_as_live(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            codex_root = root / "codex"
            codex_file = codex_root / "2026" / "03" / "10" / "rollout-live.jsonl"
            write_jsonl(codex_file, [{"role": "user", "content": "live session"}])
            now = time.time() - 120
            os.utime(codex_file, (now, now))

            config_path = root / "providers.json"
            write_json(
                config_path,
                {
                    "default_providers": ["codex"],
                    "providers": {
                        "codex": {
                            "root": str(codex_root),
                            "include": ["**/rollout-*.jsonl"],
                            "exclude": [],
                        }
                    },
                },
            )

            completed = self.run_cli(
                "latest",
                "--providers-config",
                str(config_path),
                "--live-within-minutes",
                "10",
                "--active-within-minutes",
                "60",
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["latest"]["activity_state"], "live")
            self.assertEqual(payload["query"]["mode"], "latest")
            self.assertEqual(payload["query"]["timezone"], "Europe/Moscow")

    def test_kimi_uses_wire_as_canonical_session_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            kimi_root = root / "kimi"
            session_dir = kimi_root / "hash-a" / "session-uuid"
            context_file = session_dir / "context.jsonl"
            wire_file = session_dir / "wire.jsonl"
            write_jsonl(context_file, [{"role": "user", "content": "newer context"}])
            write_jsonl(wire_file, [{"role": "user", "content": "canonical wire"}])
            os.utime(context_file, (1_900_000_000, 1_900_000_000))
            os.utime(wire_file, (1_800_000_000, 1_800_000_000))

            config_path = root / "providers.json"
            write_json(
                config_path,
                {
                    "default_providers": ["kimi"],
                    "providers": {
                        "kimi": {
                            "root": str(kimi_root),
                            "include": ["**/wire.jsonl"],
                            "exclude": ["**/context_sub_*.jsonl"],
                        }
                    },
                },
            )

            completed = self.run_cli(
                "--latest",
                "--providers-config",
                str(config_path),
                "--timezone",
                "UTC",
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["latest"]["path"], str(wire_file.resolve()))
            self.assertEqual(payload["latest"]["session_id"], "session-uuid")

    def test_claude_excludes_subagents_from_latest_results(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            claude_root = root / "claude"
            main_file = claude_root / "project-a" / "main.jsonl"
            subagent_file = claude_root / "project-a" / "subagents" / "newer.jsonl"
            write_jsonl(main_file, [{"role": "user", "content": "keep the parent session"}])
            write_jsonl(subagent_file, [{"role": "user", "content": "ignore the subagent session"}])
            os.utime(main_file, (1_800_000_000, 1_800_000_000))
            os.utime(subagent_file, (1_900_000_000, 1_900_000_000))

            config_path = root / "providers.json"
            write_json(
                config_path,
                {
                    "default_providers": ["claude"],
                    "providers": {
                        "claude": {
                            "root": str(claude_root),
                            "include": ["**/*.jsonl"],
                            "exclude": ["**/subagents/*.jsonl"],
                        }
                    },
                },
            )

            completed = self.run_cli(
                "--latest",
                "--providers-config",
                str(config_path),
                "--timezone",
                "UTC",
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["latest"]["path"], str(main_file.resolve()))
            self.assertEqual(payload["meta"]["scanned_files"], 1)

    def test_latest_rejects_limit_flag(self) -> None:
        completed = self.run_cli("--latest", "--limit=3")
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("unrecognized arguments: --limit=3", completed.stderr)

    def test_latest_can_filter_by_project_path_using_codex_cwd_and_provider_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            project_path = root / "sessions_landing"
            other_project = root / "other_project"
            codex_root = root / "codex"
            qwen_root = root / "qwen"

            codex_file = codex_root / "2026" / "03" / "10" / "rollout-project.jsonl"
            qwen_file = qwen_root / "-tmp" / f"-{project_path.as_posix().strip('/').replace('/', '-')}" / "chats" / "latest.jsonl"
            non_match_file = qwen_root / "-tmp" / f"-{other_project.as_posix().strip('/').replace('/', '-')}" / "chats" / "newest.jsonl"

            write_jsonl(
                codex_file,
                [
                    {
                        "timestamp": "2026-03-10T10:00:00+00:00",
                        "type": "session_meta",
                        "payload": {
                            "cwd": str(project_path),
                        },
                    },
                    {"role": "user", "content": "codex project session"},
                ],
            )
            write_jsonl(
                qwen_file,
                [
                    {"role": "user", "content": "matching qwen project session"},
                ],
            )
            write_jsonl(
                non_match_file,
                [
                    {"role": "user", "content": "newer but wrong project"},
                ],
            )
            os.utime(codex_file, (1_800_000_000, 1_800_000_000))
            os.utime(qwen_file, (1_850_000_000, 1_850_000_000))
            os.utime(non_match_file, (1_900_000_000, 1_900_000_000))

            config_path = root / "providers.json"
            write_json(
                config_path,
                {
                    "default_providers": ["codex", "qwen"],
                    "providers": {
                        "codex": {
                            "root": str(codex_root),
                            "include": ["**/rollout-*.jsonl"],
                            "exclude": [],
                        },
                        "qwen": {
                            "root": str(qwen_root),
                            "include": ["**/chats/*.jsonl"],
                            "exclude": [],
                        },
                    },
                },
            )

            completed = self.run_cli(
                "--latest",
                "--providers-config",
                str(config_path),
                "--project",
                str(project_path),
                "--timezone",
                "UTC",
                "--cognize-provider-chain",
                "local",
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["query"]["project"], str(project_path.resolve()))
            self.assertEqual(payload["latest"]["path"], str(qwen_file.resolve()))
            self.assertEqual(payload["latest"]["first_user_message"], "matching qwen project session")

    def test_latest_accepts_single_provider_alias(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            qwen_root = root / "qwen"
            qwen_file = qwen_root / "project" / "chats" / "latest.jsonl"
            write_jsonl(qwen_file, [{"role": "user", "content": "single provider alias"}])
            os.utime(qwen_file, (1_850_000_000, 1_850_000_000))

            config_path = root / "providers.json"
            write_json(
                config_path,
                {
                    "default_providers": ["qwen"],
                    "providers": {
                        "qwen": {
                            "root": str(qwen_root),
                            "include": ["**/chats/*.jsonl"],
                            "exclude": [],
                        }
                    },
                },
            )

            completed = self.run_cli(
                "--latest",
                "--provider",
                "qwen",
                "--providers-config",
                str(config_path),
                "--timezone",
                "UTC",
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["query"]["providers"], ["qwen"])
            self.assertEqual(payload["latest"]["path"], str(qwen_file.resolve()))

    def test_gemini_json_sessions_extract_nested_user_messages(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            gemini_root = root / "gemini"
            session_file = gemini_root / "workspace" / "chats" / "session-2026-03-10T05-44-demo.json"
            write_json(
                session_file,
                {
                    "sessionId": "demo",
                    "messages": [
                        {
                            "type": "user",
                            "content": [{"text": "first gemini instruction"}],
                        },
                        {
                            "type": "gemini",
                            "content": "working",
                        },
                        {
                            "type": "user",
                            "content": [{"text": "last gemini instruction"}],
                        },
                    ],
                },
            )
            os.utime(session_file, (1_800_000_000, 1_800_000_000))

            config_path = root / "providers.json"
            write_json(
                config_path,
                {
                    "default_providers": ["gemini"],
                    "providers": {
                        "gemini": {
                            "root": str(gemini_root),
                            "include": ["**/chats/session-*.json"],
                            "exclude": [],
                        }
                    },
                },
            )

            completed = self.run_cli(
                "--latest",
                "--providers-config",
                str(config_path),
                "--timezone",
                "UTC",
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["latest"]["format"], "json")
            self.assertEqual(payload["latest"]["first_user_message"], "first gemini instruction")
            self.assertEqual(payload["latest"]["last_user_message"], "last gemini instruction")

    def test_latest_includes_duration_and_intent_evolution(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            codex_root = root / "codex"
            session_file = codex_root / "2026" / "03" / "10" / "rollout-intent.jsonl"
            start_dt = datetime(2026, 3, 10, 8, 0, tzinfo=timezone.utc)
            modified_dt = datetime(2026, 3, 10, 10, 30, tzinfo=timezone.utc)

            write_jsonl(
                session_file,
                [
                    {"timestamp": start_dt.isoformat(), "role": "user", "content": "починить фильтр сегодня"},
                    {"timestamp": "2026-03-10T08:40:00+00:00", "role": "user", "content": "исправить latest карточку"},
                    {"timestamp": "2026-03-10T09:20:00+00:00", "role": "user", "content": "показать полный путь файла"},
                    {"timestamp": "2026-03-10T09:50:00+00:00", "role": "user", "content": "усилить playwright проверку"},
                ],
            )
            os.utime(session_file, (modified_dt.timestamp(), modified_dt.timestamp()))

            config_path = root / "providers.json"
            write_json(
                config_path,
                {
                    "default_providers": ["codex"],
                    "providers": {
                        "codex": {
                            "root": str(codex_root),
                            "include": ["**/rollout-*.jsonl"],
                            "exclude": [],
                        }
                    },
                },
            )

            completed = self.run_cli(
                "--latest",
                "--providers-config",
                str(config_path),
                "--timezone",
                "UTC",
                "--cognize-provider-chain",
                "local",
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            latest = payload["latest"]
            self.assertEqual(latest["started_at"], start_dt.isoformat())
            self.assertEqual(latest["duration_seconds"], 9000)
            self.assertEqual(latest["intent_summary_provider"], "local")
            self.assertEqual(latest["intent_summary_source"], "local_fallback")
            self.assertEqual(latest["intent_evolution"], [
                "починить фильтр сегодня",
                "исправить latest карточку",
                "показать полный путь",
                "проверить published flow",
            ])

    def test_latest_omits_duration_when_start_timestamp_is_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            qwen_root = root / "qwen"
            session_file = qwen_root / "project" / "chats" / "latest.jsonl"
            write_jsonl(
                session_file,
                [
                    {"role": "user", "content": "сделать latest карточку"},
                    {"role": "user", "content": "добавить intent bullets"},
                ],
            )
            os.utime(session_file, (1_800_000_000, 1_800_000_000))

            config_path = root / "providers.json"
            write_json(
                config_path,
                {
                    "default_providers": ["qwen"],
                    "providers": {
                        "qwen": {
                            "root": str(qwen_root),
                            "include": ["**/chats/*.jsonl"],
                            "exclude": [],
                        }
                    },
                },
            )

            completed = self.run_cli(
                "--latest",
                "--providers-config",
                str(config_path),
                "--timezone",
                "UTC",
                "--cognize-provider-chain",
                "local",
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            latest = payload["latest"]
            self.assertNotIn("started_at", latest)
            self.assertNotIn("duration_seconds", latest)
            self.assertEqual(latest["intent_summary_provider"], "local")
            self.assertEqual(latest["intent_summary_source"], "local_fallback")
            self.assertEqual(latest["intent_evolution"], [
                "исправить latest карточку",
                "усилить карточку сессии",
                "сделать latest карточку добавить intent",
            ])

    def test_date_today_returns_only_today_sessions(self) -> None:
        """Test --date today filters sessions modified today."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            codex_root = root / "codex"
            
            # Today's session
            today_file = codex_root / "2026" / "03" / "11" / "rollout-today.jsonl"
            write_jsonl(today_file, [{"role": "user", "content": "today session"}])
            
            # Yesterday's session
            yesterday_file = codex_root / "2026" / "03" / "10" / "rollout-yesterday.jsonl"
            write_jsonl(yesterday_file, [{"role": "user", "content": "yesterday session"}])
            
            now = time.time()
            os.utime(today_file, (now, now))
            os.utime(yesterday_file, (now - 86400, now - 86400))  # 1 day ago

            config_path = root / "providers.json"
            write_json(
                config_path,
                {
                    "default_providers": ["codex"],
                    "providers": {
                        "codex": {
                            "root": str(codex_root),
                            "include": ["**/rollout-*.jsonl"],
                            "exclude": [],
                        }
                    },
                },
            )

            completed = self.run_cli(
                "--date", "today",
                "--providers-config", str(config_path),
                "--timezone", "UTC",
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            
            self.assertIn("sessions", payload)
            self.assertEqual(len(payload["sessions"]), 1)
            self.assertEqual(payload["sessions"][0]["provider"], "codex")
            self.assertIn("rollout-today.jsonl", payload["sessions"][0]["path"])

    def test_date_yesterday_returns_only_yesterday_sessions(self) -> None:
        """Test --date yesterday filters sessions modified yesterday."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            codex_root = root / "codex"
            
            today_file = codex_root / "2026" / "03" / "11" / "rollout-today.jsonl"
            yesterday_file = codex_root / "2026" / "03" / "10" / "rollout-yesterday.jsonl"
            
            write_jsonl(today_file, [{"role": "user", "content": "today"}])
            write_jsonl(yesterday_file, [{"role": "user", "content": "yesterday"}])
            
            now = time.time()
            os.utime(today_file, (now, now))
            os.utime(yesterday_file, (now - 86400, now - 86400))

            config_path = root / "providers.json"
            write_json(
                config_path,
                {
                    "default_providers": ["codex"],
                    "providers": {
                        "codex": {
                            "root": str(codex_root),
                            "include": ["**/rollout-*.jsonl"],
                            "exclude": [],
                        }
                    },
                },
            )

            completed = self.run_cli(
                "--date", "yesterday",
                "--providers-config", str(config_path),
                "--timezone", "UTC",
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            
            self.assertEqual(len(payload["sessions"]), 1)
            self.assertIn("rollout-yesterday.jsonl", payload["sessions"][0]["path"])

    def test_date_specific_date_returns_matching_sessions(self) -> None:
        """Test --date YYYY-MM-DD filters sessions for specific date."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            codex_root = root / "codex"
            
            target_file = codex_root / "2026" / "03" / "05" / "rollout-target.jsonl"
            other_file = codex_root / "2026" / "03" / "10" / "rollout-other.jsonl"
            
            write_jsonl(target_file, [{"role": "user", "content": "target date"}])
            write_jsonl(other_file, [{"role": "user", "content": "other date"}])
            
            # March 5, 2026
            target_ts = datetime(2026, 3, 5, 12, 0, tzinfo=timezone.utc).timestamp()
            # March 10, 2026
            other_ts = datetime(2026, 3, 10, 12, 0, tzinfo=timezone.utc).timestamp()
            
            os.utime(target_file, (target_ts, target_ts))
            os.utime(other_file, (other_ts, other_ts))

            config_path = root / "providers.json"
            write_json(
                config_path,
                {
                    "default_providers": ["codex"],
                    "providers": {
                        "codex": {
                            "root": str(codex_root),
                            "include": ["**/rollout-*.jsonl"],
                            "exclude": [],
                        }
                    },
                },
            )

            completed = self.run_cli(
                "--date", "2026-03-05",
                "--providers-config", str(config_path),
                "--timezone", "UTC",
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            
            self.assertEqual(len(payload["sessions"]), 1)
            self.assertIn("rollout-target.jsonl", payload["sessions"][0]["path"])

    def test_date_last_n_days_returns_sessions_in_range(self) -> None:
        """Test --date last-N-days filters sessions within N days."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            codex_root = root / "codex"
            
            # Sessions at different ages
            recent_file = codex_root / "recent.jsonl"
            week_ago_file = codex_root / "week-ago.jsonl"
            old_file = codex_root / "old.jsonl"
            
            write_jsonl(recent_file, [{"role": "user", "content": "recent"}])
            write_jsonl(week_ago_file, [{"role": "user", "content": "week ago"}])
            write_jsonl(old_file, [{"role": "user", "content": "old"}])
            
            now = time.time()
            os.utime(recent_file, (now, now))
            os.utime(week_ago_file, (now - 5 * 86400, now - 5 * 86400))  # 5 days ago
            os.utime(old_file, (now - 10 * 86400, now - 10 * 86400))  # 10 days ago

            config_path = root / "providers.json"
            write_json(
                config_path,
                {
                    "default_providers": ["codex"],
                    "providers": {
                        "codex": {
                            "root": str(codex_root),
                            "include": ["*.jsonl"],
                            "exclude": [],
                        }
                    },
                },
            )

            completed = self.run_cli(
                "--date", "last-7-days",
                "--providers-config", str(config_path),
                "--timezone", "UTC",
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            
            # Should include recent and week_ago, but not old
            self.assertEqual(len(payload["sessions"]), 2)
            paths = [s["path"] for s in payload["sessions"]]
            self.assertTrue(any("recent" in p for p in paths))
            self.assertTrue(any("week-ago" in p for p in paths))
            self.assertFalse(any("old" in p for p in paths))

    def test_date_with_project_filters_by_project_and_date(self) -> None:
        """Test --date with --project filters by both."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            project_path = root / "my_project"
            other_project = root / "other_project"
            qwen_root = root / "qwen"
            
            # Matching project, today
            match_file = qwen_root / "-tmp" / f"-{project_path.as_posix().strip('/').replace('/', '-')}" / "chats" / "latest.jsonl"
            # Matching project, yesterday
            old_match_file = qwen_root / "-tmp" / f"-{project_path.as_posix().strip('/').replace('/', '-')}" / "chats" / "old.jsonl"
            # Other project, today
            other_file = qwen_root / "-tmp" / f"-{other_project.as_posix().strip('/').replace('/', '-')}" / "chats" / "other.jsonl"
            
            write_jsonl(match_file, [{"role": "user", "content": "match"}])
            write_jsonl(old_match_file, [{"role": "user", "content": "old match"}])
            write_jsonl(other_file, [{"role": "user", "content": "other"}])
            
            now = time.time()
            os.utime(match_file, (now, now))
            os.utime(old_match_file, (now - 86400, now - 86400))
            os.utime(other_file, (now, now))

            config_path = root / "providers.json"
            write_json(
                config_path,
                {
                    "default_providers": ["qwen"],
                    "providers": {
                        "qwen": {
                            "root": str(qwen_root),
                            "include": ["**/chats/*.jsonl"],
                            "exclude": [],
                        }
                    },
                },
            )

            completed = self.run_cli(
                "--date", "today",
                "--project", str(project_path),
                "--providers-config", str(config_path),
                "--timezone", "UTC",
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            
            self.assertEqual(len(payload["sessions"]), 1)
            self.assertIn("latest.jsonl", payload["sessions"][0]["path"])

    def test_date_pretty_renders_human_friendly_list(self) -> None:
        """Test --date with --pretty renders human-friendly output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            codex_root = root / "codex"
            qwen_root = root / "qwen"
            
            codex_file = codex_root / "today.jsonl"
            qwen_file = qwen_root / "chats" / "today.jsonl"
            
            write_jsonl(codex_file, [{"role": "user", "content": "codex today"}])
            write_jsonl(qwen_file, [{"role": "user", "content": "qwen today"}])
            
            now = time.time()
            os.utime(codex_file, (now, now))
            os.utime(qwen_file, (now - 3600, now - 3600))  # 1 hour ago

            config_path = root / "providers.json"
            write_json(
                config_path,
                {
                    "default_providers": ["codex", "qwen"],
                    "providers": {
                        "codex": {
                            "root": str(codex_root),
                            "include": ["*.jsonl"],
                            "exclude": [],
                        },
                        "qwen": {
                            "root": str(qwen_root),
                            "include": ["**/*.jsonl"],
                            "exclude": [],
                        }
                    },
                },
            )

            completed = self.run_cli(
                "--date", "today",
                "--pretty",
                "--providers-config", str(config_path),
                "--timezone", "UTC",
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            
            # Check pretty output format
            self.assertIn("📋", completed.stdout)
            self.assertIn("codex", completed.stdout)
            self.assertIn("qwen", completed.stdout)
            self.assertNotIn('"meta"', completed.stdout)  # Not JSON

    def test_sessions_includes_provider_and_path_details(self) -> None:
        """Test sessions array includes all required fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            codex_root = root / "codex"
            session_file = codex_root / "session.jsonl"
            
            write_jsonl(session_file, [{"role": "user", "content": "test"}])
            now = time.time()
            os.utime(session_file, (now, now))

            config_path = root / "providers.json"
            write_json(
                config_path,
                {
                    "default_providers": ["codex"],
                    "providers": {
                        "codex": {
                            "root": str(codex_root),
                            "include": ["*.jsonl"],
                            "exclude": [],
                        }
                    },
                },
            )

            completed = self.run_cli(
                "--date", "today",
                "--providers-config", str(config_path),
                "--timezone", "UTC",
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            
            session = payload["sessions"][0]
            self.assertEqual(session["provider"], "codex")
            self.assertIn("path", session)
            self.assertIn("relative_path", session)
            self.assertIn("modified_at", session)
            self.assertIn("modified_human", session)
            self.assertIn("activity_state", session)


if __name__ == "__main__":
    unittest.main()
