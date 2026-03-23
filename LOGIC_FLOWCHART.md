# WaterRPA 运行逻辑可视化

## 1. 应用启动流程

```mermaid
graph TD
    A["启动应用<br/>python -m water_rpa.main"] --> B["创建QApplication<br/>应用对象"]
    B --> C["创建RPAWindow<br/>主窗口实例"]
    C --> D["初始化界面组件<br/>控制栏、列表、日志"]
    D --> E["第一次添加任务行<br/>TaskRow"]
    E --> F["显示窗口<br/>进入事件循环"]
    F --> G["等待用户交互"]
    
    style A fill:#e1f5ff
    style G fill:#fff3e0
```

## 2. 任务配置流程

```mermaid
graph TD
    A["用户操作"] --> B{用户操作?}
    
    B -->|点击 + 新增指令| C["add_row方法"]
    C --> D["创建TaskRow组件"]
    D --> E["添加到任务列表"]
    E --> F["显示新的任务行"]
    
    B -->|修改操作类型| G["on_type_changed<br/>回调"]
    G --> H{操作类型?}
    H -->|1,2,3,8| I["显示图片选择按钮<br/>显示重试输入框"]
    H -->|4| J["隐藏按钮<br/>显示文本提示"]
    H -->|5| K["隐藏按钮<br/>显示时间提示"]
    H -->|6| L["隐藏按钮<br/>显示数值提示"]
    H -->|7| M["隐藏按钮<br/>显示快捷键提示"]
    H -->|9| N["显示文件夹选择<br/>隐藏重试"]
    
    B -->|点击删除| O["delete_row方法"]
    O --> P["删除TaskRow<br/>从列表中移除"]
    
    I --> Q["更新UI"]
    J --> Q
    K --> Q
    L --> Q
    M --> Q
    N --> Q
    P --> Q
    Q --> A
    
    style A fill:#fff3e0
    style C fill:#c8e6c9
    style G fill:#c8e6c9
    style O fill:#ffcdd2
```

## 3. 配置保存与加载

```mermaid
graph TD
    A["用户操作"] --> B{选择?}
    
    B -->|保存配置| C["save_config方法"]
    C --> D["收集所有TaskRow数据<br/>get_data"]
    D --> E["转换为JSON格式"]
    E --> F["打开文件选择对话框"]
    F --> G["保存到JSON文件"]
    G --> H["显示成功提示"]
    
    B -->|导入配置| I["load_config方法"]
    I --> J["打开文件选择对话框"]
    J --> K["读取JSON文件内容"]
    K --> L["解析JSON数据"]
    L --> M{验证格式?}
    M -->|有效| N["清空现有任务"]
    N --> O["逐条添加任务"]
    O --> P["显示导入成功提示"]
    M -->|无效| Q["显示错误提示"]
    
    H --> R["返回主界面"]
    P --> R
    Q --> R
    
    style C fill:#b3e5fc
    style I fill:#b3e5fc
    style R fill:#fff3e0
```

## 4. 任务执行总流程

```mermaid
graph TD
    A["用户点击 开始运行"] --> B["start_task方法"]
    B --> C["收集所有任务数据"]
    C --> D{参数验证?}
    D -->|有空参数| E["显示警告"]
    E --> F["返回，不执行"]
    D -->|无空参数| G["清空日志区域"]
    G --> H["发送日志：任务开始"]
    H --> I["禁用添加按钮"]
    I --> J["启用停止按钮"]
    J --> K["获取执行模式<br/>是否循环"]
    K --> L["创建WorkerThread<br/>后台线程"]
    L --> M["连接日志信号"]
    M --> N["连接完成信号"]
    N --> O["启动线程<br/>executor.start"]
    O --> P{勾选最小化?}
    P -->|是| Q["最小化窗口"]
    P -->|否| R["保持窗口"]
    Q --> S["返回,等待线程完成"]
    R --> S
    
    style A fill:#fff3e0
    style E fill:#ffcdd2
    style S fill:#fff3e0
    style L fill:#c8e6c9
```

## 5. WorkerThread 后台线程执行

```mermaid
graph TD
    A["WorkerThread.run<br/>在后台线程执行"] --> B["调用 engine.run_tasks"]
    B --> C["设置标志<br/>is_running = True"]
    C --> D{"loop_forever?"}
    D -->|是| E["外层 while True"]
    D -->|否| F["单次执行"]
    E --> G["遍历任务列表"]
    F --> G
    G --> H["for idx, task in tasks"]
    H --> I{"检查中止<br/>stop_requested?"}
    I -->|是| J["发送日志：停止"]
    I -->|否| K["获取任务参数<br/>type, value, retry"]
    J --> L["返回"]
    K --> M["发送日志：执行步骤"]
    M --> N["分发操作"]
    N --> O["执行对应操作"]
    O --> P["发送日志：操作结果"]
    P --> Q{还有任务?}
    Q -->|是| H
    Q -->|否| R{loop_forever?}
    R -->|是| S["等待0.1秒"]
    S --> E
    R -->|否| T["结束循环"]
    T --> U["发送finished信号"]
    U --> L
    
    style A fill:#b3e5fc
    style B fill:#b3e5fc
    style N fill:#fff9c4
    style O fill:#fff9c4
    style U fill:#c8e6c9
```

## 6. 操作分发与执行

