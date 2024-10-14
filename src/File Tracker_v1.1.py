import wx
import os
import sqlite3
import subprocess
import json
import ctypes
from datetime import datetime

class CustomBitmapButton(wx.Panel):
    def __init__(self, parent, bitmap, size):
        super().__init__(parent, size=size)
        self.bitmap = bitmap
        self.SetBackgroundColour(parent.GetBackgroundColour())
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        dc.SetBackground(wx.Brush(self.GetParent().GetBackgroundColour()))
        dc.Clear()
        padding = 2
        dc.DrawBitmap(self.bitmap, padding, padding, True)

    def OnLeftDown(self, event):
        self.SetBackgroundColour(wx.Colour(230, 230, 230))
        self.Refresh()

    def OnLeftUp(self, event):
        self.SetBackgroundColour(self.GetParent().GetBackgroundColour())
        self.Refresh()
        wx.PostEvent(self, wx.CommandEvent(wx.wxEVT_BUTTON))

    def SetBitmap(self, bitmap):
        self.bitmap = bitmap
        self.Refresh()

class CustomButton(wx.Button):
    def __init__(self, parent, label, color=None, min_width=None):
        super().__init__(parent, label=label, style=wx.BORDER_NONE)
        self.normal_color = wx.Colour(240, 240, 240)
        self.hover_color = wx.Colour(200, 200, 200)
        self.color = color if color else wx.BLACK
        self.SetForegroundColour(self.color)
        self.hovering = False

        wx.Button.SetBackgroundColour(self, parent.GetBackgroundColour())

        self.Bind(wx.EVT_ENTER_WINDOW, self.on_enter)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.on_leave)
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_LEFT_UP, self.on_left_up)

        text_width, text_height = self.GetTextExtent(label)
        min_width = max(text_width + 20, min_width or 0)
        self.SetMinSize((min_width, text_height + 10))

    def on_enter(self, event):
        self.hovering = True
        self.Refresh()

    def on_leave(self, event):
        self.hovering = False
        self.Refresh()

    def on_paint(self, event):
        dc = wx.PaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        
        rect = self.GetRect()
        if self.hovering:
            gc.SetBrush(wx.Brush(self.hover_color))
        else:
            gc.SetBrush(wx.Brush(self.normal_color))
        
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRoundedRectangle(0, 0, rect.width, rect.height, 5)
        
        gc.SetFont(self.GetFont(), self.color)
        text_width, text_height = gc.GetTextExtent(self.GetLabel())
        gc.DrawText(self.GetLabel(), (rect.width - text_width) / 2, (rect.height - text_height) / 2)

    def SetBackgroundColour(self, color):
        self.normal_color = color
        self.Refresh()

    def on_left_up(self, event):
        self.Refresh()
        event.Skip()

