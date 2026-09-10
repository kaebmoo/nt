# anomaly_web/test_merge_uploads.py
"""เช็คว่า FileHandler.save_uploads รวมไฟล์ CSV ถูกต้อง: python3 test_merge_uploads.py"""
import io
import shutil
import tempfile

from werkzeug.datastructures import FileStorage
from utils.file_handler import FileHandler


def fs(name, body):
    return FileStorage(io.BytesIO(body), filename=name)


def main():
    tmp = tempfile.mkdtemp()
    fh = FileHandler(f'{tmp}/up', f'{tmp}/out')

    # header เดียวกัน + ไฟล์สุดท้ายไม่มี newline ปิดท้าย
    info = fh.save_uploads([
        fs('r_2026-1.csv', b'A|B\n1|2\n3|4\n'),
        fs('r_2026-2.csv', b'A|B\n5|6\n'),
        fs('r_2026-3.csv', b'A|B\n7|8'),
    ], input_mode='long')
    body = open(info['filepath'], 'rb').read()
    assert body == b'A|B\n1|2\n3|4\n5|6\n7|8\n', body
    assert info['original_filename'] == 'r_2026-1_merged3.csv', info['original_filename']
    assert len(info['source_files']) == 3

    # header ไม่ตรง -> error และไม่ทิ้งไฟล์ค้าง
    try:
        fh.save_uploads([fs('a.csv', b'A|B\n1|2\n'), fs('b.csv', b'A|C\n1|2\n')], input_mode='long')
        raise AssertionError('ควร raise เมื่อ header ไม่ตรง')
    except ValueError as e:
        assert 'b.csv' in str(e), e

    # ไฟล์เดียว -> ทำงานเหมือน save_upload เดิม
    one = fh.save_uploads([fs('solo.csv', b'A,B\n1,2\n')], input_mode='long')
    assert one['original_filename'] == 'solo.csv'
    assert 'source_files' not in one

    # ปนไฟล์ที่ไม่ใช่ csv -> error
    try:
        fh.save_uploads([fs('a.csv', b'A\n1\n'), fs('b.xlsx', b'PK\x03\x04')], input_mode='long')
        raise AssertionError('ควร raise เมื่อมีไฟล์ที่ไม่ใช่ CSV')
    except ValueError:
        pass

    shutil.rmtree(tmp)
    print('OK')


if __name__ == '__main__':
    main()
