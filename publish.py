#!/usr/bin/env python3
"""
Simple notebook publishing script for workshops.
Processes notebooks with metadata and solution-tagged cells.
"""

import json
from pathlib import Path
import zipfile
from glob import glob
import yaml
import re
import shutil
import subprocess
import sys
import argparse
import os
import fnmatch
try:
    import markdown
except ImportError:
    print("Warning: 'markdown' package not installed. Install with: pip install markdown")
    markdown = None

def get_notebook_metadata(notebook):
    """Extract workshop metadata from notebook."""
    return notebook.get('metadata', {}).get('workshop', {})

def extract_markdown_frontmatter(content):
    """Extract YAML frontmatter from markdown content."""
    pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
    match = re.match(pattern, content, re.DOTALL)
    
    if match:
        yaml_content = match.group(1)
        markdown_content = match.group(2)
        try:
            frontmatter = yaml.safe_load(yaml_content)
            return frontmatter, markdown_content
        except:
            print(f"Warning: Invalid YAML frontmatter")
            return {}, content
    return {}, content

def generate_toc_from_markdown(markdown_content, has_useful_links=False):
    """Generate a table of contents from second-level headers (##) in markdown content."""
    # Find all second-level headers
    header_pattern = r'^## (.+)$'
    headers = re.findall(header_pattern, markdown_content, re.MULTILINE)
    
    # Add Useful Links to the beginning if it exists
    if has_useful_links:
        headers = ["Useful Links"] + headers
    
    if not headers:
        return ""
    
    # Build TOC
    toc_lines = ["## Table of Contents\n"]
    for header in headers:
        # Create anchor link - remove special characters and convert spaces to hyphens
        anchor = re.sub(r'[^\w\s-]', '', header).strip().lower().replace(' ', '-')
        toc_lines.append(f"- [{header}](#{anchor})")
    
    return "\n".join(toc_lines) + "\n"

