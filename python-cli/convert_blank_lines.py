from converter_core import add_editor_blank_lines, run_cli


run_cli(
    usage_message="사용법: python3 convert_blank_lines.py ./post.md",
    post_processors=[
        add_editor_blank_lines,
    ],
)
