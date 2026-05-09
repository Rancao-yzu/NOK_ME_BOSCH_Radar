# 测试数据合并
## 1.测试数据文件
读取的文件名字里面必须包含Failed或者Fail
## 2.合并后的测试数据列名
产品DMC，产品料号（半成品/成品），测试站，测试工位(StationID)，测试时间(Start Date Time)，failure mode(Test Step Name)，测试值(Measurement Value)，测试limit（Low Limit）,测试limit（High Limit）
## 3.测试数据填写
### 产品DMC
三种文件格式：
- 2200002200021222000108160825260010520019#_20251203140309_Failed.csv  为Customizing项目
- [Failed][EOL-1][RadarTest.seq][2025-11-30][16-20-13][2200002880021228100110160725328003920019].csv   为EOL项目
- [Fail][2025-12-02 00-40-24][2200002880021228100110160825328006260019]2.csv 为Function test项目  
产品DMC 填写为2200002200021222000108160825260010520019
### 原始测试文件列名
- 对于EOL项目，Step,Status,Measurement,Units,Low Limit,High Limit,Comparison Type
- 对于Function test项目，StepName,Status,MeasureValue,Unit,LowLimit,HighLimit,ElapseTime,ErrorCode,ErrorMessage,Return
- 对于Customizing项目，Test Step Name,Status,Date,Time,Measurement Value,Units,Low Limit,High Limit,String Value,String Limit,Total Time,Error Code,Error Message,Test Step Type,Sequence,Report Text

### 产品料号（半成品/成品）
仅仅对于Function test文件夹下的文件，才需要填写，否则用空格即可。  
例如对于：
- TsetNO:,0203306956,,,,,,,,
- TsetVar:,0203306956,,,,,,,,  
产品料号 填写为0203306956

### 测试站
根据文件名称中的测试站名称填写，例如：
- EOL 填写为 EOL
- Function test 填写为 FCT
- Customizing 填写为 CUS

### 测试工位(StationID)
- 对于EOL项目，关键词为StationID
- 对于Function test项目，关键词为Station ID:
- 对于Customizing项目，关键词为[Station]  
具体信息都在关键词后面一个，填写为该信息

### 测试时间(Start Date Time)
从文件名中可以读取，统一填写为YYYY-MM-DD_HH:MM:SS

### failure mode(Test Step Name)
- 对于EOL项目，类似为：RCS,Failed,该列记录为RCS
- 对于Function test项目，类似为：ArrayEleAmp Max/Min,Failed,该列记录为ArrayEleAmp Max/Min
- 对于Customizing项目，类似为：ExtendedSession,Failed,该列记录为ExtendedSession  
填写为该列记录

### 测试值(Measurement Value)
- 对于EOL项目，填写为Measurement Value下的值(可为空)
- 对于Function test项目，填写为Measurement Value下的值(可为空)
- 对于Customizing项目，填写为Measurement下的值(可为空)

### 测试limit（Low Limit）和 测试limit（High Limit）
- 对于EOL项目，填写为Low Limit,High Limit下的值(可为空)
- 对于Function test项目，填写为LowLimit,HighLimit下的值(可为空)
- 对于Customizing项目，填写为Low Limit,High Limit下的值(可为空)

## 4.软件架构说明
1. 读取文件夹
2. 用户使用时间选择读取文件
预先存储测试时间(Start Date Time)
例如，用户选择2025-12-03 14:03:09至2025-12-08 14:03:10，才正式读取文件
3. 命名规则为测试时间段，输出文件夹为OUT
4. python架构，至少ui和处理逻辑分离（2个文件最佳）
5. ttk界面，但是要稍微好看一些







