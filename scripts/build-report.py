#!/usr/bin/env python3
"""Build a printable report using the supplied IBM Plex font family."""
from pathlib import Path
import re
import markdown
root = Path(__file__).resolve().parents[1]
source = (root / 'docs/REPORT.md').read_text()
body = markdown.markdown(source, extensions=['tables', 'fenced_code', 'toc', 'sane_lists'])
body = re.sub(r'<ol start="(\d+)">',
              lambda m: f'<ol start="{m[1]}" style="counter-reset:list-item {int(m[1])-1}">', body)
style = '''
@font-face{font-family:Plex;src:url("assets/IBM-Plex-Sans-Arabic/IBMPlexSansArabic-Regular.otf")}
@font-face{font-family:Plex;src:url("assets/IBM-Plex-Sans-Arabic/IBMPlexSansArabic-SemiBold.otf");font-weight:600}
@page{size:A4;margin:18mm 17mm 20mm;@bottom-left{content:"Thmanyah infrastructure assessment";font:8pt Plex;color:#666}@bottom-right{content:counter(page);font:8pt Plex;color:#666}}
*{box-sizing:border-box}body{font-family:Plex,sans-serif;font-size:10pt;line-height:1.5;color:#171717}
svg{max-width:100%;height:auto}
h1{font-size:28pt;line-height:1.18;margin:0 0 8mm;font-weight:600;color:#000}
h2{font-size:17pt;line-height:1.3;margin:9mm 0 4mm;font-weight:600;color:#000;break-after:avoid}
h2[id="7-evidence-index-and-remaining-acceptance-checks"]{break-before:page}
h3{font-size:12pt;line-height:1.3;margin:6mm 0 3mm;font-weight:600;color:#000;break-after:avoid}
h3[id="36-optional-microsoft-sql-server-task"]{break-before:page}
p{margin:0 0 3mm;orphans:3;widows:3}a{color:#174b3e;text-decoration:underline;overflow-wrap:anywhere}
table{width:100%;border-collapse:collapse;font-size:8.5pt;margin:4mm 0 5mm;table-layout:auto}
th{background:#263d36;color:white;font-weight:600;text-align:left}th,td{padding:2.3mm;border:1px solid #d9d9d9;vertical-align:middle}
tr:nth-child(even) td{background:#f3f5f4}tr{break-inside:avoid}thead{display:table-header-group}
pre{font:8pt/1.5 monospace;white-space:pre-wrap;overflow-wrap:anywhere;margin:3mm 0 5mm;break-inside:avoid}
code{font:8.5pt monospace;overflow-wrap:anywhere}li{margin-bottom:1.5mm}ul,ol{padding-left:5mm;margin:2mm 0 4mm}
blockquote{margin:3mm 0;color:#555}.toc{font-size:9pt}.toc a{text-decoration:none;color:#222}.toc ul{list-style:none}
@media screen{body{max-width:900px;margin:40px auto;padding:32px;background:white}html{background:#edece7}}
'''
(root / 'docs/REPORT.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>Thmanyah infrastructure assessment</title><style>'+style+'</style><body>'+body+'</body></html>')
print('Report HTML generated')