def markdown_to_html(content, title=""):
    """Convert markdown to HTML with basic styling."""
    if markdown:
        html_content = markdown.markdown(content, extensions=['extra', 'codehilite', 'toc'])
    else:
        # Fallback: just wrap in pre tags if markdown not available
        html_content = f"<pre>{content}</pre>"
    
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title}</title>
    <style>
        body {{
            max-width: 800px;
            margin: 40px auto;
            padding: 0 20px;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            font-size: 16px;
            padding-bottom: 5em;
        }}
        h1, h3, h4 {{ margin-top: 2em; }}
        h2 {{
            position: sticky;
            top: 0;
            background: white;
            padding-top: 2em;
            padding-bottom: 0.5em;
            z-index: 100;
            border-bottom: 2px solid #eee;
        }}
        /* Give the first h2 (Table of Contents) less top margin */
        h2:first-of-type {{
            margin-top: 1em;
            padding-top: 1em;
        }}
        h3 a {{
            text-decoration: none;
        }}
        h3 a:hover {{
            text-decoration: underline;
        }}
        p {{
            margin: 1em 0;
        }}
        code {{ 
            background: #f4f4f4; 
            padding: 2px 4px; 
            border-radius: 3px;
            font-family: Consolas, Monaco, monospace;
        }}
        pre {{ 
            background: #f4f4f4; 
            padding: 1em; 
            border-radius: 5px; 
            overflow-x: auto;
        }}
        pre code {{ background: none; padding: 0; }}
        a {{ color: #0066cc; }}
        img {{
            display: block;
            max-width: 80%;
            height: auto;
            margin: 1em auto;
            border: solid 1px #999;
        }}
        blockquote {{
            border-left: solid lightblue 20px;
            margin-left: 4em;
            padding-left: 1em;
            color: #999;
        }}
        video {{
            display: block;
            max-width: 80%;
            height: auto;
            margin: 1em auto;
            border: solid 1px #999;
        }}
        .download-box {{
            background: #e8f4f8;
            padding: 1em;
            border-radius: 5px;
            margin: 1em 0;
        }}
        ul {{
            list-style-type: disc;
            padding-left: 2em;
            margin: 0.5em 0;
        }}
        li {{
            margin: 0.3em 0;
        }}
        .section-header {{
            margin-top: 2em;
            margin-bottom: 1em;
            padding-bottom: 0.5em;
            border-bottom: 2px solid #eee;
        }}
        .resource-buttons {{
            margin: 1em 0;
            display: flex;
            flex-wrap: wrap;
            gap: 0.5em;
        }}
        .resource-button {{
            display: inline-block;
            padding: 0.4em 0.8em;
            background: #f0f0f0;
            border: 1px solid #ddd;
            border-radius: 4px;
            text-decoration: none;
            color: #333;
            font-size: 0.9em;
            transition: all 0.2s;
        }}
        .resource-button:hover {{
            background: #e0e0e0;
            border-color: #ccc;
        }}
        .resource-button.primary {{
            background: #e3f2fd;
            color: #1565c0;
            border-color: #90caf9;
        }}
        .resource-button.primary:hover {{
            background: #bbdefb;
            border-color: #64b5f6;
        }}
        .resource-button.completed {{
            background: #e8f5e9;
            color: #2e7d32;
            border-color: #a5d6a7;
        }}
        .resource-button.completed:hover {{
            background: #c8e6c9;
            border-color: #81c784;
        }}
        .data-download {{
            margin: 0.5em 0;
            font-size: 0.9em;
        }}
        .download-links {{
            margin: 0.5em 0;
            line-height: 1.8;
        }}
        .download-links a {{
            color: #1976d2;
            text-decoration: none;
        }}
        .download-links a:hover {{
            text-decoration: underline;
        }}
        p:last {{
            margin-bottom: 0;
            margin-top: 5em;
        }}
    </style>
</head>
<body>
{html_content}
</body>
</html>"""

def load_config():
    """Load workshop configuration from YAML file."""
    config_path = Path('workshop-config.yaml')
    if not config_path.exists():
        print("Warning: workshop-config.yaml not found, using defaults")
        return {
            'github_repo': 'jsoma/natural-pdf-workshop',
            'github_branch': 'main',
            'title': 'Workshop',
            'description': '',
            'output_dir': 'docs'
        }
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def _deep_merge(base, override):
    """Recursively merge override into base and return a new dict."""
    if not isinstance(base, dict):
        base = {}
    result = dict(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(result.get(k), dict):
            result[k] = _deep_merge(result.get(k, {}), v)
        else:
            # For lists and scalars, override entirely by default
            result[k] = v
    return result

def _iter_metadata_overrides(config):
    """Yield (pattern, values) from config metadata overrides.

    Supports these shapes:
    - metadata_overrides: [{ pattern: "path/glob", values: {...} }, ...]
    - metadata:            [{ pattern: "...", values: {...} }, ...]
    - metadata:            { "path/glob": {...}, ... }
    - metadata:            [{ file|match: "...", merge|values: {...} }]
    """
    md = config.get('metadata_overrides') or config.get('metadata')
    if not md:
        return
    if isinstance(md, dict):
        for pat, vals in md.items():
            if isinstance(vals, dict):
                yield pat, vals
    elif isinstance(md, list):
        for item in md:
            if not isinstance(item, dict):
                continue
            pattern = item.get('pattern') or item.get('file') or item.get('match')
            values = item.get('values') or item.get('merge')
            if not values:
                # allow inline style: { pattern: "...", title: "...", data_files: [...] }
                values = {k: v for k, v in item.items() if k not in ('pattern', 'file', 'match')}
            if pattern and isinstance(values, dict):
                yield pattern, values

def apply_metadata_overrides(file_path: Path, meta: dict, config: dict) -> dict:
    """Apply any matching metadata overrides based on relative path glob patterns.

    Returns a new merged metadata dict.
    """
    try:
        rel = file_path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except Exception:
        rel = file_path.as_posix()

    merged = dict(meta or {})
    for pattern, values in _iter_metadata_overrides(config) or []:
        # Support both repo-root relative and section-relative globs
        if fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(file_path.name, pattern):
            merged = _deep_merge(merged, values)
    return merged

def create_setup_cells(zip_name, config, install_packages="pandas natural_pdf tqdm", section_folder=None, for_codespaces=False):
    """Create setup cells that work in Colab, Jupyter, etc.

    Returns a list of cells (install cell and optionally download cell).
    If for_codespaces=True, returns empty list since setup is not needed.
    """
    # Skip setup cells entirely for Codespaces (everything is pre-installed)
    if for_codespaces:
        return []

    cells = []
    github_repo = config['github_repo']
    github_branch = config.get('github_branch', 'main')
    output_dir = config.get('output_dir', 'docs')

    # Create install cell if packages are specified
    if install_packages:
        install_lines = ["# Install required packages\n"]
        if isinstance(install_packages, str):
            # If it's a string, split it into a list
            packages = install_packages.split()
        elif isinstance(install_packages, list):
            packages = install_packages
        else:
            packages = []

        # Install each package separately using %pip
        for package in packages:
            if package.strip():  # Only if package name is not empty
                install_lines.append(f"%pip install --upgrade --quiet {package.strip()}\n")

        if packages:
            cells.append({
                "cell_type": "code",
                "metadata": {},
                "source": install_lines,
                "execution_count": None,
                "outputs": []
            })

    # Create download cell if zip file is specified
    if zip_name:
        download_lines = [
            "# Download and extract data files\n",
            "import os\n",
            "import urllib.request\n",
            "import zipfile\n",
            "\n"
        ]

        # URL encode the zip name for Colab compatibility
        import urllib.parse
        encoded_zip_name = urllib.parse.quote(zip_name)

        # Include section folder in the URL if provided
        if section_folder:
            encoded_zip_url = f"{output_dir}/{section_folder}/{encoded_zip_name}"
        else:
            encoded_zip_url = f"{output_dir}/{encoded_zip_name}"

        download_lines.extend([
            f"url = 'https://github.com/{github_repo}/raw/{github_branch}/{encoded_zip_url}'\n",
            "print(f'Downloading data from {url}...')\n",
            f"urllib.request.urlretrieve(url, '{zip_name}')\n",
            "\n",
            f"print('Extracting {zip_name}...')\n",
            f"with zipfile.ZipFile('{zip_name}', 'r') as zip_ref:\n",
            "    zip_ref.extractall('.')\n",
            "\n",
            f"os.remove('{zip_name}')\n",
            "print('✓ Data files extracted!')"
        ])

        cells.append({
            "cell_type": "code",
            "metadata": {},
            "source": download_lines,
            "execution_count": None,
            "outputs": []
        })

    return cells

def process_notebook(notebook_path, output_dir, config, section_cfg=None):
    """Process a single notebook and return info for index."""
    with open(notebook_path, 'r') as f:
        notebook = json.load(f)

    metadata = get_notebook_metadata(notebook)
    # Merge config-provided metadata overrides for this file
    metadata = apply_metadata_overrides(notebook_path, metadata, config)
    # (No inheritance of section data_files here - section-level zips are created
    # separately in main() and shown on the index page.)
    if not metadata:
        print(f"Skipping {notebook_path} - no workshop metadata")
        return None
    
    base_name = notebook_path.stem
    notebook_dir = notebook_path.parent
    
    # Create complete version (ANSWERS)
    complete_nb = notebook.copy()
    
    # Set kernel to python3 for both versions
    if 'metadata' not in complete_nb:
        complete_nb['metadata'] = {}
    if 'kernelspec' not in complete_nb['metadata']:
        complete_nb['metadata']['kernelspec'] = {}
    complete_nb['metadata']['kernelspec']['name'] = 'python3'
    complete_nb['metadata']['kernelspec']['display_name'] = 'Python 3'
    complete_nb['metadata']['kernelspec']['language'] = 'python'
    
    # Create exercise version
    exercise_nb = json.loads(json.dumps(complete_nb))  # Deep copy

    # Persist merged workshop metadata back into both notebook variants
    for nb in (complete_nb, exercise_nb):
        nb.setdefault('metadata', {})
        nb['metadata'].setdefault('workshop', {})
        nb['metadata']['workshop'] = metadata
    
    # Process cells for exercise version
    for i, cell in enumerate(exercise_nb['cells']):
        # Clear outputs for all code cells (keep the source code)
        if cell['cell_type'] == 'code':
            cell['outputs'] = []
            cell['execution_count'] = None
        
        # Replace solution-tagged cells with empty cells
        if cell.get('metadata', {}).get('tags') and 'solution' in cell['metadata']['tags']:
            exercise_nb['cells'][i] = {
                "cell_type": "code",
                "metadata": {},
                "source": [],
                "execution_count": None,
                "outputs": []
            }
    
    # Add setup cells if data files or install packages are specified
    # (Skip for Codespaces branch)
    setup_cells = []  # Initialize empty list
    if metadata.get('data_files') or metadata.get('install'):
        zip_name = f"{base_name}-data.zip" if metadata.get('data_files') else None
        install_packages = metadata.get('install', 'pandas natural_pdf tqdm')
        setup_cells = create_setup_cells(zip_name, config, install_packages, section_folder=notebook_dir.name)

        # Insert setup cells at the beginning (in reverse order to maintain order)
        for cell in reversed(setup_cells):
            complete_nb['cells'].insert(0, cell)
            exercise_nb['cells'].insert(0, cell)
    
    # Write output files
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create output subdirectory matching the source structure
    output_subdir = output_dir / notebook_dir.name
    output_subdir.mkdir(parents=True, exist_ok=True)

    # Copy any referenced files (PDFs, images) to the section output subdir
    find_and_copy_referenced_files(notebook, notebook_dir, output_subdir)

    # Handle slides if specified (item-specific or section-level)
    slide_file = metadata.get('slides')
    if slide_file:
        # Add simple markdown cell with slide link after setup cells
        slide_link_cell = {
            "cell_type": "markdown",
            "metadata": {},
            "source": [f"**Slides:** [{Path(slide_file).name}](./{Path(slide_file).name})"]
        }
        # Insert after all setup cells
        insert_pos = len(setup_cells)
        complete_nb['cells'].insert(insert_pos, slide_link_cell)
        exercise_nb['cells'].insert(insert_pos, slide_link_cell)

        # Copy slide file to section output folder
        source_pdf = notebook_dir / slide_file
        if not source_pdf.exists():
            # Try as absolute path from project root
            source_pdf = Path(slide_file)
        if source_pdf.exists():
            dest_pdf = output_subdir / Path(slide_file).name
            if not dest_pdf.exists():
                shutil.copy2(source_pdf, dest_pdf)
                print(f"  → Copied slide file: {slide_file}")
        else:
            print(f"\n❌ ERROR: Slide file not found: {slide_file}")
            print(f"   Looked in: {notebook_dir / slide_file}")
            print(f"   Also tried: {Path(slide_file)}")
            sys.exit(1)

    # Create data zip in the section folder if data files are specified
    if metadata.get('data_files'):
        zip_name = f"{base_name}-data.zip"
        create_data_zip(metadata['data_files'], output_subdir / zip_name, notebook_dir)

    # Exercise version keeps original name
    with open(output_subdir / f"{base_name}.ipynb", 'w') as f:
        json.dump(exercise_nb, f, indent=1)
    print(f"✓ Created {output_subdir.relative_to(output_dir)}/{base_name}.ipynb")

    # Complete version gets -ANSWERS suffix
    with open(output_subdir / f"{base_name}-ANSWERS.ipynb", 'w') as f:
        json.dump(complete_nb, f, indent=1)
    print(f"✓ Created {output_subdir.relative_to(output_dir)}/{base_name}-ANSWERS.ipynb")
    
    # Return info for index
    return {
        'name': base_name,
        'title': metadata.get('title', base_name),
        'description': metadata.get('description', ''),
        'exercise_file': f"{notebook_dir.name}/{base_name}.ipynb",
        'answers_file': f"{notebook_dir.name}/{base_name}-ANSWERS.ipynb",
        'data_file': f"{notebook_dir.name}/{base_name}-data.zip" if metadata.get('data_files') else None,
        'section': notebook_dir.name,
        'order': metadata.get('order', None),
        'links': metadata.get('links', None),
        'slides': metadata.get('slides', None)
    }

def create_data_zip(data_patterns, zip_path, base_dir):
    """Create a zip file with files matching the patterns, relative to base_dir."""
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        added_files = set()
        
        for pattern in data_patterns:
            # Resolve pattern relative to notebook directory
            full_pattern = str(base_dir / pattern)
            matches = glob(full_pattern, recursive=True)
            
            if not matches:
                print(f"  Warning: No files match pattern '{pattern}' in {base_dir}")
            
            for file_path in matches:
                file_path = Path(file_path)
                # Calculate the archive name relative to the notebook's directory
                try:
                    arcname = file_path.relative_to(base_dir)
                except ValueError:
                    # If file is outside notebook dir, use full relative path
                    arcname = file_path
                
                if str(file_path) not in added_files:
                    zipf.write(file_path, str(arcname))
                    added_files.add(str(file_path))
        
        print(f"✓ Created {zip_path.name} with {len(added_files)} files")

def find_and_copy_referenced_files(notebook, notebook_dir, output_dir):
    """Find files referenced in markdown cells and copy them to output."""
    copied_files = []
    
    # Regex patterns for finding file references
    patterns = [
        r'\[.*?\]\(([^)]+\.(?:pdf|png|jpg|jpeg|gif|svg))\)',  # Markdown links
        r'<img.*?src=["\']([^"\']+\.(?:png|jpg|jpeg|gif|svg))["\']',  # HTML img tags
        r'!\[.*?\]\(([^)]+\.(?:png|jpg|jpeg|gif|svg))\)',  # Markdown images
    ]
    
    for cell in notebook.get('cells', []):
        if cell['cell_type'] == 'markdown':
            content = ''.join(cell.get('source', []))
            
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    # Skip URLs
                    if match.startswith('http://') or match.startswith('https://'):
                        continue
                    
                    # Resolve the file path relative to the notebook
                    source_file = notebook_dir / match
                    if source_file.exists():
                        # Copy to output directory
                        dest_file = output_dir / match
                        dest_file.parent.mkdir(parents=True, exist_ok=True)
                        
                        if not dest_file.exists():
                            shutil.copy2(source_file, dest_file)
                            copied_files.append(match)
                            print(f"  → Copied referenced file: {match}")
    
    return copied_files

def copy_markdown_referenced_files(content, markdown_dir, output_dir):
    """Find files referenced in markdown content and copy them to output."""
    copied_files = []
    
    # Regex patterns for finding file references
    patterns = [
        r'\[.*?\]\(([^)]+\.(?:pdf|png|jpg|jpeg|gif|svg|mp4|webm|mov))\)',  # Markdown links
        r'<img.*?src=["\']([^"\']+\.(?:png|jpg|jpeg|gif|svg))["\']',  # HTML img tags
        r'!\[.*?\]\(([^)]+\.(?:png|jpg|jpeg|gif|svg))\)',  # Markdown images
        r'<source.*?src=["\']([^"\']+\.(?:mp4|webm|mov))["\']',  # HTML video sources
        r'<video.*?src=["\']([^"\']+\.(?:mp4|webm|mov))["\']',  # HTML video src
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            # Skip URLs
            if match.startswith('http://') or match.startswith('https://'):
                continue
            
            # Resolve the file path relative to the markdown file
            source_file = markdown_dir / match
            if source_file.exists():
                # Copy to output directory
                dest_file = output_dir / match
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                
                if not dest_file.exists():
                    shutil.copy2(source_file, dest_file)
                    copied_files.append(match)
                    print(f"  → Copied referenced file: {match}")
            else:
                print(f"  ⚠ Referenced file not found: {match}")
    
    return copied_files

def create_slide_thumbnail(pdf_path, output_dir, width=800):
    """Create a thumbnail of the first page of a PDF."""
    pdf_name = pdf_path.stem
    thumb_name = f"{pdf_name}-thumb.png"
    thumb_path = output_dir / thumb_name
    
    if thumb_path.exists():
        return thumb_name
    
    try:
        # Try using ImageMagick's convert command
        cmd = [
            'convert',
            '-density', '150',
            f'{pdf_path}[0]',  # First page only
            '-resize', f'{width}x',
            '-quality', '85',
            str(thumb_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  → Created slide thumbnail: {thumb_name}")
            return thumb_name
    except:
        pass
    
    # If ImageMagick fails, try pdftoppm
    try:
        cmd = [
            'pdftoppm',
            '-f', '1',
            '-l', '1',
            '-png',
            '-r', '150',
            '-singlefile',
            str(pdf_path),
            str(output_dir / pdf_name)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            # pdftoppm creates a file with .png extension
            if (output_dir / f"{pdf_name}.png").exists():
                shutil.move(output_dir / f"{pdf_name}.png", thumb_path)
                print(f"  → Created slide thumbnail: {thumb_name}")
                return thumb_name
    except:
        pass
    
    print(f"  ⚠ Could not create thumbnail for {pdf_path.name} (install ImageMagick or poppler-utils)")
    return None

def convert_pptx_to_pdf(pptx_path):
    """Convert PPTX to PDF in the same directory as the source file."""
    pdf_path = pptx_path.parent / (pptx_path.stem + '.pdf')
    
    # Check if PDF exists and is newer than PPTX
    if pdf_path.exists():
        pptx_mtime = pptx_path.stat().st_mtime
        pdf_mtime = pdf_path.stat().st_mtime
        if pdf_mtime > pptx_mtime:
            print(f"  → Using existing PDF (newer than PPTX): {pdf_path.name}")
            return pdf_path
    
    # Try AppleScript on Mac (using PowerPoint)
    if sys.platform == 'darwin':  # macOS
        try:
            # Convert paths to absolute paths
            pptx_abs = str(pptx_path.resolve())
            pdf_abs = str(pdf_path.resolve())
            
            # AppleScript to convert PPTX to PDF using PowerPoint
            applescript = f'''
            tell application "Microsoft PowerPoint"
                activate
                open POSIX file "{pptx_abs}"
                delay 2
                save active presentation in POSIX file "{pdf_abs}" as save as PDF
                close active presentation
            end tell
            '''
            
            print(f"  → Converting {pptx_path.name} to PDF using PowerPoint (AppleScript)...")
            result = subprocess.run(['osascript', '-e', applescript], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and pdf_path.exists():
                print(f"  → Converted {pptx_path.name} to PDF")
                return pdf_path
            else:
                if result.stderr:
                    print(f"  ⚠ AppleScript error: {result.stderr}")
                if result.stdout:
                    print(f"  ⚠ AppleScript output: {result.stdout}")
        except subprocess.TimeoutExpired:
            print(f"  ⚠ PowerPoint conversion timed out")
        except Exception as e:
            print(f"  ⚠ AppleScript conversion failed: {e}")
    
    # Try pptxtopdf package on Windows
    if sys.platform == 'win32':
        try:
            from pptxtopdf import convert
            print(f"  → Converting {pptx_path.name} to PDF using pptxtopdf...")
            # Convert the directory containing the PPTX file
            convert(str(pptx_path.parent), str(pptx_path.parent))
            if pdf_path.exists():
                print(f"  → Converted {pptx_path.name} to PDF")
                return pdf_path
        except ImportError as ie:
            print(f"  ⚠ pptxtopdf not installed: {ie}")
        except Exception as e:
            print(f"  ⚠ pptxtopdf conversion failed: {e}")
    
    # Fallback to LibreOffice/soffice (most common on Linux/Mac)
    try:
        cmd = [
            'soffice',
            '--headless',
            '--convert-to', 'pdf',
            '--outdir', str(pptx_path.parent),
            str(pptx_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and pdf_path.exists():
            print(f"  → Converted {pptx_path.name} to PDF using LibreOffice")
            return pdf_path
    except:
        pass
    
    # Try unoconv (alternative LibreOffice interface)
    try:
        cmd = [
            'unoconv',
            '-f', 'pdf',
            '-o', str(pdf_path),
            str(pptx_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and pdf_path.exists():
            print(f"  → Converted {pptx_path.name} to PDF using unoconv")
            return pdf_path
    except:
        pass
    
    print(f"  ❌ Could not convert {pptx_path.name} to PDF")
    print(f"     Install: pip install pptxtopdf (requires PowerPoint)")
    print(f"     Or: brew install --cask libreoffice (Mac/Linux)")
    return None

def prepare_codespaces_build(config) -> Path | None:
    """Create the build-codespaces directory with notebooks, data, and environment files.

    - Copies each section folder into build-codespaces/<folder> (skips __pycache__ and .ipynb_checkpoints)
    - Writes requirements.txt from config.codespaces.requirements
    - Copies _devcontainer-template to .devcontainer if present
    Returns the Path to the build directory or None if nothing created.
    """
    try:
        from pathlib import Path
        import shutil
    except Exception:
        return None

    build_dir = Path('build-codespaces')
    # Reset build directory
    if build_dir.exists():
        try:
            shutil.rmtree(build_dir)
        except Exception:
            pass
    build_dir.mkdir(parents=True, exist_ok=True)

    # Requirements
    reqs = (config.get('codespaces') or {}).get('requirements')
    if isinstance(reqs, list) and reqs:
        try:
            (build_dir / 'requirements.txt').write_text("\n".join(reqs) + "\n", encoding='utf-8')
            print("  → Wrote build-codespaces/requirements.txt")
        except Exception as e:
            print(f"  ⚠ Failed to write requirements.txt: {e}")

    # Devcontainer
    dev_src = Path('_devcontainer-template')
    if dev_src.exists() and dev_src.is_dir():
        try:
            shutil.copytree(dev_src, build_dir / '.devcontainer')
            print("  → Copied .devcontainer configuration for Codespaces")
        except Exception as e:
            print(f"  ⚠ Failed to copy devcontainer: {e}")

    # Copy section folders
    copied_any = False
    for section in config.get('sections', []) or []:
        # Skip draft sections
        if isinstance(section, dict) and section.get('draft', False):
            print(f"  → Skipping draft section in Codespaces build: {section.get('title', section.get('folder'))}")
            continue
        folder = section.get('folder') if isinstance(section, dict) else section
        if not folder:
            continue
        src = Path(folder)
        if not src.exists() or not src.is_dir():
            continue
        dest = build_dir / src.name
        try:
            shutil.copytree(
                src,
                dest,
                ignore=shutil.ignore_patterns('__pycache__', '.ipynb_checkpoints')
            )
            copied_any = True
            print(f"  → Copied section: {folder}")
        except Exception as e:
            print(f"  ⚠ Failed to copy section {folder}: {e}")

    # Add a README if missing
    readme = build_dir / 'README.md'
    if not readme.exists():
        try:
            readme.write_text(
                "# Codespaces Workspace\n\n"
                "This branch contains notebooks and data for GitHub Codespaces.\n\n"
                "- Open in Codespaces using the workshop link.\n"
                "- Python packages are listed in requirements.txt.\n"
                , encoding='utf-8')
        except Exception:
            pass

    return build_dir if copied_any else build_dir

def generate_slide_embed(slide_file, notebook_dir, output_dir, item_type='notebook', section_folder=None):
    """Generate HTML for slide embedding with lazy loading."""
    # Find the slide file
    source_file = notebook_dir / slide_file
    if not source_file.exists():
        # Try as absolute path from project root
        source_file = Path(slide_file)
        if not source_file.exists():
            print(f"\n❌ ERROR: Slide file not found: {slide_file}")
            print(f"   Looked in: {notebook_dir / slide_file}")
            print(f"   Also tried: {Path(slide_file)}")
            sys.exit(1)

    # Determine the actual output directory (with section folder if provided)
    if section_folder and item_type == 'index':
        actual_output_dir = output_dir / section_folder
        actual_output_dir.mkdir(parents=True, exist_ok=True)
        # Update paths to be relative to section folder
        slide_file_path = f"{section_folder}/{Path(slide_file).name}"
    else:
        actual_output_dir = output_dir
        slide_file_path = Path(slide_file).name
    
    # Handle PPTX files by converting to PDF
    if source_file.suffix.lower() == '.pptx':
        converted_pdf = convert_pptx_to_pdf(source_file)
        if converted_pdf:
            source_pdf = converted_pdf
            pdf_filename = converted_pdf.name
        else:
            # Conversion failed - copy PPTX for download only
            dest_file = actual_output_dir / Path(slide_file).name
            if not dest_file.exists():
                shutil.copy2(source_file, dest_file)
                print(f"  → Copied PPTX file: {slide_file}")

            # Return download-only box (no embed)
            return f'''
<div class="download-box">
    <strong>Slides:</strong> <a href="./{slide_file_path}">📥 Download PowerPoint ({Path(slide_file).name})</a>
</div>
'''
    else:
        source_pdf = source_file
        pdf_filename = Path(slide_file).name

    dest_pdf = actual_output_dir / pdf_filename
    if not dest_pdf.exists():
        shutil.copy2(source_pdf, dest_pdf)
        print(f"  → Copied slide file: {slide_file}")

    # Create thumbnail in the same directory as the PDF
    thumb_name = create_slide_thumbnail(source_pdf, actual_output_dir)
    
    # Generate unique ID for this slide embed
    slide_id = f"slides-{source_pdf.stem}".replace(' ', '-').replace('.', '-')
    
    # Build the HTML with correct paths
    if thumb_name:
        thumb_path = f"{section_folder}/{thumb_name}" if section_folder and item_type == 'index' else thumb_name
        preview_html = f'<img src="./{thumb_path}" alt="First slide" style="max-width: 100%; cursor: pointer;">'
    else:
        preview_html = '<div style="background: #f0f0f0; padding: 3em; text-align: center; cursor: pointer;">📊 Click to load slides</div>'

    html = f'''
<div id="{slide_id}" class="slide-embed" style="margin: 2em 0;">
    <div class="slide-preview" onclick="loadSlides('{slide_id}', './{slide_file_path}')">
        {preview_html}
        <p style="text-align: center; margin-top: 0.5em;">
            <button style="padding: 0.5em 1em; background: #1976d2; color: white; border: none; border-radius: 4px; cursor: pointer;">
                📊 View Slides
            </button>
            <a href="./{slide_file_path}" download style="margin-left: 1em;">📥 Download PDF</a>
        </p>
    </div>
    <div class="slide-container" style="display: none;">
        <embed src="./{slide_file_path}" type="application/pdf" style="width: 100%; height: 600px; border: 1px solid #ddd;">
    </div>
</div>

<script>
function loadSlides(id, src) {{
    const container = document.querySelector(`#${{id}} .slide-container`);
    const preview = document.querySelector(`#${{id}} .slide-preview`);
    container.style.display = 'block';
    preview.style.display = 'none';
}}
</script>
'''
    
    return html

def process_markdown(markdown_path, output_dir, config, section_cfg=None):
    """Process a markdown file with frontmatter and return info for index."""
    with open(markdown_path, 'r') as f:
        content = f.read()

    frontmatter, markdown_content = extract_markdown_frontmatter(content)
    if not frontmatter:
        # Proceed with empty frontmatter to allow config overrides to apply
        frontmatter = {}
    # Merge config-provided metadata overrides for this file
    frontmatter = apply_metadata_overrides(markdown_path, frontmatter, config)
    
    base_name = markdown_path.stem
    markdown_dir = markdown_path.parent
    title = frontmatter.get('title', base_name)
    
    # Create output subdirectory matching the source structure (moved up here)
    output_subdir = output_dir / markdown_dir.name
    output_subdir.mkdir(parents=True, exist_ok=True)

    # Copy referenced files (images, videos, etc) from markdown content
    copy_markdown_referenced_files(markdown_content, markdown_dir, output_subdir)
    
    # Create data zip only if the markdown itself declares data_files
    if frontmatter.get('data_files'):
        zip_name = f"{base_name}-data.zip"
        create_data_zip(frontmatter['data_files'], output_subdir / zip_name, markdown_dir)
    
    # Compute relative link back to main index
    try:
        index_rel = os.path.relpath((output_dir / 'index.html'), start=output_subdir)
    except Exception:
        index_rel = '../index.html'

    # Build the full content with back link and title
    full_content = f"[← Back to main page]({index_rel})\n\n# {title}\n\n"
    
    # Generate and add table of contents at the top (after title)
    has_useful_links = bool(frontmatter.get('links'))
    toc = generate_toc_from_markdown(markdown_content, has_useful_links)
    if toc:
        full_content += toc + "\n"
    
    # Add download link if data files exist
    if frontmatter.get('data_files'):
        zip_name = f"{base_name}-data.zip"
        full_content += f'<div class="download-box">\n<strong>Download files:</strong> <a href="./{zip_name}">📦 {zip_name}</a>\n</div>\n\n'
    
    # Add slides if specified
    if frontmatter.get('slides'):
        slide_html = generate_slide_embed(frontmatter['slides'], markdown_dir, output_dir, 'markdown')
        full_content += slide_html + '\n\n'
    
    # Add links section if present
    if frontmatter.get('links'):
        full_content += "## Useful Links\n\n"
        for link in frontmatter['links']:
            name = link.get('name', 'Link')
            url = link.get('url', '#')
            desc = link.get('description', '')
            if desc:
                full_content += f"- [{name}]({url}) - {desc}\n"
            else:
                full_content += f"- [{name}]({url})\n"
        full_content += "\n"
    
    full_content += markdown_content

    # Convert to HTML and save
    html_content = markdown_to_html(full_content, title)
    output_html = output_subdir / f"{base_name}.html"
    with open(output_html, 'w') as f:
        f.write(html_content)

    print(f"✓ Created {output_subdir.relative_to(output_dir)}/{base_name}.html")

    # Return info for index
    return {
        'name': base_name,
        'title': title,
        'description': frontmatter.get('description', ''),
        'html_file': f"{markdown_dir.name}/{base_name}.html",
        'data_file': f"{markdown_dir.name}/{base_name}-data.zip" if frontmatter.get('data_files') else None,
        'section': markdown_dir.name,
        'type': 'markdown',
        'order': frontmatter.get('order', None),
        'links': frontmatter.get('links', None),
        'slides': frontmatter.get('slides', None)
    }

def create_index(notebooks, config, output_dir):
    """Create index.html with links to all notebooks."""
    github_repo = config['github_repo']
    github_branch = config.get('github_branch', 'main')
    output_dir_name = config.get('output_dir', 'docs')
    
    # Group notebooks by section
    sections = {}
    section_configs = {}
    
    # Get section configurations from config
    for section_cfg in config.get('sections', []):
        if isinstance(section_cfg, dict):
            section_configs[section_cfg.get('title', section_cfg.get('folder'))] = section_cfg
    
    for nb in notebooks:
        section = nb['section']
        if section not in sections:
            sections[section] = []
        sections[section].append(nb)
    
    # Build notebooks markdown
    notebooks_md = []
    
    # Handle root-level content (slides, data_files, links)
    if config.get('slides') or config.get('data_files') or config.get('links'):
        # Add root-level slides
        if config.get('slides'):
            slide_html = generate_slide_embed(config['slides'], Path('.'), output_dir, 'index')
            notebooks_md.append(slide_html + '\n')
        
        # Add root-level data files
        if config.get('data_files'):
            zip_name = "workshop-data.zip"
            create_data_zip(config['data_files'], output_dir / zip_name, Path('.'))
            notebooks_md.append(f'<div class="download-box">\n<strong>Download files:</strong> <a href="./{zip_name}">📦 {zip_name}</a>\n</div>\n\n')
        
        # Add root-level links
        if config.get('links'):
            notebooks_md.append('## Useful Links\n\n')
            for link in config['links']:
                name = link.get('name', 'Link')
                url = link.get('url', '#')
                desc = link.get('description', '')
                if desc:
                    notebooks_md.append(f"- [{name}]({url}) - {desc}\n")
                else:
                    notebooks_md.append(f"- [{name}]({url})\n")
            notebooks_md.append('\n')
    
    # Process sections in the order they appear in config
    section_order = []
    for section_cfg in config.get('sections', []):
        if isinstance(section_cfg, dict):
            title = section_cfg.get('title', section_cfg.get('folder'))
            if title in sections:
                section_order.append(title)
    
    # Add any sections not in config at the end
    for section in sorted(sections.keys()):
        if section not in section_order:
            section_order.append(section)
    
    for section in section_order:
        section_items = sections.get(section, [])
        notebooks_md.append(f'\n## {section}\n')

        # Check if this is a draft section (all items in section would be draft placeholders)
        if section_items and len(section_items) == 1 and section_items[0].get('is_draft'):
            # This is a draft section - just show placeholder
            if section_items[0].get('description'):
                notebooks_md.append(f"\n{section_items[0]['description']}\n\n")
            notebooks_md.append("*Content will be uploaded later.*\n")
            continue

        # Add section slides if available
        section_cfg = section_configs.get(section, {})
        if section_cfg.get('slides'):
            # Determine the section directory even if there are no items
            if section_items:
                section_dir = Path(section_items[0]['section_folder'])
                section_folder = section_dir.name
            else:
                cfg_folder = section_cfg.get('folder', '')
                section_dir = Path(cfg_folder) if cfg_folder else Path('.')
                section_folder = section_dir.name if cfg_folder else None
            slide_html = generate_slide_embed(section_cfg['slides'], section_dir.parent, Path(config.get('output_dir', 'docs')), 'index', section_folder=section_folder)
            notebooks_md.append('\n' + slide_html + '\n')

        # If the section declares data_files, add a download box linking to the section zip
        if section_cfg.get('data_files'):
            sec_folder = section_items[0]['section_folder'] if section_items else section_cfg.get('folder')
            if sec_folder:
                zip_name = f"{Path(sec_folder).name}-data.zip"
                notebooks_md.append(f"\n<div class=\"download-box\">\n<strong>Section files:</strong> <a href=\"./{sec_folder}/{zip_name}\">📦 {zip_name}</a>\n</div>\n\n")

        # Sort items: first by those with order (ascending), then by filename (descending)
        def sort_key(item):
            if item.get('order') is not None:
                return (0, item['order'], '')  # Items with order come first
            else:
                return (1, 0, item.get('name', ''))  # Then items without order

        sorted_items = sorted(section_items, key=sort_key)
        # For items without order, we want descending by name
        items_with_order = [item for item in sorted_items if item.get('order') is not None]
        items_without_order = sorted([item for item in sorted_items if item.get('order') is None],
                                   key=lambda x: x.get('name', ''), reverse=True)
        sorted_items = items_with_order + items_without_order

        # Optional section icon prefix for each item link
        icon_prefix = ''
        if section_cfg.get('icon'):
            icon_prefix = f"{section_cfg.get('icon')} "

        for item in sorted_items:
            # Make title a link with arrow
            if item.get('type') == 'markdown':
                notebooks_md.append(f"### {icon_prefix}[{item['title']} →](./{item['html_file']})\n")
            else:
                colab_url = f"https://colab.research.google.com/github/{github_repo}/blob/{github_branch}/{output_dir_name}/{item['exercise_file']}"
                notebooks_md.append(f"### {icon_prefix}[{item['title']} →]({colab_url})\n")
            
            if item['description']:
                notebooks_md.append(f"{item['description']}\n")
            
            if item.get('type') == 'markdown':
                # Handle markdown files
                notebooks_md.append('<div>\n')
                # notebooks_md.append(f'📄 View: <a href="./{item["html_file"]}">content</a><br>\n')
                if item['data_file']:
                    notebooks_md.append(f'📦 Data: <a href="./{item["data_file"]}">{item["data_file"]}</a><br>\n')
                notebooks_md.append('</div>\n')
            else:
                # Handle notebooks
                colab_url = f"https://colab.research.google.com/github/{github_repo}/blob/{github_branch}/{output_dir_name}/{item['exercise_file']}"
                answers_colab_url = f"https://colab.research.google.com/github/{github_repo}/blob/{github_branch}/{output_dir_name}/{item['answers_file']}"
                
                notebooks_md.append('<div class="resource-buttons">\n')
                notebooks_md.append(f'<a href="{colab_url}" class="resource-button primary">🚀 Open in Colab</a>\n')
                notebooks_md.append(f'<a href="{answers_colab_url}" class="resource-button completed">✓ Completed (Colab)</a>\n')
                notebooks_md.append('</div>\n')
                
                notebooks_md.append('<div class="download-links">\n')
                notebooks_md.append(f'📓 Download: <a href="./{item["exercise_file"]}">worksheet</a> | ')
                notebooks_md.append(f'<a href="./{item["answers_file"]}">completed</a><br>\n')
                if item['data_file']:
                    notebooks_md.append(f'📦 Data: <a href="./{item["data_file"]}">{item["data_file"]}</a>\n')
                notebooks_md.append('</div>\n')
            
            # Add slides mention only if it's item-specific (not inherited from section)
            # Item has its own slides if 'slides' exists but is different from 'section_slides'
            if item.get('slides') and item.get('slides') != item.get('section_slides'):
                slide_filename = Path(item["slides"]).name
                notebooks_md.append(f'<div style="margin: 0.5em 0; color: #666;">📑 Slides: <a href="./{item["slides"]}">{slide_filename}</a></div>\n')
            
            # Add links if present
            if item.get('links'):
                notebooks_md.append('\n**Links:**\n\n')
                notebooks_md.append("<ul>")
                for link in item['links']:
                    name = link.get('name', 'Link')
                    url = link.get('url', '#')
                    desc = link.get('description', '')
                    if desc:
                        notebooks_md.append(f'<li><a href="{url}">{name}</a> {desc}</li>\n')
                    else:
                        notebooks_md.append(f'<li><a href="{url}">{name}</a></li>\n')
            notebooks_md.append("</ul>")
            notebooks_md.append("\n\n")
            notebooks_md.append("")  # Empty line between items
    
    # Use template from config or default
    template = config.get('index_template', '''
<style>
/* Hero section */
.hero {
    padding: 56px 24px;
    margin: 1.5em 0 2em;
    text-align: center;
    background: linear-gradient(180deg, #f6f8fa 0%, #ffffff 100%);
    border: 1px solid #e6e8eb;
    border-radius: 12px;
}
.hero h1 { margin: 0 0 0.4em; font-size: 2.2em; }
.hero .subtitle { margin: 0 auto; max-width: 980px; color: #555; font-size: 1.1em; }
</style>

<div class="hero">
    <h1>{{ title }}</h1>
    <p class="subtitle">{{ description }}</p>
  
</div>

{{ codespaces_button }}

{{ notebooks }}
''')
    
    # Replace template variables
    index_content = template
    index_content = index_content.replace('{{ title }}', config.get('title', 'Workshop'))
    index_content = index_content.replace('{{ description }}', config.get('description', ''))

    # Add Codespaces button if configured
    codespaces_button = ''
    platforms = config.get('platforms', [])
    if 'codespaces' in platforms:
        notebooks_branch = config.get('notebooks_branch', 'codespaces')
        # Link to open/resume an existing Codespace filtered by repo
        owner_repo_escaped = github_repo.replace('/', '%2F')
        resume_url = f"https://github.com/codespaces?query=repo%3A{owner_repo_escaped}"
        # Direct link to create a new Codespace for this repo/branch
        codespaces_url = f"https://codespaces.new/{github_repo}?ref={notebooks_branch}"
        codespaces_button = f'''
<div class="cs-cta" style="text-align: center; margin: 2em 0; padding: 1.5em; background: #f6f8fa; border-radius: 8px; border: 1px solid #e6e8eb;">
    <style>
    .cs-cta .row {{ display: grid; grid-template-columns: 260px 1fr; align-items: center; gap: 16px; margin: 12px 0; }}
    .cs-cta .btn {{ display: inline-flex; align-items: center; justify-content: center; padding: 12px 24px; border-radius: 6px; font-weight: 600; text-decoration: none; min-width: 240px; }}
    .cs-cta .btn-green {{ background: #238636; color: #fff; }}
    .cs-cta .btn-blue {{ background: #0969da; color: #fff; }}
    .cs-cta .explain {{ max-width: 720px; color: #666; font-size: 0.95em; text-align: left; }}
    @media (max-width: 800px) {{ .cs-cta .row {{ grid-template-columns: 1fr; }} .cs-cta .explain {{ text-align: center; }} }}
    </style>
    <h3 style="margin-top: 0;">🚀 Start Coding in the Cloud</h3>
    <p style="margin: 0.5em 0 1em; color: #444; font-size: 0.95em;">
        GitHub Codespaces lets you code right in your browser — no installs, no setup. Your files and tools live safely in the cloud.
    </p>
    <!-- Row 1: New Codespaces (left button, right explanation) -->
    <div class="row">
        <a class="btn btn-green" href="{codespaces_url}">☁️ new codespaces</a>
        <div class="explain">Create a fresh cloud workspace for this course on the <code>{notebooks_branch}</code> branch — nothing to install.</div>
    </div>
    <!-- Row 2: Open Existing (left button, right explanation) -->
    <div class="row">
        <a class="btn btn-blue" href="{resume_url}">📂 open existing</a>
        <div class="explain">If you already have a Codespace for this repo, reopen it and pick up where you left off.</div>
    </div>
</div>
'''

    index_content = index_content.replace('{{ codespaces_button }}', codespaces_button)
    index_content = index_content.replace('{{ notebooks }}', '\n'.join(notebooks_md))
    index_content = index_content.replace('{{ author }}', config.get('author', ''))
    index_content = index_content.replace('{{ organization }}', config.get('organization', ''))
    index_content = index_content.replace('{{ newsletter }}', config.get('newsletter_signup', ''))
    
    # Convert to HTML and write
    html_content = markdown_to_html(index_content, config.get('title', 'Workshop'))
    with open(output_dir / 'index.html', 'w') as f:
        f.write(html_content)
    
    print(f"✓ Created {output_dir / 'index.html'}")


def setup_git_lfs(output_dir, size_threshold_mb=80):
    """Setup Git LFS for large files if in a git repository."""
    # Check if we're in a git repository
    try:
        result = subprocess.run(['git', 'rev-parse', '--git-dir'], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            return  # Not a git repo
    except:
        return  # Git not installed
    
    print("\n📦 Git repository detected, checking for large files...")
    
    # Check if Git LFS is initialized
    gitattributes = Path('.gitattributes')
    lfs_initialized = False
    
    if gitattributes.exists():
        with open(gitattributes, 'r') as f:
            content = f.read()
            if 'filter=lfs' in content:
                lfs_initialized = True
    
    if not lfs_initialized:
        # Initialize Git LFS
        try:
            result = subprocess.run(['git', 'lfs', 'install'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("  → Git LFS initialized")
                lfs_initialized = True
            else:
                print("  ⚠ Git LFS not available. Install with: brew install git-lfs")
                return
        except:
            print("  ⚠ Git LFS not installed. Install with: brew install git-lfs")
            return
    
    # Find large files in output directory AND root directory (for source PPTX/PDF files)
    large_files = []
    size_threshold = size_threshold_mb * 1024 * 1024  # Convert MB to bytes
    
    # Check files in output directory
    for file_path in output_dir.rglob('*'):
        if file_path.is_file():
            file_size = file_path.stat().st_size
            if file_size > size_threshold:
                # Make sure we have a relative path
                try:
                    if file_path.is_absolute():
                        relative_path = file_path.relative_to(Path.cwd())
                    else:
                        relative_path = file_path
                except ValueError:
                    # If path is not relative to cwd, just use the output_dir relative path
                    relative_path = output_dir / file_path.name
                large_files.append((relative_path, file_size))
    
    # Also check root directory for PPTX/PDF files
    for pattern in ['*.pptx', '*.pdf', '*.zip']:
        for file_path in Path.cwd().glob(pattern):
            if file_path.is_file():
                file_size = file_path.stat().st_size
                if file_size > size_threshold:
                    relative_path = file_path.relative_to(Path.cwd())
                    # Don't duplicate if already in list
                    if not any(str(path) == str(relative_path) for path, _ in large_files):
                        large_files.append((relative_path, file_size))
    
    if not large_files:
        return
    
    print(f"\n  Found {len(large_files)} large files (>{size_threshold_mb}MB):")
    
    # Track large files with Git LFS
    lfs_patterns = set()
    
    # Read existing LFS patterns
    if gitattributes.exists():
        with open(gitattributes, 'r') as f:
            for line in f:
                if 'filter=lfs' in line:
                    pattern = line.split()[0]
                    lfs_patterns.add(pattern)
    
    new_patterns = []
    for relative_path, file_size in large_files:
        size_mb = file_size / (1024 * 1024)
        print(f"    • {relative_path} ({size_mb:.1f}MB)")
        
        # Track specific file, not wildcard patterns
        pattern = str(relative_path)
        
        if pattern not in lfs_patterns:
            new_patterns.append(pattern)
    
    if new_patterns:
        print(f"\n  Adding {len(new_patterns)} new Git LFS patterns:")
        for pattern in new_patterns:
            print(f"    • {pattern}")
            try:
                subprocess.run(['git', 'lfs', 'track', pattern], 
                             capture_output=True, text=True, check=True)
            except subprocess.CalledProcessError as e:
                print(f"    ⚠ Failed to track {pattern}: {e}")
        
        print("  → Git LFS tracking updated")
        print("  → Remember to commit .gitattributes")
    else:
        print("  → All large files already tracked by Git LFS")

def create_codespaces_branch(config, commit=False, keep_temp=False):
    """Create or update a codespaces branch with notebooks and data files.

    Uses a temporary repository or a git worktree so the current working tree is not modified.
    Returns True on success, False on failure.
    """
    import shutil
    import tempfile
    import subprocess
    from pathlib import Path

    notebooks_branch = config.get('notebooks_branch', 'codespaces')

    # Verify git repo and remote
    try:
        subprocess.run(['git', 'rev-parse', '--git-dir'], capture_output=True, text=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠ Not in a git repository. Skipping codespaces branch creation.")
        return True

    try:
        remote_proc = subprocess.run(['git', 'config', '--get', 'remote.origin.url'], capture_output=True, text=True, check=True)
        remote_url = remote_proc.stdout.strip()
    except subprocess.CalledProcessError:
        print("  ⚠ Could not determine remote URL. Skipping codespaces branch creation.")
        return False

    if not remote_url:
        print("  ⚠ No remote 'origin' found. Set a remote and try again.")
        return False

    build_dir = Path('build-codespaces')
    if not build_dir.exists():
        print("  ⚠ Build directory not found - nothing to publish.")
        return False

    tmp_ctx = None
    try:
        # create temporary location
        if keep_temp:
            tmp_path = Path(tempfile.mkdtemp(prefix='publish-codespaces-'))
        else:
            tmp_ctx = tempfile.TemporaryDirectory()
            tmp_path = Path(tmp_ctx.name)

        # init temp repo
        subprocess.run(['git', 'init'], cwd=str(tmp_path), check=True, capture_output=True, text=True)
        subprocess.run(['git', 'lfs', 'install'], cwd=str(tmp_path), capture_output=True, text=True)
        subprocess.run(['git', 'remote', 'add', 'origin', remote_url], cwd=str(tmp_path), check=True, capture_output=True, text=True)
        subprocess.run(['git', 'checkout', '--orphan', notebooks_branch], cwd=str(tmp_path), check=True, capture_output=True, text=True)

        # copy build artifacts
        for item in build_dir.iterdir():
            dest = tmp_path / item.name
            if item.is_dir():
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)

        # auto-generate .gitattributes for large files in build_dir
        try:
            threshold_mb = int(config.get('git_lfs_threshold_mb', 80))
        except Exception:
            threshold_mb = 80
        threshold_bytes = threshold_mb * 1024 * 1024
        gitattributes_lines = []
        for f in build_dir.rglob('*'):
            if f.is_file():
                try:
                    if f.stat().st_size > threshold_bytes:
                        rel = f.relative_to(build_dir).as_posix()
                        gitattributes_lines.append(f"{rel} filter=lfs diff=lfs merge=lfs -text\n")
                except Exception:
                    pass

        # include existing top-level .gitattributes
        top_gitattributes = Path('.gitattributes')
        if top_gitattributes.exists():
            try:
                with open(top_gitattributes, 'r') as gf:
                    existing = gf.read()
                for line in existing.splitlines(keepends=True):
                    if line and line not in gitattributes_lines:
                        gitattributes_lines.append(line)
            except Exception:
                pass

        if gitattributes_lines:
            try:
                with open(tmp_path / '.gitattributes', 'w') as outf:
                    outf.writelines(gitattributes_lines)
                print(f"  → Wrote .gitattributes with {len(gitattributes_lines)} entries")
            except Exception as e:
                print(f"  ⚠ Failed to write .gitattributes: {e}")

        # ensure LFS is available
        subprocess.run(['git', 'lfs', 'install'], cwd=str(tmp_path), capture_output=True, text=True)

        # add & commit
        subprocess.run(['git', 'add', '.'], cwd=str(tmp_path), check=True, capture_output=True, text=True)
        commit_msg = f"Update {notebooks_branch} branch with notebooks and data"
        try:
            subprocess.run(['git', 'commit', '-m', commit_msg], cwd=str(tmp_path), check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            if 'nothing to commit' in (e.stderr or '') or 'nothing to commit' in (e.stdout or ''):
                print("  → Nothing to commit in temp repo (maybe no changes). Proceeding to push.")
            else:
                print(f"  ✗ git commit failed: {e.stderr.strip() if e.stderr else e.stdout.strip()}")
                return False

        if commit:
            print("\n  → Pushing temporary branch to remote...")
            try:
                subprocess.run(['git', 'push', '-f', 'origin', notebooks_branch], cwd=str(tmp_path), check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as e:
                print(f"  ✗ git push failed: {e.stderr.strip() if e.stderr else e.stdout.strip()}")
                return False
        else:
            print("\n  → Dry run: temporary repo/worktree created. To push, run with --commit or run these commands in the temp directory:")
            print(f"    cd {tmp_path}")
            print(f"    git push -f origin {notebooks_branch}")

        print(f"\n✓ Successfully prepared {notebooks_branch} from temporary location")
        print(f"✓ Codespaces URL: https://codespaces.new/{config.get('github_repo', 'USER/REPO')}?ref={notebooks_branch}")

        # cleanup: if not keeping temp and tmp_ctx exists, it will be cleaned up in finally

        return True

    except Exception as e:
        print(f"  ✗ Error creating/pushing temporary repo/worktree: {e}")
        return False
    finally:
        if tmp_ctx is not None:
            try:
                tmp_ctx.cleanup()
            except Exception:
                pass

def commit_and_push_main(config) -> bool:
    """Commit and push changes on the main (source) branch of the current repo."""
    try:
        # Ensure we're in a git repo
        subprocess.run(['git', 'rev-parse', '--git-dir'], capture_output=True, text=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠ Not in a git repository. Skipping commit/push on main branch.")
        return True

    branch = config.get('github_branch', 'main')
    # Determine current branch
    try:
        cur = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], capture_output=True, text=True, check=True)
        current_branch = (cur.stdout or '').strip()
    except subprocess.CalledProcessError:
        current_branch = ''

    switched = False
    if current_branch and current_branch != branch:
        print(f"→ Switching from {current_branch} to {branch} to commit site changes...")
        try:
            subprocess.run(['git', 'switch', branch], check=True, capture_output=True, text=True)
            switched = True
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to switch to {branch}: {e.stderr.strip() if e.stderr else e.stdout.strip()}")
            return False

    # Stage all changes (docs/, .gitattributes, etc.)
    try:
        subprocess.run(['git', 'add', '-A'], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"✗ git add failed: {e.stderr.strip() if e.stderr else e.stdout.strip()}")
        return False

    # Commit (ignore if nothing to commit)
    committed = True
    try:
        subprocess.run(['git', 'commit', '-m', 'Publish site updates'], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        committed = False
        if 'nothing to commit' in (e.stderr or '') or 'nothing to commit' in (e.stdout or ''):
            print("→ No changes to commit on main branch.")
        else:
            print(f"✗ git commit failed: {e.stderr.strip() if e.stderr else e.stdout.strip()}")
            return False

    # Push
    print(f"\n→ Pushing changes to origin/{branch}...")
    try:
        subprocess.run(['git', 'push', 'origin', branch], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"✗ git push failed: {e.stderr.strip() if e.stderr else e.stdout.strip()}")
        return False

    if committed:
        print("✓ Pushed main branch changes")
    else:
        print("✓ Main branch is up to date on remote")

    # Switch back to original branch if we switched
    if switched and current_branch:
        try:
            subprocess.run(['git', 'switch', current_branch], check=True, capture_output=True, text=True)
            print(f"→ Switched back to {current_branch}")
        except subprocess.CalledProcessError:
            # Non-fatal; user can switch manually if needed
            pass
    return True

def main():
    """Process all notebooks and create data packages."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Process notebooks and create workshop materials')
    parser.add_argument('--commit', action='store_true',
                       help='Commit and push main branch, and update/push the codespaces branch')
    parser.add_argument('--keep-temp', action='store_true',
                       help='Keep the temporary repo for inspection (for debugging)')
    args = parser.parse_args()

    config = load_config()
    output_dir = Path(config.get('output_dir', 'docs'))
    
    # Clean up old publish directory
    if output_dir.exists():
        import shutil
        shutil.rmtree(output_dir)
        print(f"✓ Cleaned up old {output_dir}/ directory")
    
    output_dir.mkdir(exist_ok=True)
    
    # Look for notebooks and markdown files in configured sections
    sections = config.get('sections', [])
    processed_items = []
    
    # If no sections but root-level content exists, still create the index
    if not sections:
        if config.get('slides') or config.get('data_files') or config.get('links'):
            print("No sections defined, creating index with root-level content only")
        else:
            print("Warning: No sections defined and no root-level content in workshop-config.yaml")
            return
    
    for section in sections:
        if isinstance(section, dict):
            folder = section.get('folder')
            title = section.get('title', folder)
            section_slides = section.get('slides')
            is_draft = section.get('draft', False)
        else:
            # Handle if sections is a list of strings
            folder = section
            title = section
            section_slides = None
            is_draft = False

        # Handle draft sections - just add a placeholder
        if is_draft:
            print(f"\nSkipping draft section: {title}")
            # Add a placeholder item for the index
            processed_items.append({
                'section': title,
                'section_folder': folder,
                'is_draft': True,
                'description': section.get('description', '') if isinstance(section, dict) else ''
            })
            continue

        if not folder or not Path(folder).exists():
            print(f"Warning: Section folder '{folder}' not found")
            continue

        # Create section-level data zip if section declares data_files
        if isinstance(section, dict) and section.get('data_files'):
            section_zip_name = f"{Path(folder).name}-data.zip"
            section_output_subdir = output_dir / folder
            section_output_subdir.mkdir(parents=True, exist_ok=True)
            # Normalize patterns: if patterns include the section folder prefix, strip it
            raw_patterns = list(section.get('data_files') or [])
            normalized = []
            folder_prefix = f"{Path(folder).name}/"
            for p in raw_patterns:
                if isinstance(p, str) and p.startswith(folder_prefix):
                    normalized.append(p[len(folder_prefix):])
                else:
                    normalized.append(p)

            # Patterns in config are relative to the section folder; pass base_dir=Path(folder)
            create_data_zip(normalized, section_output_subdir / section_zip_name, Path(folder))

        # Process notebooks
        for notebook_path in Path(folder).glob('*.ipynb'):
            # Skip checkpoints
            if '.ipynb_checkpoints' in str(notebook_path):
                continue

            print(f"\nProcessing {notebook_path}")
            notebook_info = process_notebook(notebook_path, output_dir, config, section_cfg=section)
            if notebook_info:
                # Override section with configured title
                notebook_info['section'] = title
                notebook_info['section_folder'] = folder
                # Add section slides separately to avoid duplication
                if section_slides:
                    notebook_info['section_slides'] = section_slides
                processed_items.append(notebook_info)

        # Process markdown files
        for markdown_path in Path(folder).glob('*.md'):
            print(f"\nProcessing {markdown_path}")
            markdown_info = process_markdown(markdown_path, output_dir, config, section_cfg=section)
            if markdown_info:
                # Override section with configured title
                markdown_info['section'] = title
                markdown_info['section_folder'] = folder
                # Add section slides separately to avoid duplication
                if section_slides:
                    markdown_info['section_slides'] = section_slides
                processed_items.append(markdown_info)
    
    # Create index.html (even if no items, we might have root-level content)
    if processed_items or config.get('slides') or config.get('data_files') or config.get('links'):
        print("\nCreating index.html...")
        create_index(processed_items, config, output_dir)
    
    print(f"\n✓ Published {len(processed_items)} items to {output_dir}/")
    
    # Setup Git LFS for large files if in a git repo
    lfs_threshold = int(config.get('git_lfs_threshold_mb', 80))  # Default 80MB
    setup_git_lfs(output_dir, lfs_threshold)

    # If requested, commit and push main branch changes first
    if args.commit:
        main_ok = commit_and_push_main(config)
        if not main_ok:
            print("\n❌ Failed to commit/push main branch. Exiting with error.")
            sys.exit(1)

    # Prepare build-codespaces content before creating/updating codespaces branch
    prepare_codespaces_build(config)

    # Create or update codespaces branch
    result = create_codespaces_branch(config, commit=args.commit, keep_temp=args.keep_temp)
    if result is False:
        print("\n❌ Failed to create/update codespaces branch. Exiting with error.")
        sys.exit(1)

if __name__ == '__main__':
    main()