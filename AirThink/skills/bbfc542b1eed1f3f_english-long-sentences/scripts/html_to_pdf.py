# -*- coding: utf-8 -*-
"""HTML转PDF生成器（共享内核薄封装）

将HTML文件通过 Playwright Chromium 转换为PDF。
实际渲染逻辑由 .trae/skills/common/pdf_renderer.py 统一实现。

用法:
    python html_to_pdf.py <输入html文件路径> [输出pdf路径]

示例:
    python html_to_pdf.py test.html
    python html_to_pdf.py test.html output.pdf
"""
import sys
from pathlib import Path

_COMMON = Path(__file__).resolve().parents[2] / "common"
if str(_COMMON) not in sys.path:
    sys.path.insert(0, str(_COMMON))
from pdf_renderer import render_html_to_pdf  # noqa: E402


def html_to_pdf(input_html, output_pdf=None):
    """将HTML文件转换为PDF。"""
    return render_html_to_pdf(input_html, output_pdf)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    success = html_to_pdf(input_file, output_file)
    sys.exit(0 if success else 1)
