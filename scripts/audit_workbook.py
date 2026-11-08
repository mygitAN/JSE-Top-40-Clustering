"""Read-only OOXML inspection; no Excel engine or source modifications required."""
import json
import posixpath
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'data/source/Top40_PIT_Verification_v4.xlsx'
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}


def read_workbook(path=SOURCE):
    with zipfile.ZipFile(path) as archive:
        shared = []
        if 'xl/sharedStrings.xml' in archive.namelist():
            shared = [''.join(n.itertext()) for n in ET.fromstring(archive.read('xl/sharedStrings.xml')).findall('s:si', NS)]
        relations = {r.attrib['Id']: r.attrib['Target'] for r in ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))}
        sheets = {}
        for sheet in ET.fromstring(archive.read('xl/workbook.xml')).findall('s:sheets/s:sheet', NS):
            rid = sheet.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']
            target = relations[rid]
            target = target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/'+target)
            rows = []
            for row in ET.fromstring(archive.read(target)).findall('s:sheetData/s:row', NS):
                cells = {}
                for cell in row.findall('s:c', NS):
                    value = cell.findtext('s:v', default='', namespaces=NS)
                    if cell.attrib.get('t') == 's':
                        value = shared[int(value)]
                    elif cell.attrib.get('t') == 'inlineStr':
                        value = ''.join(cell.find('s:is', NS).itertext())
                    cells[cell.attrib['r']] = value
                rows.append(cells)
            sheets[sheet.attrib['name']] = rows
        return sheets


def summary():
    return {name: {'physical_rows': len(rows), 'first_rows': rows[:2]}
            for name, rows in read_workbook().items()}


if __name__ == '__main__':
    print(json.dumps(summary(), indent=2))
