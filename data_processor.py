import os
import re
import csv
from datetime import datetime
from collections import OrderedDict


def find_csv_files(folder_path):
    """递归查找包含 Failed|Fail 的CSV文件"""
    files = []
    for root, dirs, filenames in os.walk(folder_path):
        for f in filenames:
            if not f.lower().endswith('.csv'):
                continue
            if 'Failed' in f or 'Fail' in f:
                files.append(os.path.join(root, f))
    return files


def get_project_type(file_path):
    """根据文件所在文件夹判断项目类型: EOL / FCT / CUS"""
    parent = os.path.basename(os.path.dirname(file_path))
    if 'EOL' in parent:
        return 'EOL'
    elif 'Function' in parent:
        return 'FCT'
    elif 'Customizing' in parent:
        return 'CUS'
    return 'UNKNOWN'


def parse_test_time_from_filename(file_path, project_type):
    """从文件名中解析测试时间 YYYY-MM-DD_HH:MM:SS"""
    basename = os.path.basename(file_path)
    name_no_ext = os.path.splitext(basename)[0]

    if project_type == 'EOL':
        m = re.search(r'\[(\d{4}-\d{2}-\d{2})\]\[(\d{2}-\d{2}-\d{2})\]', name_no_ext)
        if m:
            date_part = m.group(1)
            time_part = m.group(2).replace('-', ':')
            return f"{date_part}_{time_part}"

    elif project_type == 'FCT':
        m = re.search(r'\[(\d{4}-\d{2}-\d{2})\s+(\d{2}-\d{2}-\d{2})\]', name_no_ext)
        if m:
            date_part = m.group(1)
            time_part = m.group(2).replace('-', ':')
            return f"{date_part}_{time_part}"

    elif project_type == 'CUS':
        m = re.search(r'#_(\d{14})_Failed', name_no_ext)
        if m:
            dt_str = m.group(1)
            dt = datetime.strptime(dt_str, '%Y%m%d%H%M%S')
            return dt.strftime('%Y-%m-%d_%H:%M:%S')

    return ''


def extract_dmc(file_path, project_type):
    """从文件名中提取产品DMC"""
    basename = os.path.basename(file_path)
    name_no_ext = os.path.splitext(basename)[0]

    if project_type == 'CUS':
        m = re.match(r'(\d+)#_', name_no_ext)
        if m:
            return m.group(1)

    elif project_type == 'EOL':
        m = re.search(r'\[(\d+)\]$', name_no_ext)
        if m:
            return m.group(1)

    elif project_type == 'FCT':
        parts = re.findall(r'\[([^\]]+)\]', name_no_ext)
        for p in parts:
            if re.match(r'^\d{30,}$', p):
                return p

    return ''


