# :star: File Tracker
一个自动跟踪文件路径并根据使用频率和时间排序的工具

File Tracker_v1.1.0 堂堂发布！！！更小的体积，更快的响应速度，更方便的功能实现！！！

<br>

A tool for automatically tracking file paths and sorting them by usage frequency and time.

File Tracker_v1.1.0 Grand Release!!! Smaller size, faster response time, and more convenient functionality!!!

<div align="center">

![File Tracker 概览](https://raw.githubusercontent.com/Neus117/File-Tracker/main/images/FileTracker_v1.1-Overview.jpg)

</div>

## 功能 | Features
左边的文件选择器(Browser)支持
- 树状图浏览导航
- 同时支持选择文件夹或文件(选择文件可双击直接打开其父文件夹)
- 记忆上次浏览的视图位置
- 自动重置水平滚动条

右边的路径记录器(Logger)支持
- 自动记录路径
- 按使用频率或时间排序
- Ctrl C 复制路径
- 右键菜单展开功能选项
- 路径顶置和取消顶置
- 路径的单独或全量删除
- 置顶和取消置顶用户图形界面

<br><br>

The file selector (Browser) on the left supports:
- Tree-view navigation
- Ability to select both folders and files (double-clicking a file allows direct access to its parent folder)
- Memory of the last viewed location
- Automatic reset of the horizontal scroll bar

The path logger (Logger) on the right supports:
- Automatic path logging
- Sorting based on frequency of use or time
- Path copying via Ctrl + C
- Context menu with expanded options on right-click
- Pinning and unpinning of paths
- Individual or bulk deletion of paths
- Pinning and unpinning of the user interface elements

<br><br>

## 使用说明 | How to Use
1.在 Releases 中下载并运行 `File Tracker.exe` 即可使用。

2.程序运行后会在 "C:\Users\Currentuser" 下释放一个数据库文件(1.0+ 版本文件名为 file_access.db，1.1+ 版本文件名为 file_tracker.db)，用于储存路径信息。

3.在 Windows 系统中添加自启动任务的方法：WIN+R 打开运行，然后输入命令 shell:startup 回车。之后将需要添加自启动任务的程序快捷方式放入弹出的窗口即可。

4.如何卸载：直接删除 File Tracker.exe 和 file_tracker.db(或 file_access.db)。

<br><br>

1.Download and run `File Tracker.exe` from the Releases section to start using the program.

2.After the program is launched, a database file will be created under "C:\Users\Currentuser" (file name for version 1.0+ is file_access.db, and for version 1.1+ it is file_tracker.db), which will store path information.

3.To add the program to startup in Windows: Press WIN+R to open the Run dialog, then type the command shell:startup and press Enter. Add the shortcut of the program that you want to start automatically to the folder that opens.

4.To uninstall: Simply delete File Tracker.exe and file_tracker.db (or file_access.db).

<br><br>

## 依赖 | Dependencies
- Python 3.11
- 1.0+ 版本依赖 PyQt5，1.1+ 版本依赖 wxPython。其他依赖请参考 `requirements.txt` 或 `environment.yml`

<br>

- Python 3.11
- Version 1.0+ depends on PyQt5, and version 1.1+ depends on wxPython. For other dependencies, please refer to `requirements.txt` or `environment.yml`.

<br><br>

## 开发者安装 | Developer Installation
1. 克隆此仓库 | Clone this repository
   ```bash
   git clone https://github.com/yourusername/file-tracker.git
2. 安装依赖 | Install the required dependencies
   ```bash
   conda env create -f environment.yml
   conda activate ft_env

<br><br>

## 开发者调试 | Developer Debugging
- 运行 file_tracker.py 启动应用 | Run file_tracker.py to start the application
  ```bash
  python src/file_tracker.py
- 接下来请开始您的自定义。 | From here, feel free to customize it as you like.

<br><br>

## 开发者贡献 | Developer Contributions
欢迎提交 issue 或 pull request！

<br>

You are welcome to submit issues or pull requests!
