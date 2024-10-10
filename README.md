# File Tracker
一个自动跟踪文件路径并根据使用频率和时间排序的工具。
 | A tool for automatically tracking file paths and sorting them by usage frequency and time.

## 功能 | Features
- 自动记录文件路径
   | Automatically records file paths
- 按使用频率排序
   | Sort by usage frequency
- 按最后访问时间排序
   | Sort by last accessed time
- 支持双击记录打开对应路径文件夹
   | Supports double-clicking a record to open the corresponding folder
- 允许 CTRL+C 以及右键复制路径
   | Allows copying paths via CTRL+C and right-click menu
- 允许单独或全量删除记录
   | Supports deleting individual or all records
- 提供窗口置顶选项
   | Offers a "stay on top" window option

## 使用方法 | How to Use
1. 在 Releases 中下载并运行 `File Tracker.exe` 即可使用。
    | Download and run `File Tracker.exe` from the Releases section to start using.

2. 如何卸载：程序应该没有任何文件释放，可直接删除无残留。
    | How to Uninstall: The program does not create additional files, so you can simply delete it without leaving any traces.

## 依赖 | Dependencies
- Python 3.11

- 其他依赖请参考 `requirements.txt` 或 `environment.yml`
   | For other dependencies, please refer to `requirements.txt` or `environment.yml`

## 开发者安装 | Developer Installation
1. 克隆此仓库 | Clone this repository
   ```bash
   git clone https://github.com/yourusername/file-tracker.git
2. 安装依赖 | Install the required dependencies
   ```bash
   conda env create -f environment.yml
   conda activate ft_env

## 开发者调试 | Developer Debugging
- 运行 file_tracker.py 启动应用 | Run file_tracker.py to start the application
  ```bash
  python src/file_tracker.py
- 接下来请开始您的自定义。 | From here, feel free to customize it as you like.

## 开发者贡献 | Developer Contributions
- 欢迎提交 issue 或 pull request！ | You are welcome to submit issues or pull requests!

- 但是我不一定会看，即使看到了也很大可能没有能力解决，毕竟我是初学者中的菜鸟。 | However, I might not be able to review or resolve them, as I'm just a beginner and likely won't have the skills to fix any major problems.

- 最好有经验丰富的开发者继续开发和完善此工具，比如让它能够直接监控 Windows 资源管理器的导航行为，无需在其界面主动导航而是后台运行持续提供记录服务。还可以增加一个小的悬浮窗，是否开启交由用户选择，鼠标悬停在浮窗上时展开主窗口呈现路径记录供用户选择。 | Ideally, experienced developers could continue improving this tool, such as enabling it to monitor Windows File Explorer's navigation behavior in the background without requiring manual navigation within the tool's interface. It would be great to add a small floating window that can be toggled on or off by the user, expanding into the main window to display the recorded paths when hovered over.

## 一些废话 | A Few Notes
- 这个工具目前最大的缺点是，用户只能主动通过它提供的导航方式实现路径记录，并没有与 Windows 资源管理器实现良好的融合。用户目前只能改变一些使用习惯，比如将它设置随系统自启动，然后尝试将它作为最主要的文件导航方式使用。 | The biggest drawback of this tool is that it currently relies on users actively navigating through its interface to record paths, as it isn't seamlessly integrated with Windows File Explorer. Users will need to adjust their habits, perhaps setting the tool to launch on system startup and using it as their primary method for file navigation.

- 在 Windows 系统中添加自启动任务的方法：WIN+R 打开运行，然后输入命令 shell:startup 回车。之后将需要添加自启动任务的程序快捷方式放入弹出的窗口即可。 | How to add a startup task in Windows: Press WIN+R to open the Run dialog, then enter the command shell:startup and press Enter. Next, place the shortcut of the program you want to add to startup in the window that pops up.