class FileTracker(wx.Frame):
    def __init__(self):
        style = wx.DEFAULT_FRAME_STYLE | wx.WANTS_CHARS
        super().__init__(parent=None, title='File Tracker', style=style)
        self.SetName("FileTrackerFrame")
        self.SetBackgroundColour(wx.WHITE)
        
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.app_data_dir = wx.StandardPaths.Get().GetUserDataDir()
        if not os.path.exists(self.app_data_dir):
            os.makedirs(self.app_data_dir)
        self.config_file = os.path.join(self.app_data_dir, "config.json")
        self.accessed_paths_file = os.path.join(self.app_data_dir, 'accessed_paths.json')
        self.init_database()
        self.pinned_paths = self.load_pinned_paths()
        self.last_directory = self.load_last_directory()
        self.set_icon("shell32_star.ico")
        
        self.set_global_font()
        
        self.InitUI()
        self.Centre()
        
        self.sort_column = 1
        self.sort_reverse = True
        
        self.load_accessed_paths()
        self.sort_list_items(self.sort_column)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Bind(wx.EVT_SIZE, self.on_window_resize)
        self.Bind(wx.EVT_ACTIVATE, self.on_activate)
        self.Bind(wx.EVT_SHOW, self.on_show)
        
        wx.CallAfter(self.restore_scroll_position)
        self.ignore_scroll_events = False
        self.scroll_timer = None
        self.initial_scroll_position = None

    def restore_scroll_position(self):
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                scroll_pos = config.get('scroll_position', {})
                v_relative = scroll_pos.get('v_relative', 0)
                
                tree = self.dir_ctrl.GetTreeCtrl()
                total_height = tree.GetScrollRange(wx.VERTICAL)
                v_pos = int(v_relative * total_height)
                
                self.ignore_scroll_events = True
                self.initial_scroll_position = v_pos
                
                # 立即设置滚动位置
                tree.SetScrollPos(wx.VERTICAL, v_pos)
                tree.Refresh()
                
                # 使用一个短暂的定时器来确保滚动位置已经被正确设置
                wx.CallLater(50, self.finalize_scroll_restore)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"恢复滚动位置时出错: {e}")

    def finalize_scroll_restore(self):
        tree = self.dir_ctrl.GetTreeCtrl()
        current_pos = tree.GetScrollPos(wx.VERTICAL)
        
        if current_pos != self.initial_scroll_position:
            tree.SetScrollPos(wx.VERTICAL, self.initial_scroll_position)
            tree.Refresh()
        
        # 短暂冻结树控件以防止闪烁
        tree.Freeze()
        wx.CallLater(100, self.unfreeze_tree, tree)
        
        self.ignore_scroll_events = False

    def unfreeze_tree(self, tree):
        tree.Thaw()
        tree.Refresh()

    def init_database(self):
        self.db_path = os.path.join(os.path.expanduser("~"), "file_tracker.db")
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS paths (
                id INTEGER PRIMARY KEY,
                path TEXT UNIQUE,
                access_count INTEGER DEFAULT 1,
                last_access_time TEXT,
                is_pinned INTEGER DEFAULT 0
            )
            ''')
            self.conn.commit()
        except sqlite3.Error as e:
            wx.MessageBox(f"初始化数据库时发生错误: {e}", "数据库错误", wx.OK | wx.ICON_ERROR)

    def set_icon(self, icon_name):
        icon_paths = [
            os.path.join(self.current_dir, "images", icon_name),
            os.path.join("D:\\Work\\programming\\File Tracker\\images", icon_name),
            icon_name  # 尝试直接使用文件名
        ]
        
        for icon_path in icon_paths:
            if os.path.exists(icon_path):
                try:
                    icon = wx.Icon(icon_path, wx.BITMAP_TYPE_ICO)
                    self.SetIcon(icon)
                    return
                except Exception as e:
                    print(f"Error loading icon from {icon_path}: {e}")
        
        print("Failed to load icon from all possible paths.")

    def load_bitmap(self, bitmap_name, size=None):
        bitmap_path = os.path.join(self.current_dir, "images", bitmap_name)
        if not os.path.exists(bitmap_path):
            bitmap_path = f"D:\\Work\\programming\\File Tracker\\images\\{bitmap_name}"
        image = wx.Image(bitmap_path, wx.BITMAP_TYPE_PNG)
        if size:
            image = image.Scale(size[0], size[1], wx.IMAGE_QUALITY_HIGH)
        return wx.Bitmap(image)

    def calculate_icon_size(self, original_size, target_size):
        aspect_ratio = original_size[0] / original_size[1]
        if aspect_ratio > 1:
            return (target_size, int(target_size / aspect_ratio))
        else:
            return (int(target_size * aspect_ratio), target_size)

    def InitUI(self):
        panel = wx.Panel(self)
        panel.SetBackgroundColour(self.GetBackgroundColour())
        
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        splitter = wx.SplitterWindow(panel, style=wx.SP_LIVE_UPDATE | wx.SP_NOBORDER)
        splitter.SetBackgroundColour(self.GetBackgroundColour())

        self.dir_ctrl = wx.GenericDirCtrl(splitter, -1, dir=self.last_directory, style=wx.DIRCTRL_3D_INTERNAL|wx.DIRCTRL_MULTIPLE)
        self.dir_ctrl.ShowHidden(True)
        self.dir_ctrl.SetMinSize((300, -1))  # 设置最小宽度为300像素
        tree = self.dir_ctrl.GetTreeCtrl()
        tree.SetBackgroundColour(self.GetBackgroundColour())
        
        # 添加双击事件绑定
        tree.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.on_dir_item_activated)
        
        # 在这里添加滚动事件绑定
        tree.Bind(wx.EVT_SCROLLWIN, self.on_scroll)
        
        right_panel = wx.Panel(splitter)
        right_panel.SetBackgroundColour(self.GetBackgroundColour())
        right_sizer = wx.BoxSizer(wx.VERTICAL)

        self.list_ctrl = wx.ListCtrl(right_panel, style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_NONE)
        self.list_ctrl.SetBackgroundColour(self.GetBackgroundColour())
        self.list_ctrl.InsertColumn(0, '访问的路径', width=400)   # 访问路径列宽
        self.list_ctrl.InsertColumn(1, '频次', width=80)   # 频次列宽
        self.list_ctrl.InsertColumn(2, '最后访问时间', width=200)   # 最后访问时间列宽
        self.list_ctrl.Bind(wx.EVT_LIST_COL_CLICK, self.on_column_click)
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.on_right_click)
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_item_activated)

        right_sizer.Add(self.list_ctrl, 1, wx.EXPAND | wx.ALL, 5)

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # 切换排序
        sort_btn_width = self.GetTextExtent("切换排序")[0] + 20
        open_btn = CustomButton(right_panel, '打开', min_width=sort_btn_width)
        open_btn.Bind(wx.EVT_BUTTON, self.on_open)
        btn_sizer.Add(open_btn, 0, wx.RIGHT | wx.TOP | wx.BOTTOM, 5)
        sort_btn = CustomButton(right_panel, '切换排序')
        sort_btn.Bind(wx.EVT_BUTTON, self.on_toggle_sort)
        btn_sizer.Add(sort_btn, 0, wx.RIGHT | wx.TOP | wx.BOTTOM, 5)

        btn_sizer.AddStretchSpacer()

        # 清空
        clear_btn = CustomButton(right_panel, '清空', color=wx.RED)
        clear_btn.Bind(wx.EVT_BUTTON, self.on_clear)
        btn_sizer.Add(clear_btn, 0, wx.RIGHT | wx.TOP | wx.BOTTOM, 5)
        
        btn_sizer.AddStretchSpacer()
        
        # 置顶开关
        original_size = self.load_bitmap("pin_grey.png").GetSize()
        target_size = 28  # 设置目标尺寸，您可以根据需要调整这个值(只能是 4 的倍数，不然会很模糊)
        icon_size = self.calculate_icon_size(original_size, target_size)
        pin_bitmap = self.load_bitmap("pin_grey.png", icon_size)
        button_size = (icon_size[0] + 6, icon_size[1] + 6)  # 每边增加 3 像素
        self.pin_btn = CustomBitmapButton(right_panel, pin_bitmap, button_size)
        self.pin_btn.Bind(wx.EVT_BUTTON, self.on_always_on_top)
        btn_sizer.Add(self.pin_btn, 0, wx.ALIGN_CENTER_VERTICAL)

        right_sizer.Add(btn_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 15)   # 按钮与程序底部边界距离
        right_panel.SetSizer(right_sizer)

        splitter.SplitVertically(self.dir_ctrl, right_panel)
        splitter.SetMinimumPaneSize(300)
        splitter.SetSashPosition(400)

        main_sizer.Add(splitter, 1, wx.EXPAND | wx.ALL, 0)
        panel.SetSizer(main_sizer)

        self.SetSize(1280, 720)

        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_press)

        self.Layout()
        self.Refresh()

        self.adjust_column_widths()
        self.list_ctrl.Bind(wx.EVT_SIZE, lambda event: self.adjust_column_widths())

    def set_icon(self, icon_name="file_tracker_icon.ico"):
        icon_paths = [
            os.path.join(self.current_dir, "images", icon_name),
            os.path.join("D:\\Work\\programming\\File Tracker\\images", icon_name),
            icon_name  # 尝试直接使用文件名
        ]
        
        for icon_path in icon_paths:
            if os.path.exists(icon_path):
                try:
                    icon = wx.Icon(icon_path, wx.BITMAP_TYPE_ICO)
                    self.SetIcon(icon)
                    return
                except Exception:
                    continue  # 如果这个路径加载失败，尝试下一个路径
        
        # 如果所有路径都失败，使用 LogWarning
        wx.LogWarning("无法加载应用图标")

    def load_last_directory(self):
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                last_dir = config.get('last_directory', "C:\\")
            return last_dir if os.path.exists(last_dir) else "C:\\"
        except (FileNotFoundError, json.JSONDecodeError):
            return "C:\\"

    def adjust_column_widths(self):
        list_width = self.list_ctrl.GetSize().width
        
        # 设置固定宽度
        frequency_width = self.list_ctrl.GetTextExtent("频次").width + 20  # 额外空间用于边距
        self.list_ctrl.SetColumnWidth(1, frequency_width)
        
        # 计算最后访问时间列的宽度
        last_access_width = max([self.list_ctrl.GetTextExtent(self.list_ctrl.GetItemText(i, 2)).width for i in range(self.list_ctrl.GetItemCount())] + [self.list_ctrl.GetTextExtent("最后访问时间").width]) + 20
        self.list_ctrl.SetColumnWidth(2, last_access_width)
        
        # 计算路径列的宽度
        path_min_width = 300  # 设置一个较宽的最小宽度
        path_width = max(list_width - frequency_width - last_access_width - 20, path_min_width)  # 20 是滚动条的估计宽度
        self.list_ctrl.SetColumnWidth(0, path_width)

    def on_always_on_top(self, event):
        if self.GetWindowStyle() & wx.STAY_ON_TOP:
            self.SetWindowStyle(self.GetWindowStyle() & ~wx.STAY_ON_TOP)
            bitmap_name = "pin_grey.png"
        else:
            self.SetWindowStyle(self.GetWindowStyle() | wx.STAY_ON_TOP)
            bitmap_name = "pin_red.png"
        
        original_size = self.load_bitmap(bitmap_name).GetSize()
        target_size = 28  # 保持与 InitUI 中相同的目标尺寸
        icon_size = self.calculate_icon_size(original_size, target_size)
        bitmap = self.load_bitmap(bitmap_name, icon_size)
        self.pin_btn.SetBitmap(bitmap)

    def on_open(self, event):
        paths = self.dir_ctrl.GetPaths()
        for path in paths:
            if os.path.exists(path):
                self.record_accessed_path(path)
                self.open_folder(path)
            else:
                self.remove_invalid_path(path)
        wx.CallLater(100, self.reset_dir_ctrl_scroll)  # 100毫秒延迟

    def open_folder(self, path):
        if os.path.isfile(path):
            folder_to_open = os.path.dirname(path)
        else:
            folder_to_open = path
        subprocess.Popen(f'explorer "{folder_to_open}"')

    def reset_dir_ctrl_scroll(self):
        tree = self.dir_ctrl.GetTreeCtrl()
        wx.CallAfter(self._do_reset_horizontal_scroll, tree)

    def _do_reset_horizontal_scroll(self, tree):
        tree.SetScrollPos(wx.HORIZONTAL, 0)
        
        # 获取根节点
        root = tree.GetRootItem()
        if root.IsOk():
            # 获取第一个子节点（通常是第一个驱动器）
            first_child, cookie = tree.GetFirstChild(root)
            if first_child.IsOk():
                # 获取当前可见的第一个项目
                first_visible = tree.GetFirstVisibleItem()
                
                # 滚动到第一个子节点以重置水平滚动条
                tree.ScrollTo(first_child)
                
                # 如果之前有可见项目，则重新滚动到该项目
                if first_visible.IsOk():
                    tree.ScrollTo(first_visible)
                    tree.EnsureVisible(first_visible)
        
        # 强制更新布局
        tree.Update()
        tree.Refresh()
        
        # 再次检查并设置水平滚动位置
        final_h_pos = tree.GetScrollPos(wx.HORIZONTAL)
        if final_h_pos != 0:
            tree.SetScrollPos(wx.HORIZONTAL, 0)

    def on_clear(self, event):
        dlg = wx.MessageDialog(self, "确定要清空所有记录吗？", "确认清空", wx.YES_NO | wx.ICON_QUESTION)
        result = dlg.ShowModal()
        if result == wx.ID_YES:
            self.cursor.execute("DELETE FROM paths")
            self.conn.commit()
            self.list_ctrl.DeleteAllItems()
            self.pinned_paths.clear()
            self.adjust_column_widths()
        dlg.Destroy()
        self.Refresh()

    def on_right_click(self, event):
        if self.list_ctrl.GetFirstSelected() == -1:
            return
        menu = wx.Menu()
        
        copy_item = menu.Append(wx.ID_ANY, "复制路径")
        self.Bind(wx.EVT_MENU, self.on_copy, copy_item)
        
        selected_path = self.list_ctrl.GetItemText(self.list_ctrl.GetFirstSelected())
        if selected_path in self.pinned_paths:
            unpin_item = menu.Append(wx.ID_ANY, "取消顶置")
            self.Bind(wx.EVT_MENU, self.on_unpin, unpin_item)
        else:
            pin_item = menu.Append(wx.ID_ANY, "顶置")
            self.Bind(wx.EVT_MENU, self.on_pin, pin_item)
        
        open_item = menu.Append(wx.ID_ANY, "打开")
        self.Bind(wx.EVT_MENU, self.on_open_selected, open_item)
        
        delete_item = menu.Append(wx.ID_ANY, "删除")
        self.Bind(wx.EVT_MENU, self.on_delete_selected, delete_item)
        
        self.PopupMenu(menu)
        menu.Destroy()

    def on_pin(self, event):
        selected = self.list_ctrl.GetFirstSelected()
        if selected != -1:
            path = self.list_ctrl.GetItemText(selected)
            if path not in self.pinned_paths:
                self.pinned_paths.insert(0, path)
                self.cursor.execute("UPDATE paths SET is_pinned = 1 WHERE path = ?", (path,))
                self.conn.commit()
                self.sort_list_items(self.sort_column)

    def on_unpin(self, event):
        selected = self.list_ctrl.GetFirstSelected()
        if selected != -1:
            path = self.list_ctrl.GetItemText(selected)
            if path in self.pinned_paths:
                self.pinned_paths.remove(path)
                self.cursor.execute("UPDATE paths SET is_pinned = 0 WHERE path = ?", (path,))
                self.conn.commit()
                self.sort_list_items(self.sort_column)
    
    def on_copy(self, event):
        selected = self.list_ctrl.GetFirstSelected()
        if selected != -1:
            path = self.list_ctrl.GetItemText(selected)
            if wx.TheClipboard.Open():
                wx.TheClipboard.SetData(wx.TextDataObject(path))
                wx.TheClipboard.Close()

    def on_open_selected(self, event):
        selected = self.list_ctrl.GetFirstSelected()
        if selected != -1:
            path = self.list_ctrl.GetItemText(selected)
            if os.path.exists(path):
                self.open_folder(path)
                self.record_accessed_path(path)
                wx.CallLater(100, self.reset_dir_ctrl_scroll)  # 100毫秒延迟
            else:
                self.remove_invalid_path(path)
                self.load_accessed_paths()
                self.sort_list_items(self.sort_column)

    def on_item_activated(self, event):
        index = event.GetIndex()
        path = self.list_ctrl.GetItemText(index)
        if os.path.exists(path):
            self.open_folder(path)
            self.record_accessed_path(path)
            wx.CallLater(100, self.reset_dir_ctrl_scroll)  # 100毫秒延迟
        else:
            self.remove_invalid_path(path)
            self.load_accessed_paths()
            self.sort_list_items(self.sort_column)

    def record_accessed_path(self, path):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute('''
        INSERT INTO paths (path, access_count, last_access_time)
        VALUES (?, 1, ?)
        ON CONFLICT(path) DO UPDATE SET
        access_count = access_count + 1,
        last_access_time = ?
        ''', (path, now, now))
        self.conn.commit()
        self.load_accessed_paths()
        self.sort_list_items(self.sort_column)

    def remove_invalid_path(self, path):
        index = self.find_path(path)
        if index != -1:
            self.list_ctrl.DeleteItem(index)
            # 从数据库中删除记录
            self.cursor.execute("DELETE FROM paths WHERE path=?", (path,))
            self.conn.commit()
            # 如果是置顶路径，也从置顶列表中移除
            if path in self.pinned_paths:
                self.pinned_paths.remove(path)
        wx.MessageBox(f"路径 '{path}' 已失效，已从记录中删除。", "路径失效", wx.OK | wx.ICON_INFORMATION)

    def find_path(self, path):
        for i in range(self.list_ctrl.GetItemCount()):
            if self.list_ctrl.GetItemText(i) == path:
                return i
        return -1

    def load_pinned_paths(self):
            self.cursor.execute("SELECT path FROM paths WHERE is_pinned = 1 ORDER BY id")
            return [row[0] for row in self.cursor.fetchall()]

    def load_accessed_paths(self):
        self.list_ctrl.DeleteAllItems()
        
        # 首先添加置顶路径
        for path in self.pinned_paths:
            self.cursor.execute("SELECT access_count, last_access_time FROM paths WHERE path=?", (path,))
            result = self.cursor.fetchone()
            if result:
                access_count, last_access_time = result
                index = self.list_ctrl.InsertItem(self.list_ctrl.GetItemCount(), path)
                self.list_ctrl.SetItem(index, 1, str(access_count))
                self.list_ctrl.SetItem(index, 2, last_access_time)
                self.list_ctrl.SetItemBackgroundColour(index, wx.Colour(255, 255, 200))  # 设置背景色
        
        # 然后添加其他路径
        self.cursor.execute("SELECT path, access_count, last_access_time FROM paths WHERE is_pinned = 0 ORDER BY access_count DESC")
        for path, access_count, last_access_time in self.cursor.fetchall():
            index = self.list_ctrl.InsertItem(self.list_ctrl.GetItemCount(), path)
            self.list_ctrl.SetItem(index, 1, str(access_count))
            self.list_ctrl.SetItem(index, 2, last_access_time)
        
        self.adjust_column_widths()

    def save_accessed_paths(self):
        # 首先，删除数据库中所有记录
        self.cursor.execute("DELETE FROM paths")
        
        # 然后，重新插入当前 list_ctrl 中的所有记录
        for i in range(self.list_ctrl.GetItemCount()):
            path = self.list_ctrl.GetItemText(i)
            count = int(self.list_ctrl.GetItem(i, 1).GetText())
            last_access = self.list_ctrl.GetItem(i, 2).GetText()
            is_pinned = 1 if path in self.pinned_paths else 0
            self.cursor.execute('''
            INSERT INTO paths (path, access_count, last_access_time, is_pinned)
            VALUES (?, ?, ?, ?)
            ''', (path, count, last_access, is_pinned))
        self.conn.commit()

    def on_column_click(self, event):
        column = event.GetColumn()
        self.sort_column = column
        self.sort_reverse = not self.sort_reverse
        self.sort_list_items(column)

    def on_toggle_sort(self, event):
        self.sort_column = 1 if self.sort_column == 2 else 2
        self.sort_reverse = True
        self.sort_list_items(self.sort_column)

    def sort_list_items(self, column):
        items = []
        for i in range(self.list_ctrl.GetItemCount()):
            items.append((self.list_ctrl.GetItemText(i),
                        int(self.list_ctrl.GetItem(i, 1).GetText()),
                        self.list_ctrl.GetItem(i, 2).GetText()))
        
        # 分离置顶项和非置顶项
        pinned_items = [item for item in items if item[0] in self.pinned_paths]
        unpinned_items = [item for item in items if item[0] not in self.pinned_paths]
        
        # 对非置顶项进行排序
        if column == 0:  # 路径
            unpinned_items.sort(key=lambda x: x[0].lower(), reverse=self.sort_reverse)
        elif column == 1:  # 访问次数
            unpinned_items.sort(key=lambda x: x[1], reverse=self.sort_reverse)
        elif column == 2:  # 最后访问时间
            unpinned_items.sort(key=lambda x: datetime.strptime(x[2], "%Y-%m-%d %H:%M:%S"), reverse=self.sort_reverse)

        # 对置顶项按照它们在 self.pinned_paths 中的顺序排序
        pinned_items.sort(key=lambda x: self.pinned_paths.index(x[0]))

        # 合并置顶项和非置顶项
        sorted_items = pinned_items + unpinned_items

        # 更新列表控件
        self.list_ctrl.DeleteAllItems()
        for index, item in enumerate(sorted_items):
            list_index = self.list_ctrl.InsertItem(self.list_ctrl.GetItemCount(), item[0])
            self.list_ctrl.SetItem(list_index, 1, str(item[1]))
            self.list_ctrl.SetItem(list_index, 2, item[2])
            
            # 为置顶项添加浅芽黄色背景
            if item[0] in self.pinned_paths:
                self.list_ctrl.SetItemBackgroundColour(list_index, wx.Colour(255, 255, 200))  # 浅芽黄色
            else:
                self.list_ctrl.SetItemBackgroundColour(list_index, wx.WHITE)  # 恢复默认背景色
        
        self.adjust_column_widths()

    def on_key_press(self, event):
        keycode = event.GetKeyCode()
        if event.ControlDown() and keycode == 67:  # Ctrl+C
            self.on_copy(event)
        else:
            event.Skip()

    def on_delete_selected(self, event):
        selected = self.list_ctrl.GetFirstSelected()
        if selected != -1:
            dlg = wx.MessageDialog(self, "确定要删除这条记录吗？", "确认删除", wx.YES_NO | wx.ICON_QUESTION)
            result = dlg.ShowModal()
            if result == wx.ID_YES:
                path = self.list_ctrl.GetItemText(selected)
                self.list_ctrl.DeleteItem(selected)
                self.cursor.execute("DELETE FROM paths WHERE path=?", (path,))
                self.conn.commit()
                if path in self.pinned_paths:
                    self.pinned_paths.remove(path)
                self.adjust_column_widths()
            dlg.Destroy()
            self.Refresh()

    def load_last_directory(self):
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                last_dir = config.get('last_directory', "C:\\")
            return last_dir if os.path.exists(last_dir) else "C:\\"
        except (FileNotFoundError, json.JSONDecodeError):
            return "C:\\"

    def save_last_directory(self):
        current_dir = self.dir_ctrl.GetPath()
        if os.path.exists(current_dir):
            config = {'last_directory': current_dir}
            try:
                with open(self.config_file, 'w') as f:
                    json.dump(config, f)
            except IOError as e:
                wx.LogError(f"无法保存配置: {e}")

    def on_close(self, event):
        self.save_last_directory()
        self.save_accessed_paths()
        self.save_scroll_position()
        self.conn.close()
        event.Skip()

    def save_scroll_position(self):
        tree = self.dir_ctrl.GetTreeCtrl()
        v_pos = tree.GetScrollPos(wx.VERTICAL)
        total_height = tree.GetScrollRange(wx.VERTICAL)
        relative_pos = v_pos / total_height if total_height > 0 else 0
        
        config = {}
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        config['scroll_position'] = {'v_relative': relative_pos}
        with open(self.config_file, 'w') as f:
            json.dump(config, f)

    def on_window_resize(self, event):
        self.adjust_column_widths()
        event.Skip()

    def set_global_font(self):
        default_font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        new_font = wx.Font(default_font.GetPointSize() + 1, 
                        default_font.GetFamily(), 
                        default_font.GetStyle(), 
                        wx.FONTWEIGHT_NORMAL,
                        False,
                        default_font.GetFaceName())
        
        self.SetFont(new_font)
        
        wx.SystemOptions.SetOption("msw.staticbox.optimized-paint", 0)
        wx.Button.SetFont(self, new_font)
        wx.StaticText.SetFont(self, new_font)
        wx.TextCtrl.SetFont(self, new_font)

    def on_dir_item_activated(self, event):
        tree = self.dir_ctrl.GetTreeCtrl()
        item = event.GetItem()
        path = self.dir_ctrl.GetPath(item)
        
        if os.path.isfile(path):
            folder_to_open = os.path.dirname(path)
            if os.path.exists(folder_to_open):
                self.open_folder(folder_to_open)
                self.record_accessed_path(folder_to_open)
                wx.CallLater(100, self.reset_dir_ctrl_scroll)
            else:
                self.remove_invalid_path(folder_to_open)
            event.Veto()
        else:
            event.Skip()

    def refresh_custom_buttons(self):
        for child in self.GetChildren():
            if isinstance(child, CustomButton):
                child.Refresh()

    def on_activate(self, event):
        self.Refresh()
        self.refresh_custom_buttons()
        wx.CallAfter(self.reset_dir_ctrl_scroll)
        event.Skip()
        
    def on_scroll(self, event):
        if self.ignore_scroll_events:
            return
        
        tree = self.dir_ctrl.GetTreeCtrl()
        v_pos = tree.GetScrollPos(wx.VERTICAL)
        total_height = tree.GetScrollRange(wx.VERTICAL)
        relative_pos = v_pos / total_height if total_height > 0 else 0
        
        if self.scroll_timer:
            self.scroll_timer.Stop()
        self.scroll_timer = wx.CallLater(200, self.save_scroll_position)
        
        event.Skip()

    def on_show(self, event):
        if event.IsShown():
            wx.CallAfter(self.reset_dir_ctrl_scroll)
        event.Skip()

if __name__ == '__main__':
    app = wx.App()
    if 'wxMSW' in wx.PlatformInfo:
        ctypes.windll.shcore.SetProcessDpiAwareness(True)
    frm = FileTracker()
    frm.Show()
    app.MainLoop()