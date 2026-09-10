# anomaly_web/test_csv_io.py
"""เช็คว่า sniff_csv/read_csv_auto เดา sep+encoding ถูก: python3 test_csv_io.py"""
import shutil
import tempfile

import pandas as pd

from utils.csv_io import read_any, read_csv_auto, sniff_csv

THAI = 'บริการโทรศัพท์'


def write(tmp, name, text, encoding):
    path = f'{tmp}/{name}'
    with open(path, 'wb') as f:
        f.write(text.encode(encoding))
    return path


def main():
    tmp = tempfile.mkdtemp()

    cases = [
        # (ชื่อไฟล์, เนื้อไฟล์, encoding ที่เขียน, sep ที่ควรเดาได้, encoding ที่ควรเดาได้)
        ('comma.csv', f'A,B\n1,{THAI}\n', 'utf-8', ',', 'utf-8-sig'),
        ('dw.csv', f'A|B|C\n1|2|{THAI}\n', 'cp874', '|', 'cp874'),
        ('semi.csv', 'A;B\n1;2\n', 'utf-8', ';', 'utf-8-sig'),
        ('tab.csv', 'A\tB\n1\t2\n', 'utf-8', '\t', 'utf-8-sig'),
        ('bom.csv', f'A,B\n1,{THAI}\n', 'utf-8-sig', ',', 'utf-8-sig'),
        ('single.csv', 'A\n1\n2\n', 'utf-8', ',', 'utf-8-sig'),
    ]

    for name, text, enc, want_sep, want_enc in cases:
        path = write(tmp, name, text, enc)
        got = sniff_csv(path)
        assert got == (want_sep, want_enc), f'{name}: {got} != {(want_sep, want_enc)}'
        df = read_csv_auto(path)
        assert list(df.columns) == text.split('\n')[0].split(want_sep), f'{name}: {list(df.columns)}'
        if THAI in text:
            assert THAI in df.iloc[0].astype(str).tolist(), f'{name}: อ่านภาษาไทยเพี้ยน'

    # ตัวอักษรไทย cp874 ที่คร่อม 64KB boundary ต้องไม่ทำให้เดา encoding พลาด
    big = write(tmp, 'big.csv', 'A|B\n' + f'1|{THAI}\n' * 20000, 'cp874')
    assert sniff_csv(big, sample_bytes=1000) == ('|', 'cp874')

    # override ได้
    df = read_csv_auto(f'{tmp}/dw.csv', sep='|', encoding='cp874', nrows=1)
    assert len(df) == 1

    # read_any: .xlsx ต้องไปเข้า read_excel ไม่ใช่ read_csv (บั๊กเดิมของหน้า preview)
    pd.DataFrame({'A': [1, 2], 'B': [THAI, 'x']}).to_excel(f'{tmp}/book.xlsx', index=False)
    xlsx = f'{tmp}/book.XLSX'  # นามสกุลตัวใหญ่ ต้องจับได้เหมือนกัน
    shutil.move(f'{tmp}/book.xlsx', xlsx)
    df = read_any(xlsx, nrows=1)
    assert list(df.columns) == ['A', 'B'] and df['B'].iloc[0] == THAI, df

    # read_any: csv ยังใช้ทางเดิม
    df = read_any(f'{tmp}/dw.csv')
    assert list(df.columns) == ['A', 'B', 'C'], df.columns

    shutil.rmtree(tmp)
    print('OK')


if __name__ == '__main__':
    main()
