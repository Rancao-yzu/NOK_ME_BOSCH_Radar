import os
import re
import csv
import time
from datetime import datetime
from collections import OrderedDict


def find_csv_files(folder_path):
    """
    递归遍历指定文件夹，查找所有包含 'Failed' 或 'Fail' 的 CSV 文件
    """
    files = []
    for root, dirs, filenames in os.walk(folder_path):
        for f in filenames:
            # 只处理 CSV 文件（忽略大小写）
            if not f.lower().endswith('.csv'):
                continue
            # 文件名必须包含 Failed 或 Fail
            if 'Failed' in f or 'Fail' in f:
                files.append(os.path.join(root, f))
    return files


def get_project_type(file_path):
    """
    根据文件所在的父文件夹名称判断项目类型

    判断规则:
    根据文件名特征判断:
        - 文件名含 '#_'  → 'CUS' (Customizing项目，如 xxx#_20251203140309_Failed.csv)
        - 文件名含 'EOL' → 'EOL' (如 [Failed][EOL-1]...[DMC].csv)
        - 其余含 Fail/Failed → 'FCT' (如 [Fail][日期][DMC]...csv)
    """

    basename = os.path.basename(file_path)
    if '#_' in basename:
        return 'CUS'
    elif 'EOL' in basename:
        return 'EOL'
    else:
        return 'FCT'


def parse_test_time_from_filename(file_path, project_type):
    """
    从文件名中提取测试时间，统一输出为 YYYY-MM-DD_HH:MM:SS 格式

    各项目文件名的日期时间提取规则:
        - EOL:  文件名中 [2025-11-30][16-20-13] 格式
        - FCT:  文件名中 [2025-12-02 00-40-24] 格式（日期和时间之间有空格）
        - CUS:  文件名中 #_20251203140309_Failed 格式（14位连续数字的时间戳）
    """
    basename = os.path.basename(file_path)
    name_no_ext = os.path.splitext(basename)[0]

    if project_type == 'EOL':
        # 匹配: [YYYY-MM-DD][HH-MM-SS]
        m = re.search(r'\[(\d{4}-\d{2}-\d{2})\]\[(\d{2}-\d{2}-\d{2})\]', name_no_ext)
        if m:
            date_part = m.group(1)
            time_part = m.group(2)
            return f"{date_part}_{time_part}"

    elif project_type == 'FCT':
        # 匹配: [YYYY-MM-DD HH-MM-SS]（日期和时间之间有空格）
        m = re.search(r'\[(\d{4}-\d{2}-\d{2})\s+(\d{2}-\d{2}-\d{2})\]', name_no_ext)
        if m:
            date_part = m.group(1)
            time_part = m.group(2)
            return f"{date_part}_{time_part}"

    elif project_type == 'CUS':
        # 匹配: #_YYYYMMDDHHmmss_Failed
        m = re.search(r'#_(\d{14})_Failed', name_no_ext)
        if m:
            dt_str = m.group(1)
            dt = datetime.strptime(dt_str, '%Y%m%d%H%M%S')
            return dt.strftime('%Y-%m-%d_%H-%M-%S')

    return ''


def extract_dmc(file_path, project_type):
    """
    从文件名中提取产品 DMC（唯一标识码）
    """
    basename = os.path.basename(file_path)
    name_no_ext = os.path.splitext(basename)[0]

    if project_type == 'CUS':
        # 匹配: 数字串#_ 格式（DMC在 # 之前）
        m = re.match(r'(\d+)#_', name_no_ext)
        if m:
            return m.group(1)

    elif project_type == 'EOL':
        # 匹配: 文件名末尾方括号 [纯数字]
        m = re.search(r'\[(\d+)\]$', name_no_ext)
        if m:
            return m.group(1)

    elif project_type == 'FCT':
        # 遍历所有方括号内容，取第一个长度≥30的纯数字串
        parts = re.findall(r'\[([^\]]+)\]', name_no_ext)
        for p in parts:
            if re.match(r'^\d{30,}$', p):
                return p

    return ''


