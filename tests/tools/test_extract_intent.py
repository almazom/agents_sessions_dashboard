import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CLI_MAIN = REPO_ROOT / "tools" / "extract-intent" / "main.py"
MODULE_SPEC = importlib.util.spec_from_file_location("extract_intent_main", CLI_MAIN)
MODULE = importlib.util.module_from_spec(MODULE_SPEC)
assert MODULE_SPEC is not None and MODULE_SPEC.loader is not None
MODULE_SPEC.loader.exec_module(MODULE)


def write_jsonl(path: Path, records) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False))
            handle.write("\n")


class ExtractIntentTests(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(CLI_MAIN), *args],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_default_mode_returns_json_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            source_path = root / "session.jsonl"
            state_path = root / "provider-state.json"
            write_jsonl(
                source_path,
                [
                    {"role": "user", "content": "починить фильтр сегодня"},
                    {"role": "user", "content": "исправить latest карточку"},
                    {"role": "user", "content": "показать полный путь файла"},
                    {"role": "user", "content": "проверить published flow через playwright"},
                ],
            )

            completed = self.run_cli(
                "--input",
                str(source_path),
                "--provider-chain",
                "local",
                "--state-file",
                str(state_path),
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)

            self.assertEqual(payload["meta"]["tool"], "extract-intent")
            self.assertEqual(payload["meta"]["selected_provider"], "local")
            self.assertEqual(payload["meta"]["processing_provider"], "local")
            self.assertEqual(payload["meta"]["summary_source"], "local_fallback")
            self.assertNotIn("path", payload["source"])
            self.assertEqual(payload["source"]["harness_provider"], "")
            self.assertEqual(
                payload["intent"]["summary"],
                "Пользователь хочет починить фильтр сегодня, исправить latest карточку и показать полный путь.",
            )
            self.assertEqual(payload["intent"]["steps"], [
                "починить фильтр сегодня",
                "исправить latest карточку",
                "показать полный путь",
                "проверить published flow",
            ])

    def test_pretty_mode_renders_numbered_terminal_view(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            source_path = root / "session.jsonl"
            state_path = root / "provider-state.json"
            write_jsonl(
                source_path,
                [
                    {"role": "user", "content": "починить фильтр сегодня"},
                    {"role": "user", "content": "исправить latest карточку"},
                    {"role": "user", "content": "показать полный путь файла"},
                ],
            )

            completed = self.run_cli(
                "--input",
                str(source_path),
                "--provider-chain",
                "local",
                "--state-file",
                str(state_path),
                "--pretty",
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("🧭 Вектор намерений", completed.stdout)
            self.assertIn("📝 Пользователь хочет", completed.stdout)
            self.assertNotIn("📁", completed.stdout)
            self.assertNotIn("🤖", completed.stdout)
            self.assertIn("① починить фильтр сегодня", completed.stdout)
            self.assertIn("② исправить latest карточку", completed.stdout)
            self.assertIn("③ показать полный путь", completed.stdout)
            self.assertNotIn('"meta"', completed.stdout)

    def test_project_mode_resolves_latest_session_before_extracting_intent(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            project_path = root / "sessions_landing"
            qwen_root = root / "qwen"
            session_path = qwen_root / "-tmp" / f"-{project_path.as_posix().strip('/').replace('/', '-')}" / "chats" / "latest.jsonl"
            state_path = root / "provider-state.json"

            write_jsonl(
                session_path,
                [
                    {"role": "user", "content": "починить фильтр сегодня"},
                    {"role": "user", "content": "исправить latest карточку"},
                    {"role": "user", "content": "показать полный путь файла"},
                ],
            )

            config_path = root / "providers.json"
            with open(config_path, "w", encoding="utf-8") as handle:
                json.dump(
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
                    handle,
                    ensure_ascii=False,
                )

            completed = self.run_cli(
                "--project",
                str(project_path),
                "--providers-config",
                str(config_path),
                "--provider-chain",
                "local",
                "--state-file",
                str(state_path),
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["meta"]["selected_provider"], "local")
            self.assertEqual(payload["source"]["harness_provider"], "qwen")
            self.assertEqual(payload["source"]["provider"], "qwen")
            self.assertEqual(
                payload["intent"]["summary"],
                "Пользователь хочет починить фильтр сегодня, исправить latest карточку и показать полный путь.",
            )

    def test_project_mode_accepts_single_provider_alias(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            project_path = root / "sessions_landing"
            qwen_root = root / "qwen"
            session_path = qwen_root / "-tmp" / f"-{project_path.as_posix().strip('/').replace('/', '-')}" / "chats" / "latest.jsonl"
            state_path = root / "provider-state.json"

            write_jsonl(
                session_path,
                [
                    {"role": "user", "content": "починить фильтр сегодня"},
                    {"role": "user", "content": "исправить latest карточку"},
                    {"role": "user", "content": "показать полный путь файла"},
                ],
            )

            config_path = root / "providers.json"
            with open(config_path, "w", encoding="utf-8") as handle:
                json.dump(
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
                    handle,
                    ensure_ascii=False,
                )

            completed = self.run_cli(
                "--project",
                str(project_path),
                "--hp",
                "qwen",
                "--providers-config",
                str(config_path),
                "--provider-chain",
                "local",
                "--state-file",
                str(state_path),
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["source"]["harness_provider"], "qwen")
            self.assertEqual(payload["source"]["provider"], "qwen")

    def test_pretty_project_mode_shows_harness_and_processing_line(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            project_path = root / "sessions_landing"
            qwen_root = root / "qwen"
            session_path = qwen_root / "-tmp" / f"-{project_path.as_posix().strip('/').replace('/', '-')}" / "chats" / "latest.jsonl"
            state_path = root / "provider-state.json"

            write_jsonl(
                session_path,
                [
                    {"role": "user", "content": "починить фильтр сегодня"},
                    {"role": "user", "content": "исправить latest карточку"},
                    {"role": "user", "content": "показать полный путь файла"},
                ],
            )

            config_path = root / "providers.json"
            with open(config_path, "w", encoding="utf-8") as handle:
                json.dump(
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
                    handle,
                    ensure_ascii=False,
                )

            completed = self.run_cli(
                "--project",
                str(project_path),
                "--hp",
                "qwen",
                "--pp",
                "local",
                "--providers-config",
                str(config_path),
                "--state-file",
                str(state_path),
                "--pretty",
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("🧩 harness: qwen · processing: local", completed.stdout)

    def test_processing_provider_alias_maps_to_single_summarizer(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            source_path = root / "session.jsonl"
            state_path = root / "provider-state.json"
            write_jsonl(
                source_path,
                [
                    {"role": "user", "content": "починить фильтр сегодня"},
                    {"role": "user", "content": "исправить latest карточку"},
                    {"role": "user", "content": "показать полный путь файла"},
                ],
            )

            completed = self.run_cli(
                "--input",
                str(source_path),
                "--processing-provider",
                "local",
                "--state-file",
                str(state_path),
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["meta"]["selected_provider"], "local")
            self.assertEqual(payload["meta"]["processing_provider"], "local")

    def test_pp_alias_maps_to_processing_provider(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            source_path = root / "session.jsonl"
            state_path = root / "provider-state.json"
            write_jsonl(
                source_path,
                [
                    {"role": "user", "content": "починить фильтр сегодня"},
                    {"role": "user", "content": "исправить latest карточку"},
                    {"role": "user", "content": "показать полный путь файла"},
                ],
            )

            completed = self.run_cli(
                "--input",
                str(source_path),
                "--pp",
                "local",
                "--state-file",
                str(state_path),
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["meta"]["selected_provider"], "local")
            self.assertEqual(payload["meta"]["processing_provider"], "local")

    def test_auto_processing_chain_excludes_same_harness_provider(self) -> None:
        resolved = MODULE.resolve_effective_processing_chain(
            base_dir=CLI_MAIN.parent,
            processing_provider=None,
            provider_chain="auto",
            harness_provider="pi",
        )
        self.assertEqual(resolved, "gemini,claude,qwen")


if __name__ == "__main__":
    unittest.main()
