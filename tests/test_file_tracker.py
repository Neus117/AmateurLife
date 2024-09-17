import os
import pytest
from src.file_tracker import MainWindow  # 引入你想测试的类
# 示例测试：测试主窗口初始化
def test_main_window_initialization():
    window = MainWindow()
    assert window is not None