def parse_file(file_path, project_type):
    """解析单个测试文件，返回记录列表(只保留失败行)"""
    records = []

    # 提取常量信息
    dmc = extract_dmc(file_path, project_type)
    test_time = parse_test_time_from_filename(file_path, project_type)

    # 测试站名
    station_map = {'EOL': 'EOL', 'FCT': 'FCT', 'CUS': 'CUS'}
    test_station = station_map.get(project_type, '')

    if project_type == 'EOL':
        encodings = ['gb2312', 'gbk', 'utf-8']
    else:
        encodings = ['utf-8', 'gb2312', 'gbk']

    content = None
    for enc in encodings:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                content = f.read()
            break
        except (UnicodeDecodeError, LookupError):
            continue

    if content is None:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

    lines = content.splitlines()

    # 解析元数据和数据部分
    metadata = {}
    data_header = None
    data_rows = []
    in_data = False
    header_line_idx = -1

    # 确定数据头关键字
    if project_type == 'EOL':
        header_keyword = 'Test Step Name'
        step_col = 'Test Step Name'
        measure_col = 'Measurement Value'
        low_col = 'Low Limit'
        high_col = 'High Limit'
        status_fail = 'Failed'
    elif project_type == 'FCT':
        header_keyword = 'StepName'
        step_col = 'StepName'
        measure_col = 'MeasureValue'
        low_col = 'LowLimit'
        high_col = 'HighLimit'
        status_fail = 'FAIL'
    elif project_type == 'CUS':
        header_keyword = 'Step,Status,Measurement,Units,Low Limit,High Limit,Comparison Type'
        step_col = 'Step'
        measure_col = 'Measurement'
        low_col = 'Low Limit'
        high_col = 'High Limit'
        status_fail = 'Failed'

    for i, line in enumerate(lines):
        if header_keyword in line:
            in_data = True
            header_line_idx = i
            data_header = line
            continue

        if not in_data:
            # 元数据行
            if project_type == 'CUS':
                m = re.match(r'\[([^\]]+)\],(.+)', line)
                if m:
                    key = f'[{m.group(1)}]'
                    val = m.group(2).split(',')[0].strip()
                    metadata[key] = val
            elif project_type == 'EOL':
                parts = line.split(',', 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    val = parts[1].split(',')[0].strip()
                    metadata[key] = val
            elif project_type == 'FCT':
                parts = line.split(',', 1)
                if len(parts) >= 2:
                    key = parts[0].rstrip(':').strip()
                    val = parts[1].split(',')[0].strip()
                    metadata[key] = val
        else:
            # 数据行 - 需要跳过空行和分隔行
            if i == header_line_idx:
                continue
            stripped = line.strip()
            if not stripped or stripped.startswith('*') or stripped.startswith('End'):
                continue
            if stripped.startswith('RAD,') or stripped.startswith('RAD,'):
                continue
            data_rows.append(line)

    # 提取工位信息
    station_id = ''
    if project_type == 'EOL':
        station_id = metadata.get('StationID', '')
    elif project_type == 'FCT':
        station_id = metadata.get('Station ID', '')
    elif project_type == 'CUS':
        station_id = metadata.get('[Station]', '')

    # 提取产品料号(仅FCT)
    part_number = ''
    if project_type == 'FCT':
        pn = metadata.get('TsetNO', '')
        if not pn:
            pn = metadata.get('TsetVar', '')
        part_number = pn

    # 解析数据头以获取列索引
    header_cols = next(csv.reader([data_header]))

    try:
        idx_step = header_cols.index(step_col)
        idx_measure = header_cols.index(measure_col) if measure_col in header_cols else -1
        idx_low = header_cols.index(low_col) if low_col in header_cols else -1
        idx_high = header_cols.index(high_col) if high_col in header_cols else -1

        # 状态列通常是第二列(索引1)
        for row_str in data_rows:
            row = next(csv.reader([row_str]))
            if len(row) < 2:
                continue
            status = row[1].strip() if len(row) > 1 else ''
            if status != status_fail:
                continue

            step_name = row[idx_step].strip() if idx_step < len(row) else ''
            measure_val = row[idx_measure].strip() if idx_measure >= 0 and idx_measure < len(row) else ''
            low_val = row[idx_low].strip() if idx_low >= 0 and idx_low < len(row) else ''
            high_val = row[idx_high].strip() if idx_high >= 0 and idx_high < len(row) else ''

            record = OrderedDict([
                ('产品DMC', f"'{dmc}"),
                ('产品料号（半成品/成品）', part_number),
                ('测试站', test_station),
                ('测试工位(StationID)', station_id),
                ('测试时间(Start Date Time)', test_time),
                ('failure mode(Test Step Name)', step_name),
                ('测试值(Measurement Value)', measure_val),
                ('测试limit（Low Limit）', low_val),
                ('测试limit（High Limit）', high_val),
            ])
            records.append(record)

    except (ValueError, IndexError):
        pass

    return records


def parse_test_time_to_datetime(time_str):
    """将 YYYY-MM-DD_HH:MM:SS 转为 datetime 对象"""
    try:
        return datetime.strptime(time_str, '%Y-%m-%d_%H:%M:%S')
    except ValueError:
        return None


def process_folder(folder_path, start_time_str, end_time_str, progress_callback=None):
    """
    主处理函数
    folder_path: 源文件夹
    start_time_str: 开始时间 YYYY-MM-DD HH:MM:SS
    end_time_str: 结束时间 YYYY-MM-DD HH:MM:SS
    progress_callback: 进度回调函数(处理文件数, 总文件数)
    """
    all_records = []
    files = find_csv_files(folder_path)

    # 预处理时间范围
    start_dt = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
    end_dt = datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S')

    # 先用文件名中的时间过滤
    filtered_files = []
    file_times = []
    for fp in files:
        pt = get_project_type(fp)
        ft = parse_test_time_from_filename(fp, pt)
        ft_dt = parse_test_time_to_datetime(ft)
        if ft_dt and start_dt <= ft_dt <= end_dt:
            filtered_files.append(fp)
            file_times.append(ft)

    total = len(filtered_files)
    for idx, fp in enumerate(filtered_files):
        pt = get_project_type(fp)
        records = parse_file(fp, pt)
        all_records.extend(records)

        if progress_callback:
            progress_callback(idx + 1, total)

    return all_records


def save_output(records, output_folder, start_time_str, end_time_str):
    """保存合并结果到CSV，文件名为测试时间段"""
    if not records:
        return None

    os.makedirs(output_folder, exist_ok=True)

    # 命名规则为测试时间段
    start_clean = start_time_str.replace(' ', '_').replace(':', '-')
    end_clean = end_time_str.replace(' ', '_').replace(':', '-')
    file_name = f"{start_clean}__{end_clean}.csv"
    output_path = os.path.join(output_folder, file_name)

    fieldnames = list(records[0].keys())
    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    return output_path
