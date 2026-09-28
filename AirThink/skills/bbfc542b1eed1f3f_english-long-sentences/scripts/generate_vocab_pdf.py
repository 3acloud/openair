import os
import re
import subprocess
import sys

def parse_vocab(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = [line.strip() for line in content.splitlines() if line.strip()]
    
    items = []
    current_item = None
    
    # Filter out noise lines
    clean_lines = []
    for line in lines:
        if line in ["表格", "复制", "序号单词/短语释义"]:
            continue
        if "单词表" in line and ("（" in line or "(" in line):
            continue
        clean_lines.append(line)
        
    i = 0
    while i < len(clean_lines):
        line = clean_lines[i]
        
        # Check if line is a number
        if re.match(r'^\d+$', line):
            # Start of a new item
            if current_item:
                items.append(current_item)
            
            current_item = {
                'num': line,
                'word': '',
                'def': ''
            }
            i += 1
            if i < len(clean_lines):
                current_item['word'] = clean_lines[i]
                i += 1
            if i < len(clean_lines):
                current_item['def'] = clean_lines[i]
                i += 1
        else:
            i += 1
            
    if current_item:
        items.append(current_item)
        
    return items

def generate_html(items, template_path, output_path):
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()
        
    rows_html = ""
    for item in items:
        row = f"""
        <tr>
            <td class="num-col">{item['num']}</td>
            <td class="word-col">{item['word']}</td>
            <td class="def-col">{item['def']}</td>
        </tr>
        """
        rows_html += row
        
    html = template.replace('{{TITLE}}', '近期单词表')
    html = template.replace('{{SUBTITLE}}', '重点词汇 (1-48)')
    html = template.replace('{{YEAR}}', '2026')
    html = template.replace('{{COUNT}}', str(len(items)))
    html = template.replace('{{ROWS}}', rows_html)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
        
    return True

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_file = os.path.join(base_dir, 'vocab_input.txt')
    template_file = os.path.join(base_dir, 'assets', 'vocab_list_template.html')
    output_html = os.path.join(base_dir, 'vocab_list.html')
    output_pdf = os.path.join(base_dir, 'vocab_list.pdf')
    script_pdf = os.path.join(base_dir, 'scripts', 'html_to_pdf.py')
    
    print(f"Reading from: {input_file}")
    if not os.path.exists(input_file):
        print("Error: Input file not found!")
        return

    print("Parsing vocabulary...")
    items = parse_vocab(input_file)
    print(f"Found {len(items)} items.")
    
    print("Generating HTML...")
    generate_html(items, template_file, output_html)
    
    print("Converting to PDF...")
    try:
        subprocess.run(['python', script_pdf, output_html, output_pdf], check=True)
        print(f"Done! PDF saved to {output_pdf}")
    except subprocess.CalledProcessError as e:
        print(f"Error converting to PDF: {e}")

if __name__ == '__main__':
    main()
