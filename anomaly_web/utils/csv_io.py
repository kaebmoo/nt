# anomaly_web/utils/csv_io.py
"""
อ่าน CSV โดยเดา delimiter และ encoding ให้อัตโนมัติ
ไฟล์ export จาก DW เป็น pipe-delimited + cp874 (ไทย) ส่วนไฟล์ที่ผ่าน ETL เป็น comma + utf-8
"""

import pandas as pd

DELIMITERS = [',', '|', ';', '\t']
# latin-1 decode ได้ทุก byte จึงเป็นตัวสุดท้ายที่การันตีว่าไม่ throw
ENCODINGS = ['utf-8-sig', 'cp874', 'latin-1']


def sniff_csv(filepath, sample_bytes=64 * 1024):
    """เดาตัวคั่นและ encoding จากหัวไฟล์ -> (sep, encoding)"""
    with open(filepath, 'rb') as f:
        raw = f.read(sample_bytes)

    # ตัดที่ newline สุดท้าย กันตัวอักษร multi-byte ขาดกลางตัวแล้ว decode ไม่ผ่าน
    cut = raw.rfind(b'\n')
    if cut > 0:
        raw = raw[:cut]

    text, encoding = raw.decode(ENCODINGS[-1], errors='replace'), ENCODINGS[-1]
    for enc in ENCODINGS:
        try:
            text, encoding = raw.decode(enc), enc
            break
        except UnicodeDecodeError:
            continue

    # ponytail: นับตัวคั่นในบรรทัด header เอาตัวที่เจอมากสุด (เสมอกันได้ ',' ตามลำดับใน DELIMITERS)
    # พอสำหรับไฟล์ export; ถ้าเจอ header ที่มีตัวคั่นอยู่ใน quote ค่อยเปลี่ยนไปใช้ csv.Sniffer
    header = text.split('\n', 1)[0]
    sep = max(DELIMITERS, key=header.count)
    if header.count(sep) == 0:
        sep = ','

    return sep, encoding


def read_csv_auto(filepath, **kwargs):
    """pd.read_csv ที่เดา sep/encoding ให้ (ส่ง sep= หรือ encoding= มาเองเพื่อ override ได้)"""
    sep, encoding = sniff_csv(filepath)
    kwargs.setdefault('sep', sep)
    kwargs.setdefault('encoding', encoding)
    return pd.read_csv(filepath, **kwargs)


def read_any(filepath, **kwargs):
    """อ่านไฟล์ตามนามสกุล: Excel -> read_excel, ที่เหลือ -> read_csv_auto"""
    if filepath.lower().endswith(('.xlsx', '.xls', '.xlsm')):
        return pd.read_excel(filepath, **kwargs)
    return read_csv_auto(filepath, **kwargs)
