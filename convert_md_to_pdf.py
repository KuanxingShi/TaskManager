# [AI] 2026-02-21 kxshi: 创建 Markdown 转 PDF 脚本（支持中文）
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted, Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
import re

# 注册支持中文的字体
pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))

def parse_markdown_to_pdf(md_file, pdf_file):
    """将 Markdown 文件转换为 PDF"""

    # 读取 Markdown 内容
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 创建 PDF 文档
    doc = SimpleDocTemplate(
        pdf_file,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18,
    )

    # 获取样式
    styles = getSampleStyleSheet()

    # 自定义样式（使用支持中文的字体）
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName='STSong-Light',
        fontSize=24,
        textColor=colors.HexColor('#2E3440'),
        spaceAfter=30,
        alignment=1,  # 居中
    )

    heading1_style = ParagraphStyle(
        'CustomHeading1',
        parent=styles['Heading1'],
        fontName='STSong-Light',
        fontSize=18,
        textColor=colors.HexColor('#2E3440'),
        spaceAfter=12,
        spaceBefore=12,
    )

    heading2_style = ParagraphStyle(
        'CustomHeading2',
        parent=styles['Heading2'],
        fontName='STSong-Light',
        fontSize=14,
        textColor=colors.HexColor('#3B4252'),
        spaceAfter=10,
        spaceBefore=10,
    )

    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontName='STSong-Light',
        fontSize=10,
        leading=14,
    )

    code_style = ParagraphStyle(
        'Code',
        parent=styles['Code'],
        fontName='Courier',
        fontSize=9,
        leftIndent=20,
        textColor=colors.HexColor('#4C566A'),
        backColor=colors.HexColor('#ECEFF4'),
    )

    # 存储 PDF 元素
    story = []

    # 解析 Markdown 内容
    lines = content.split('\n')
    i = 0
    in_code_block = False
    code_block = []
    in_table = False
    table_data = []

    while i < len(lines):
        line = lines[i]

        # 处理代码块
        if line.startswith('```'):
            if in_code_block:
                # 代码块结束
                code_text = '\n'.join(code_block)
                story.append(Preformatted(code_text, code_style))
                story.append(Spacer(1, 12))
                code_block = []
                in_code_block = False
            else:
                # 代码块开始
                in_code_block = True
            i += 1
            continue

        if in_code_block:
            code_block.append(line)
            i += 1
            continue

        # 处理表格
        if line.startswith('|'):
            if not in_table:
                in_table = True
                table_data = []

            # 解析表格行
            cells = [cell.strip() for cell in line.split('|')[1:-1]]

            # 跳过分隔行 (|------|)
            if not all(re.match(r'^-+$', cell) for cell in cells):
                table_data.append(cells)

            i += 1

            # 检查下一行是否还是表格
            if i >= len(lines) or not lines[i].startswith('|'):
                # 表格结束，创建表格
                if table_data:
                    t = Table(table_data)
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E5E9F0')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#2E3440')),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'STSong-Light'),
                        ('FONTSIZE', (0, 0), (-1, 0), 9),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#3B4252')),
                        ('FONTNAME', (0, 1), (-1, -1), 'STSong-Light'),
                        ('FONTSIZE', (0, 1), (-1, -1), 9),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D8DEE9')),
                    ]))
                    story.append(t)
                    story.append(Spacer(1, 12))
                    table_data = []
                in_table = False
            continue

        # 一级标题 (文档标题)
        if line.startswith('# ') and not line.startswith('## '):
            text = line[2:].strip()
            story.append(Paragraph(text, title_style))
            story.append(Spacer(1, 12))

        # 二级标题
        elif line.startswith('## ') and not line.startswith('### '):
            text = line[3:].strip()
            story.append(Paragraph(text, heading1_style))

        # 三级标题
        elif line.startswith('### '):
            text = line[4:].strip()
            story.append(Paragraph(text, heading2_style))

        # 列表项
        elif line.startswith('- '):
            text = line[2:].strip()
            # 处理加粗
            text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
            # 处理行内代码
            text = re.sub(r'`(.*?)`', r'<font face="Courier" color="#4C566A">\1</font>', text)
            story.append(Paragraph('• ' + text, normal_style))

        # 普通段落
        elif line.strip():
            text = line.strip()
            # 处理加粗
            text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
            # 处理行内代码
            text = re.sub(r'`(.*?)`', r'<font face="Courier" color="#4C566A">\1</font>', text)
            story.append(Paragraph(text, normal_style))
            story.append(Spacer(1, 6))

        # 空行
        else:
            story.append(Spacer(1, 12))

        i += 1

    # 生成 PDF
    doc.build(story)
    print(f"PDF generated: {pdf_file}")

if __name__ == "__main__":
    parse_markdown_to_pdf(
        "c:\\projects\\TaskManager\\README.md",
        "c:\\projects\\TaskManager\\README.pdf"
    )
