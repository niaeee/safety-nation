"""보고서 초안 생성기. claude -p CLI 어댑터 + 결정론 fallback.

출품 1차: ClaudeCliDrafter (claude -p subprocess)
운영 전환: AnthropicSdkDrafter (미구현)
실패 fallback: TemplateDrafter
"""
import json
import subprocess
import time
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Dict
import config

PROMPT_PATH = Path(__file__).parent / "prompts" / "disaster_report.md"


@dataclass
class DraftResult:
    text: str
    source: str          # "claude_cli" | "template" | "sdk"
    elapsed_sec: float
    input_hash: str
    error: str = ""


def _hash(payload: Dict) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:12]


class TemplateDrafter:
    """결정론 fallback. AI 호출 실패 시 사용."""

    def draft(self, context: Dict) -> DraftResult:
        t0 = time.time()
        alert = context["alert"]
        schools = context["affected_schools"]
        manual = context["manual"]
        lines = [
            f"[보고] {alert['type']} 영향학교 현황 및 대응(안)",
            f"발신: 안전 담당부서 / 수신: 교육감",
            f"일시: {alert['issued_at']}",
            "",
            "■ 특보 요약",
            f"- {alert['type']} {alert['level']} (대상권역: {', '.join(alert['regions'])})",
            f"- {alert['summary']}",
            "",
            "■ 영향권 학교 목록",
        ]
        for s in schools:
            lines.append(f"- {s['id']} ({s['region']}, {s['level']}급) 영향도 {s.get('grade','-')}")
        lines += ["", "■ 즉시 조치", *[f"- {x}" for x in manual.get("response", [])]]
        lines += ["", "■ 후속 조치", f"- {manual.get('reporting','')}"]
        lines += ["", "본 초안은 AI 보조판단 결과이며 최종 판단·결재는 안전 담당자가 수행합니다."]
        return DraftResult(
            text="\n".join(lines),
            source="template",
            elapsed_sec=round(time.time() - t0, 3),
            input_hash=_hash(context),
        )


class ClaudeCliDrafter:
    """`claude -p` subprocess 어댑터."""

    def __init__(self, fallback: TemplateDrafter | None = None):
        self.fallback = fallback or TemplateDrafter()

    def draft(self, context: Dict) -> DraftResult:
        t0 = time.time()
        try:
            prompt = PROMPT_PATH.read_text(encoding="utf-8").replace(
                "{context_json}", json.dumps(context, ensure_ascii=False, indent=2)
            )
            proc = subprocess.run(
                [config.CLAUDE_CLI_PATH, "-p", prompt],
                capture_output=True, text=True,
                timeout=config.AI_DRAFT_TIMEOUT,
                encoding="utf-8",
            )
            if proc.returncode != 0 or not proc.stdout.strip():
                raise RuntimeError(f"claude CLI failed: {proc.stderr[:200]}")
            return DraftResult(
                text=proc.stdout.strip(),
                source="claude_cli",
                elapsed_sec=round(time.time() - t0, 3),
                input_hash=_hash(context),
            )
        except Exception as e:
            result = self.fallback.draft(context)
            result.error = f"cli_failed:{type(e).__name__}:{str(e)[:120]}"
            return result


def get_drafter():
    return ClaudeCliDrafter()
