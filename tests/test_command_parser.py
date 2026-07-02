from harness.command_parser import (
    MIXED_SUBMIT,
    MULTIPLE_BLOCKS,
    NO_BLOCK,
    SUBMIT_COMMAND,
    parse_reply,
)


def test_single_bash_block():
    parsed = parse_reply("I'll list files first.\n```bash\nls -la /app\n```\n")
    assert parsed.command == "ls -la /app"
    assert not parsed.submitted
    assert parsed.error is None


def test_plain_fence_and_multiline_command():
    parsed = parse_reply("```\nfor f in *.txt; do\n  cat \"$f\"\ndone\n```")
    assert parsed.command == 'for f in *.txt; do\n  cat "$f"\ndone'


def test_no_block_is_error():
    parsed = parse_reply("The task looks done to me!")
    assert parsed.command is None
    assert parsed.error == NO_BLOCK


def test_empty_block_is_error():
    parsed = parse_reply("```bash\n\n```")
    assert parsed.error == NO_BLOCK


def test_multiple_blocks_is_error():
    parsed = parse_reply("```bash\nls\n```\nthen\n```bash\npwd\n```")
    assert parsed.command is None
    assert parsed.error == MULTIPLE_BLOCKS


def test_submit_detected():
    parsed = parse_reply(f"All checks pass.\n```bash\n{SUBMIT_COMMAND}\n```")
    assert parsed.submitted


def test_command_mentioning_submit_marker_midline_is_not_submit():
    parsed = parse_reply(f'```bash\ngrep -r "{SUBMIT_COMMAND}" .\n```')
    assert not parsed.submitted
    assert parsed.error is None


def test_submit_first_then_commands_is_mixed_error():
    # The exact shape that silently ate toy-pipeline rollouts 1 and 3:
    # submit marker on line 1, real commands after it.
    parsed = parse_reply(f"```bash\n{SUBMIT_COMMAND}\nmkdir -p /output\n```")
    assert not parsed.submitted
    assert parsed.command is None
    assert parsed.error == MIXED_SUBMIT


def test_commands_then_submit_last_is_mixed_error():
    parsed = parse_reply(f"```bash\nmkdir -p /output\n{SUBMIT_COMMAND}\n```")
    assert not parsed.submitted
    assert parsed.error == MIXED_SUBMIT


def test_command_block_plus_submit_block_is_mixed_error():
    parsed = parse_reply(f"```bash\nls\n```\ndone!\n```bash\n{SUBMIT_COMMAND}\n```")
    assert not parsed.submitted
    assert parsed.error == MIXED_SUBMIT


def test_submit_with_surrounding_prose_still_submits():
    parsed = parse_reply(f"Everything checks out.\n```bash\n{SUBMIT_COMMAND}\n```\nDone.")
    assert parsed.submitted
