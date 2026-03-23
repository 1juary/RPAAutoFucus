# WaterRPA 架构深度分析

## 📑 目录
- [整体架构](#整体架构)
- [模块详解](#模块详解)
- [数据流](#数据流)
- [类设计](#类设计)
- [线程模型](#线程模型)
- [设计模式](#设计模式)

---

## 整体架构

### 分层架构模型

```
┌──────────────────────────────────────────────────────┐
│              User Interface Layer (UI层)             │
│  ┌─ RPAWindow (主窗口)                               │
│  ├─ TaskRow (任务行组件)                             │
│  └─ 事件处理与状态反馈                                │
└────────────────┬─────────────────────────────────────┘
                 │ 信号/槽连接
┌────────────────▼──────────────────────────────────────┐
│           Business Logic Layer (业务层)              │
│  ┌─ RPAEngine (任务执行引擎)                          │
│  ├─ TaskManager (任务管理)                           │
│  └─ 任务队列、循环控制、中止管理                       │
└────────────────┬─────────────────────────────────────┘
                 │
┌────────────────▼──────────────────────────────────────┐
│          Operation Layer (操作层)                    │
│  ┌─ mouseClick() (鼠标点击+图像识别)                  │
│  ├─ mouseMove() (鼠标悬停)                           │
│  └─ 各类自动化操作函数                                │
└────────────────┬─────────────────────────────────────┘
                 │
┌────────────────▼──────────────────────────────────────┐
│         System Interface Layer (系统接口层)           │
│  ┌─ pyautogui (鼠标键盘控制)                          │
│  ├─ pyperclip (剪贴板)                               │
│  ├─ os/json (文件系统)                               │
│  └─ threading (多线程)                               │
└──────────────────────────────────────────────────────┘
```

### 模块依赖关系

```
water_rpa/ (package)
│
├─ PySide6 (GUI框架)
│  └─ Qt信号槽机制
│
├─ pyautogui (图像识别与自动化)
│  └─ 图像匹配、鼠标控制、按键模拟
│
├─ pyperclip (剪贴板操作)
│  └─ 文本复制粘贴
│
├─ threading (多线程)
│  └─ QThread继承
│
└─ os/json/time (标准库)
   └─ 文件处理、配置管理、时间控制
```

---

## 模块详解

### 1. RPAWindow 类 (主窗口)

**职责**: GUI展示与用户交互管理

**类结构**:
```python
class RPAWindow(QMainWindow):
    def __init__(self)
    def add_row(self, data=None)
    def delete_row(self, row_widget)
    def save_config(self)
    def load_config(self)
    def start_task(self)
    def stop_task(self)
    def on_finished(self)
    def log(self, msg)
    def closeEvent(self, event)
```

**关键属性**:
- `engine: RPAEngine` - 任务执行引擎实例
- `worker: WorkerThread` - 后台工作线程
- `rows: list[TaskRow]` - 任务行列表
- `task_layout: QVBoxLayout` - 任务容器布局

**事件流**:
1. **初始化** → 创建UI组件、添加初始任务行
2. **用户交互** → 添加/删除/修改任务行
3. **配置管理** → 保存/加载JSON配置
4. **任务执行** → 创建线程、启动引擎
5. **完成回调** → 恢复UI状态

### 2. TaskRow 类 (任务行)

**职责**: 单个任务的UI表示与数据管理

**类结构**:
```python
class TaskRow(QFrame):
    def __init__(self, parent_layout, delete_callback)
    def on_type_changed(self, text)
    def set_data(self, data)
    def select_file(self)
    def get_data(self)
```

**动态UI处理**:

| 操作类型 | 显示按钮 | 显示重试框 | 显示输入框 | 输入提示 |
|---------|--------|---------|---------|--------|
| 1,2,3,8 | 选择图片  | 是       | 是       | 图片路径  |
| 4       | 否      | 否      | 是       | 输入文本  |
| 5       | 否      | 否      | 是       | 时间数值  |
| 6       | 否      | 否      | 是       | 滚动方向  |
| 7       | 否      | 否      | 是       | 快捷键    |
| 9       | 选择文件夹 | 否       | 是       | 保存路径  |

**数据结构**:
```python
{
    "type": 1.0,      # 操作类型编码
    "value": "path",  # 操作参数
    "retry": 1        # 重试策略
}
```

### 3. RPAEngine 类 (任务引擎)

**职责**: 核心任务执行与控制

**工作流程**:
```
run_tasks(tasks, loop_forever, callback)
    ├─ 初始化: is_running=True, stop_requested=False
    ├─ 外层循环: while True
    │   ├─ 检查中止信号: if stop_requested → return
    │   ├─ 内层循环: for task in tasks
    │   │   ├─ 提取参数: type, value, retry
    │   │   ├─ 分发操作: dispatch by type
    │   │   ├─ 执行操作: call specific function
    │   │   └─ 发送日志: callback_msg(...)
    │   ├─ 判断循环: if not loop_forever → break
    │   └─ 等待100ms继续
    └─ 异常处理: try-except-finally
```

**关键参数**:
- `tasks: list[dict]` - 任务列表
- `loop_forever: bool` - 是否循环执行
- `callback_msg: callable` - 日志回调函数

**操作映射**:
```python
type→operation mapping:
1.0 → mouseClick(1, 'left', ...)  # 单击左键
2.0 → mouseClick(2, 'left', ...)  # 双击左键
3.0 → mouseClick(1, 'right', ...) # 右键单击
4.0 → pyperclip.copy() + Ctrl+V  # 输入文本
5.0 → time.sleep(float)           # 等待延迟
6.0 → pyautogui.scroll(int)       # 滚轮滑动
7.0 → pyautogui.hotkey(*keys)     # 系统按键
8.0 → mouseMove(...)               # 鼠标悬停
9.0 → pyautogui.screenshot(path)  # 截图保存
```

### 4. WorkerThread 类 (工作线程)

**职责**: 后台执行任务，保持UI响应性

**继承链**: `QThread` ← `WorkerThread`

**信号定义**:
```python
log_signal = Signal(str)                # 发送日志
finished_signal = Signal()              # 任务完成
```

**执行流程**:
```python
def run(self):
    # 在独立线程中执行
    self.engine.run_tasks(
        self.tasks,
        self.loop_forever,
        self.log_callback
    )
    # 任务完成后发送信号
    self.finished_signal.emit()
```

**信号槽连接**:
- `log_signal` → `RPAWindow.log` (更新日志)
- `finished_signal` → `RPAWindow.on_finished` (恢复UI)

---

## 数据流

### 配置文件流向

```
用户操作 (GUI)
    ↓
TaskRow.get_data() → 收集单行数据
    ↓
RPAWindow.save_config() → 遍历所有行
    ↓
json.dump(tasks, file) → 序列化JSON
    ↓
[存储为文件] (template/1.json)
```

```
[读取文件] (template/1.json)
    ↓
json.load(file) → 反序列化
    ↓
RPAWindow.load_config() → 验证格式
    ↓
TaskRow.set_data(data) → 回填UI
    ↓
用户查看/编辑
```

### 任务执行数据流

```
用户点击 [开始运行]
    ↓
start_task() 收集任务
    ↓
WorkerThread.__init__ 接收任务列表
    ↓
worker.start() 启动线程
    ↓
[线程] engine.run_tasks() 执行任务
    ├─ 遍历任务
    ├─ 分发操作
    ├─ log_callback(msg) 发送日志
    ├─ log_signal.emit(msg) 跨线程信号
    └─ finished_signal.emit() 完成信号
    ↓
[主线程] on_finished() 处理完成
    ↓
恢复UI状态
```

### 图像识别数据流

```
Task: {type: 1.0, value: 'button.png', retry: -1}
    ↓
mouseClick(1, 'left', 'button.png', -1)
    ↓
for attempt in range(max_retries):
    ├─ pyautogui.locateCenterOnScreen(
    │      'button.png',
    │      confidence=0.9
    │  )
    │  ↓
    │  ├─ 找到: {x, y} → pyautogui.click(x, y)
    │  │                ↓ 返回成功
    │  │
    │  └─ 未找到: None → time.sleep(0.1) 继续重试
    │
    └─ [超时] → 返回超时
```

---

## 类设计

### 类关系图

```
QThread ──────┐
             │
             ▼
        WorkerThread
             │
             │ 包含
             ▼
         RPAEngine ◄─── (被RPAWindow持有)

QMainWindow ──────┐
                 │
                 ▼
            RPAWindow
                 │
                 │ 包含多个
                 ▼
              TaskRow

QFrame ────────┐
              │
              ▼
            TaskRow
```

### 关键类的状态机

#### RPAEngine 状态转移

```
    ┌─────────────┐
    │   初始态     │
    │ stopped     │
    └──────┬──────┘
           │ run_tasks() 调用
    ┌──────▼──────┐
    │  运行态      │
    │  running    │◄────────┐
    └──────┬──────┘         │ stop()后继续
           │ stop()         │ 重新run
    ┌──────▼──────┐         │
    │  中止态      │─────────┘
    │  stopping   │
    └──────┬──────┘
           │ 任务完成
    ┌──────▼──────┐
    │   完成态     │
    │ finished    │
    └─────────────┘
```

#### RPAWindow 按钮状态

```
初始化完成
 ├─ [开始运行] ←─ 启用
 ├─ [停止] ←─────── 禁用
 └─ [+新增] ←─────── 启用

点击[开始运行]
 ├─ [开始运行] ←─ 禁用 (防止重复启动)
 ├─ [停止] ←─────── 启用
 └─ [+新增] ←─────── 禁用

任务运行中/完成
 ├─ [开始运行] ←─ 启用
 ├─ [停止] ←─────── 禁用
 └─ [+新增] ←─────── 启用
```

---

## 线程模型

### 多线程设计

```
主线程 (Main Thread - Qt Event Loop)
├─ GUI事件处理
├─ 信号发送
├─ UI更新 (log_area.append)
└─ 用户交互

工作线程 (Worker Thread)
├─ RPAEngine.run_tasks 执行
├─ 所有自动化操作
├─ 发送日志信号 (log_signal.emit)
└─ 完成时发送finished信号
```

### 线程通信机制

```
信号槽通信 (Signal-Slot)

WorkerThread.log_signal
    │ emit(message)
    │
    └─► RPAWindow.log(msg)
        └─ self.log_area.append(msg)
           └─ [线程安全的UI更新]

WorkerThread.finished_signal
    │ emit()
    │
    └─► RPAWindow.on_finished()
        ├─ self.start_btn.setEnabled(True)
        ├─ self.stop_btn.setEnabled(False)
        └─ self.showNormal()
```

### 同步点与同步机制

```
同步方式: Qt信号槽 (线程安全)

① 任务数据收集同步
   主线程: get_data() 从TaskRow收集
   
② 线程启动同步
   主线程: worker.start()
   
③ UI更新同步
   工作线程: log_signal.emit(msg)
   主线程: 通过信号槽自动切换
   
④ 线程完成同步
   工作线程: finished_signal.emit()
   主线程: on_finished() 处理
   
⑤ 关闭同步
   主线程: worker.quit()
          worker.wait()
```

---

## 设计模式

### 1. MVC 模式 (Model-View-Controller)

```
Model (数据):
├─ tasks: list[dict] - 任务列表
├─ 配置文件 (JSON)
└─ engine状态

View (视图):
├─ RPAWindow - 窗口布局
├─ TaskRow - 任务行UI
├─ 日志输出区
└─ 控制按钮

Controller (控制器):
├─ 事件处理方法
├─ add_row(), delete_row()
├─ save_config(), load_config()
└─ start_task(), stop_task()
```

### 2. Observer 模式 (观察者)

```
Subject: WorkerThread
├─ log_signal - 日志信号
└─ finished_signal - 完成信号

Observer: RPAWindow
├─ log() 方法监听日志
└─ on_finished() 监听完成
```

### 3. Strategy 模式 (策略)

```
Context: RPAEngine.run_tasks()

Strategy (操作策略):
├─ MouseClickStrategy (type 1,2,3)
├─ TextInputStrategy (type 4)
├─ WaitStrategy (type 5)
├─ ScrollStrategy (type 6)
├─ HotkeyStrategy (type 7)
├─ MoveStrategy (type 8)
└─ ScreenshotStrategy (type 9)

选择依据: task['type']
```

### 4. Template Method 模式 (模板方法)

```
Base: 任务执行流程

Template:
1. 检查中止信号
2. 获取任务参数
3. 分发到操作
4. 发送日志
5. 继续下一个

Variations: 不同的操作类型
```

### 5. Factory 模式 (工厂)

**隐含的工厂模式**:
```python
# TaskRow 根据类型创建不同UI
if cmd_type in [1.0, 2.0, 3.0, 8.0]:
    创建图片选择UI
elif cmd_type == 4.0:
    创建文本输入UI
elif cmd_type == 5.0:
    创建时间输入UI
...
```

---

## 错误处理与异常

### 异常类型与处理

```
1. ImageNotFoundException (PyAutoGUI)
   └─ 捕获: 继续重试或超时返回
   
2. FileNotFoundError (配置文件)
   └─ 捕获: 显示错误对话框
   
3. ValueError (JSON解析)
   └─ 捕获: 显示格式错误提示
   
4. Exception (通用异常)
   └─ 捕获: 日志输出，继续执行下一个任务
```

### 超时保护机制

```python
mouseClick():
    start_time = time.time()
    while True:
        if time.time() - start_time > timeout:  # 默认60秒
            return  # 超时返回，避免死锁
```

---

## 性能优化

### 1. GUI响应性
- ✅ 后台线程执行任务（避免UI卡顿）
- ✅ 信号槽异步通信
- ✅ 按需更新UI（仅日志更新）

### 2. 资源管理
- ✅ 任务结束后清理线程资源
- ✅ 关闭时正确等待线程完成
- ✅ 避免线程泄漏

### 3. 图像识别优化
- ✅ 使用confidence=0.9提高识别速度
- ✅ 100ms重试间隔平衡响应与CPU占用
- ✅ 超时保护防止无限循环

---

## 扩展建议

### 短期优化
- [ ] 错误恢复机制（任务失败时的恢复策略）
- [ ] 条件判断（if-else分支）
- [ ] 变量系统（保存提取值用于后续步骤）

### 中期扩展
- [ ] 任务录制功能（记录用户操作自动生成配置）
- [ ] 高级调度（设定执行时间）
- [ ] 日志导出（保存详细执行记录）

### 长期演进
- [ ] Web界面（浏览器远程操作）
- [ ] 云同步（多设备配置共享）
- [ ] 机器学习优化（智能识别提高准确率）

---

**本文档提供了WaterRPA的完整架构视角，便于理解项目设计和扩展开发。**