```mermaid
graph TD
    A["operation dispatcher"] --> B{cmd_type?}
    
    B -->|1.0| C["单击左键<br/>mouseClick1"]
    B -->|2.0| D["双击左键<br/>mouseClick2"]
    B -->|3.0| E["右键单击<br/>mouseClickR"]
    B -->|4.0| F["输入文本<br/>Ctrl+V"]
    B -->|5.0| G["等待延迟<br/>time.sleep"]
    B -->|6.0| H["滚轮滑动<br/>pyautogui.scroll"]
    B -->|7.0| I["系统按键<br/>pyautogui.hotkey"]
    B -->|8.0| J["鼠标悬停<br/>mouseMove"]
    B -->|9.0| K["截图保存<br/>pyautogui.screenshot"]
    
    C --> L["发送操作日志"]
    D --> L
    E --> L
    F --> L
    G --> L
    H --> L
    I --> L
    J --> L
    K --> L
    L --> M["继续下一个任务"]
    
    style B fill:#fff9c4
    style C fill:#c8e6c9
    style D fill:#c8e6c9
    style E fill:#c8e6c9
    style F fill:#c8e6c9
    style G fill:#c8e6c9
    style H fill:#c8e6c9
    style I fill:#c8e6c9
    style J fill:#c8e6c9
    style K fill:#c8e6c9
```

## 7. 图像识别与点击流程（mouseClick）

```mermaid
graph TD
    A["mouseClick<br/>clickTimes,lOrR,img,reTry"] --> B["记录开始时间"]
    B --> C{reTry策略?}
    
    C -->|reTry==1| D["单次重试策略"]
    D --> E["while True循环"]
    E --> F{"超时检查<br/>timeout?"}
    F -->|否| G["尝试定位图像<br/>locateCenterOnScreen"]
    F -->|是| H["返回失败"]
    G --> I{图像找到?}
    I -->|是| J["执行点击操作<br/>pyautogui.click"]
    J --> K["break 退出循环"]
    I -->|否| L["捕获异常<br/>ImageNotFoundException"]
    L --> M["打印日志"]
    K --> N["返回成功"]
    M --> O["等待100ms"]
    O --> E
    
    C -->|reTry==-1| P["无限重试策略"]
    P --> Q["while True循环<br/>超时保护"]
    Q --> R["尝试定位图像"]
    R --> S{图像找到?}
    S -->|是| T["执行点击<br/>继续重试"]
    S -->|否| U["继续等待"]
    T --> V["等待100ms"]
    U --> V
    V --> Q
    
    C -->|reTry>1| W["指定次数策略<br/>i=1到reTry"]
    W --> X["while i < reTry+1"]
    X --> Y["尝试定位图像"]
    Y --> Z{图像找到?}
    Z -->|是| AA["执行点击<br/>i增加"]
    Z -->|否| AB["继续等待"]
    AA --> AC["等待100ms"]
    AB --> AC
    AC --> X
    
    H --> N
    
    style A fill:#fff3e0
    style E fill:#fff9c4
    style J fill:#c8e6c9
    style N fill:#c8e6c9
    style H fill:#ffcdd2
```

## 8. 任务完成与界面恢复

```mermaid
graph TD
    A["finished_signal<br/>发送完成信号"] --> B["on_finished回调方法"]
    B --> C["启用开始按钮"]
    C --> D["禁用停止按钮"]
    D --> E["启用添加按钮"]
    E --> F["发送日志：任务结束"]
    F --> G{检查窗口<br/>最小化状态?}
    G -->|是| H["恢复窗口<br/>showNormal"]
    G -->|否| I["保持当前状态"]
    H --> J["置顶窗口<br/>activateWindow"]
    I --> J
    J --> K["等待用户下一步操作"]
    
    style A fill:#c8e6c9
    style B fill:#c8e6c9
    style K fill:#fff3e0
```

## 9. 应用关闭事件处理

```mermaid
graph TD
    A["用户关闭窗口"] --> B["closeEvent事件<br/>触发"]
    B --> C{线程运行中?}
    C -->|是| D["设置引擎停止标志<br/>engine.stop"]
    D --> E["等待线程退出<br/>worker.quit"]
    E --> F["等待线程完全停止<br/>worker.wait"]
    F --> G["接受关闭事件<br/>event.accept"]
    C -->|否| G
    G --> H["应用程序退出"]
    
    style A fill:#fff3e0
    style B fill:#fff9c4
    style D fill:#ffcdd2
    style G fill:#c8e6c9
    style H fill:#ffcdd2
```

## 10. 参数验证流程

```mermaid
graph TD
    A["start_task方法"] --> B["for row in self.rows"]
    B --> C["获取任务数据<br/>row.get_data"]
    C --> D["获取value值"]
    D --> E{value为空?}
    E -->|是| F["警告提示<br/>参数不完整"]
    E -->|否| G["添加到任务列表"]
    F --> H["返回，停止执行"]
    G --> I{"是否已添加<br/>所有任务?"}
    I -->|否| B
    I -->|是| J{任务列表<br/>为空?}
    J -->|是| K["警告提示<br/>至少添加一条"]
    J -->|否| L["验证通过<br/>可以执行"]
    K --> H
    L --> M["继续执行"]
    
    style A fill:#fff3e0
    style F fill:#ffcdd2
    style K fill:#ffcdd2
    style L fill:#c8e6c9
    style M fill:#c8e6c9
```

---

**这些流程图展示了WaterRPA应用从启动、配置、执行到完成的完整逻辑链路。**