def parse_file(file_path, project_type):
    """
    解析单个测试文件，提取所有 Status=Failed 的行并返回结构化记录

    返回:
        list[OrderedDict]: 每条失败记录为一个 OrderedDict，包含以下 9 个字段:
            - 产品DMC
            - 产品料号（半成品/成品）
            - 测试站
            - 测试工位(StationID)
            - 测试时间(Start Date Time)
            - failure mode(Test Step Name)
            - 测试值(Measurement Value)
            - 测试limit（Low Limit）
            - 测试limit（High Limit）

    文件结构分为两部分（以数据表头行为分界）:
        1. 元数据区（表头之前）: 提取 StationID、产品料号等
        2. 数据区（表头之后）: CSV 格式的测试步骤记录

    编码策略:
        - EOL 文件优先使用 gb2312 → gbk → utf-8（因含中文）
        - FCT/CUS 文件优先使用 utf-8 → gb2312 → gbk
        - 全部失败时降级为 utf-8 + errors='replace'
    """
    records = []

    # ---- 从文件名提取不变信息 ----
    dmc = extract_dmc(file_path, project_type)
    test_time = parse_test_time_from_filename(file_path, project_type)

    # 测试站固定映射: EOL→EOL, FCT→FCT, CUS→CUS
    test_station = project_type

    # ---- 文件编码处理 ----
    # EOL 文件含中文，优先用 GB 系列编码
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

    # 所有编码都失败时，使用 errors='replace' 强制读取
    if content is None:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

    lines = content.splitlines()

    # ---- 解析元数据和数据行 ----
    metadata = {}       # 元数据键值对
    data_header = None  # 数据表头行（原始字符串）
    data_rows = []      # 数据行列表
    in_data = False     # 是否已进入数据区
    header_line_idx = -1  # 数据表头行索引

    # 根据项目类型设定: 表头关键字、目标列名、失败状态值
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
        # CUS 表头是完整的列名行，直接用完整字符串匹配
        header_keyword = 'Step,Status,Measurement,Units,Low Limit,High Limit,Comparison Type'
        step_col = 'Step'
        measure_col = 'Measurement'
        low_col = 'Low Limit'
        high_col = 'High Limit'
        status_fail = 'Failed'

    for i, line in enumerate(lines):
        # 检测到数据表头行后切换到数据模式
        if header_keyword in line:
            in_data = True
            header_line_idx = i
            data_header = line
            continue

        if not in_data:
            # ---- 元数据区解析 ----
            # CUS: [Key],Value 格式
            if project_type == 'CUS':
                m = re.match(r'\[([^\]]+)\],(.+)', line)
                if m:
                    key = f'[{m.group(1)}]'
                    val = m.group(2).split(',')[0].strip()
                    metadata[key] = val
            # EOL: Key,Value 格式
            elif project_type == 'EOL':
                parts = line.split(',', 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    val = parts[1].split(',')[0].strip()
                    metadata[key] = val
            # FCT: Key:Value 格式（冒号在键名后面）
            elif project_type == 'FCT':
                parts = line.split(',', 1)
                if len(parts) >= 2:
                    key = parts[0].rstrip(':').strip()
                    val = parts[1].split(',')[0].strip()
                    metadata[key] = val
        else:
            # ---- 数据区解析 ----
            # 跳过表头行本身
            if i == header_line_idx:
                continue
            stripped = line.strip()
            # 跳过空行、分隔线（***开头）、结束标记（End开头）、RAD版权行
            if not stripped or stripped.startswith('*') or stripped.startswith('End'):
                continue
            if stripped.startswith('RAD,') or stripped.startswith('RAD,'):
                continue
            data_rows.append(line)

    # 提取工位信息（StationID）
    station_id = ''
    if project_type == 'EOL':
        station_id = metadata.get('StationID', '')
    elif project_type == 'FCT':
        station_id = metadata.get('Station ID', '')
    elif project_type == 'CUS':
        station_id = metadata.get('[Station]', '')

    # 提取产品料号（半成品/成品）—— 仅 Function test 需要
    part_number = ''
    if project_type == 'FCT':
        pn = metadata.get('TsetNO', '')
        if not pn:
            pn = metadata.get('TsetVar', '')
        part_number = pn

    # ---- 解析数据表头，定位各列索引 ----
    header_cols = next(csv.reader([data_header]))

    try:
        # 通过表头列名查找索引位置
        idx_step = header_cols.index(step_col)
        idx_status = header_cols.index('Status') if 'Status' in header_cols else 1
        idx_measure = header_cols.index(measure_col) if measure_col in header_cols else -1
        idx_low = header_cols.index(low_col) if low_col in header_cols else -1
        idx_high = header_cols.index(high_col) if high_col in header_cols else -1

        # 遍历每一行数据，只保留 Status=Failed/FAIL 的记录
        for row_str in data_rows:
            row = next(csv.reader([row_str]))
            if len(row) <= idx_status:
                continue
            status = row[idx_status].strip()

            # 只保留失败状态的记录
            if status != status_fail:
                continue

            # 安全提取各列值（防止索引越界）
            step_name = row[idx_step].strip() if idx_step < len(row) else ''
            measure_val = row[idx_measure].strip() if idx_measure >= 0 and idx_measure < len(row) else ''
            low_val = row[idx_low].strip() if idx_low >= 0 and idx_low < len(row) else ''
            high_val = row[idx_high].strip() if idx_high >= 0 and idx_high < len(row) else ''

            if low_val in ('-INF', 'INF'):
                low_val = ''
            if high_val in ('-INF', 'INF'):
                high_val = ''

            # 构建输出记录: OrderedDict 保证列顺序固定
            # DMC 前加单引号防止 Excel 打开时丢失精度
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
        # 表头解析失败时跳过该文件
        pass

    return records


def parse_test_time_to_datetime(time_str):
    """
    将文件名中提取的时间字符串转为 datetime 对象，用于时间范围比较
    """
    try:
        return datetime.strptime(time_str, '%Y-%m-%d_%H-%M-%S')
    except ValueError:
        return None


def process_folder(folder_path, start_time_str, end_time_str, progress_callback=None):
    """
    主处理函数: 扫描文件夹 → 时间过滤 → 逐文件解析 → 合并所有失败记录

    参数:
        folder_path (str):      源文件夹路径（含 EOL/FCT/CUS 子目录）
        start_time_str (str):   开始时间，格式 'YYYY-MM-DD HH:MM:SS'
        end_time_str (str):     结束时间，格式 'YYYY-MM-DD HH:MM:SS'

    返回:
        list[OrderedDict]: 所有符合时间范围且 Status=Failed 的合并记录

    处理流程:
        1. 递归查找所有符合条件的 CSV 文件
        2. 解析每个文件名中的测试时间
        3. 只保留测试时间在 [start_dt, end_dt] 范围内的文件
        4. 逐文件解析，提取失败行
        5. 返回合并后的全部记录
    """
    all_records = []
    files = find_csv_files(folder_path)
    time.sleep(0.25)

    # 将用户输入的时间字符串转为 datetime 对象
    start_dt = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
    end_dt = datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S')

    filtered = []
    for fp in files:
        pt = get_project_type(fp)
        ft = parse_test_time_from_filename(fp, pt)
        ft_dt = parse_test_time_to_datetime(ft)
        # 过滤出在时间范围内的文件，存入 filtered 列表
        if ft_dt and start_dt <= ft_dt <= end_dt:
            filtered.append((fp, pt))

    total = len(filtered)
    for idx, (fp, pt) in enumerate(filtered):
        # 解析每个文件（主要解析步骤）
        records = parse_file(fp, pt)
        all_records.extend(records)

        time.sleep(0.25)
        # 通知 UI 刷新进度条
        if progress_callback:
            progress_callback(idx + 1, total)

    return all_records


def save_output(records, output_folder, start_time_str, end_time_str):
    """
    将合并后的记录保存为 CSV 文件到指定输出目录

    参数:
        records (list[OrderedDict]): 合并后的记录列表
        output_folder (str):         输出目录路径（不存在会自动创建）
        start_time_str (str):        开始时间，用于文件命名
        end_time_str (str):          结束时间，用于文件命名

    返回:
        str | None: 成功返回输出文件的完整路径，记录为空返回 None

    输出文件名规则:
        将时间中的空格换为 _ ，冒号换为 - ，然后用 __ 连接
        例: 2025-12-03_14-03-09__2025-12-08_14-03-10.csv

    编码: UTF-8-BOM (utf-8-sig)，确保 Excel 直接打开不乱码
    """
    if not records:
        return None

    # 确保输出目录存在，不存在则创建
    os.makedirs(output_folder, exist_ok=True)

    # 命名规则: 测试时间段
    start_clean = start_time_str.replace(' ', '_').replace(':', '-')
    end_clean = end_time_str.replace(' ', '_').replace(':', '-')
    file_name = f"[{start_clean}]__[{end_clean}]_Failed.csv"
    output_path = os.path.join(output_folder, file_name)

    fieldnames = list(records[0].keys())
    # utf-8-sig = UTF-8 with BOM，Excel 双击打开即可正确显示中文
    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    return output_path
