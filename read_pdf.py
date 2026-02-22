# [AI] 2026-02-21 kxshi: 创建 PDF 读取脚本
import pdfplumber

def read_pdf(pdf_file, output_file=None):
    """读取 PDF 文件内容"""
    result = []
    result.append(f"=== Reading PDF: {pdf_file} ===\n")

    with pdfplumber.open(pdf_file) as pdf:
        result.append(f"Total pages: {len(pdf.pages)}\n")

        for i, page in enumerate(pdf.pages, 1):
            result.append(f"\n--- Page {i} ---\n")
            text = page.extract_text()
            result.append(text)
            result.append("\n")

    full_text = '\n'.join(result)

    # 输出到文件
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(full_text)
        print(f"Content saved to: {output_file}")
    else:
        print(full_text)

    return full_text

if __name__ == "__main__":
    read_pdf("c:\\projects\\TaskManager\\README.pdf", "c:\\projects\\TaskManager\\README_extracted.txt")
