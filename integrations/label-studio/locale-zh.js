/* Chinese UI layer for the embedded Label Studio 1.23.2 application.
 * It only replaces known product chrome. User project names and annotation
 * values are intentionally not translated. The observer covers route changes
 * and controls rendered after an import, modal, or editor is opened. */
(function () {
  'use strict';

  const text = {
    'Projects': '项目',
    'Home': '首页',
    'Organization': '组织',
    'Pin menu': '固定菜单',
    'Go Back': '返回',
    'Go to Home': '返回首页',
    'Reload': '重新加载',
    'Runtime error': '运行错误',
    'Create': '创建',
    'Create Project': '创建项目',
    'Create new project': '创建新项目',
    'Project Name': '项目名称',
    'Description': '描述',
    'Workspace': '工作区',
    'General': '常规',
    'General Settings': '常规设置',
    'Settings': '设置',
    'Labeling Interface': '标注界面',
    'Annotation': '标注',
    'Annotation Settings': '标注设置',
    'Labeling Instructions': '标注说明',
    'Model': '模型',
    'Predictions': '预测',
    'Cloud Storage': '云存储',
    'Webhooks': '事件回调',
    'Webhook': '事件回调',
    'Danger Zone': '危险操作',
    'Data Import': '数据导入',
    'Labeling Setup': '标注配置',
    'Browse Templates': '浏览模板',
    'Custom template': '自定义模板',
    'Save': '保存',
    'Cancel': '取消',
    'Close': '关闭',
    'Delete': '删除',
    'Delete Project': '删除项目',
    'Reset Cache': '重置缓存',
    'Drop All Tabs': '关闭所有标签页',
    'Light': '浅色',
    'Default': '默认',
    'Recent Projects': '最近项目',
    'View All': '查看全部',
    'Invite Members': '邀请成员',
    'Tasks': '任务',
    'Tasks:': '任务：',
    'Task': '任务',
    'Submitted annotations': '已提交标注',
    'Predictions:': '预测：',
    'Actions': '操作',
    'Columns': '列',
    'Filters': '筛选',
    'Order by': '排序',
    'Import': '导入',
    'Export': '导出',
    'Import Data': '导入数据',
    'Export data': '导出数据',
    'Add URL': '添加 URL',
    'Upload Files': '上传文件',
    'Dataset URL': '数据集 URL',
    'Drag & drop files here': '将文件拖到此处',
    'or click to browse': '或点击选择文件',
    'or': '或',
    'Images': '图片',
    'Audio': '音频',
    'Video': '视频',
    'HTML / HyperText': 'HTML / 超文本',
    'Text': '文本',
    'Structured data': '结构化数据',
    'PDF': 'PDF',
    'Important:': '提示：',
    'JSON': 'JSON',
    'JSON-MIN': 'JSON-MIN',
    'CSV': 'CSV',
    'TSV': 'TSV',
    'COCO': 'COCO',
    'COCO with Images': 'COCO（含图片）',
    'Pascal VOC XML': 'Pascal VOC XML',
    'YOLO': 'YOLO',
    'YOLO with Images': 'YOLO（含图片）',
    'Browse templates': '浏览模板',
    'Computer Vision': '计算机视觉',
    'Natural Language Processing': '自然语言处理',
    'Audio/Speech Processing': '音频/语音处理',
    'Conversational AI': '对话式 AI',
    'Chat': '对话',
    'Ranking & Scoring': '排序与评分',
    'Structured Data Parsing': '结构化数据解析',
    'Time Series Analysis': '时间序列分析',
    'Videos': '视频',
    'Generative AI': '生成式 AI',
    'Community Contributions': '社区贡献',
    'Enterprise': '企业版',
    'Semantic Segmentation with Polygons': '多边形语义分割',
    'Semantic Segmentation with Masks': '掩码语义分割',
    'Object Detection with Bounding Boxes': '边界框目标检测',
    'OCR Labeling for PDFs': 'PDF 光学字符识别标注',
    'Keypoint Labeling': '关键点标注',
    'Medical Image Classification with Bounding Boxes': '带边界框的医学图像分类',
    'Image Captioning': '图像描述',
    'Visual Genome': '视觉基因组',
    'Multi-page document annotation': '多页文档标注',
    'Inventory Tracking': '库存跟踪',
    'Visual Question Answering': '视觉问答',
    'Image Classification': '图像分类',
    'Optical Character Recognition': '光学字符识别',
    'See the documentation to contribute a template.': '查看文档了解如何贡献模板。',
    'General Settings': '常规设置',
    'Select an option': '请选择',
    'Color': '颜色',
    'Task Sampling': '任务抽样',
    'Sequential sampling': '顺序抽样',
    'Random sampling': '随机抽样',
    'Uncertainty sampling': '不确定性抽样',
    'Show before labeling': '标注前显示',
    'Prelabeling': '预标注',
    'No model or predictions available': '没有可用的模型或预测结果',
    'No predictions uploaded yet': '尚未上传预测结果',
    'Add Webhook': '添加事件回调',
    'Delete project': '删除项目',
    'Regions': '区域',
    'History': '历史记录',
    'Relations': '关系',
    'Info': '信息',
    'Manual': '手动',
    'By Time': '按时间',
    'Preview': '预览',
    'Code': '代码',
    'Visual': '可视化',
    'Submit': '提交',
    'Skip': '跳过',
    'Review': '审核',
    'Accept': '通过',
    'Reject': '驳回',
    'Previous': '上一个',
    'Next': '下一个',
    'Undo': '撤销',
    'Redo': '重做',
    'Zoom in': '放大',
    'Zoom out': '缩小',
    'Fullscreen': '全屏',
    'Loading': '加载中',
    'Use image from': '图像来源',
    'Refresh data': '刷新数据',
    'Learn more': '了解更多',
    'Documentation': '文档',
    'API Documentation': 'API 文档',
    'Release Notes': '版本说明',
    'Slack Community': 'Slack 社区',
    'Label Studio Version: Community': '标注平台版本：社区版',
    'Welcome 👋': '欢迎',
    "Let's get you started.": '开始使用标注平台。',
    'Create your first project': '创建第一个项目',
    'Import your data and set up the labeling interface to start annotating': '导入数据并配置标注界面，开始标注',
    'Import data to get your project started': '导入数据以开始项目',
    'Connect your cloud storage or upload files from your computer': '从电脑上传文件即可开始',
    'Connect Cloud Storage': '连接云存储',
    'See docs on importing data': '查看数据导入文档',
    'Create one and start labeling your data.': '创建项目后即可开始标注数据。',
    "Heidi doesn't see any projects here!": '这里还没有项目',
    'You can export dataset in one of the following formats:': '可以将数据集导出为以下格式：',
    'Add your first webhook': '添加第一个事件回调',
    'Setup integrations that subscribe to certain events using Webhooks.': '通过事件回调配置订阅特定事件的集成。',
    'Perform these actions at your own risk.': '以下操作可能影响项目数据，请谨慎执行。',
    'Project deleted successfully': '项目已删除',
    'No data': '暂无数据',
    'Learn, explore and get help': '学习、探索并获取帮助',
    'opens in a new tab': '在新标签页打开',
    'Optional description of your project': '可选：填写项目描述',
    "Can't find an export format?": '找不到需要的导出格式？',
    'Please let us know in Slack or submit an issue to the Repository': '请在 Slack 中反馈，或向代码仓库提交 Issue。',
    'Having a timeout or trouble exporting large projects?': '导出大型项目时超时或遇到问题？',
    'See all tags.': '查看全部标签。',
    'Explore templates': '浏览模板',
    'Cloud Storage documentation (opens in a new tab)': '云存储文档（在新标签页打开）',
    'Learn more about predictions (opens in new window)': '了解更多预测信息（在新窗口打开）',
    'Learn more about webhooks (opens in new window)': '了解更多事件回调信息（在新窗口打开）',
    'Learn more about video format support (opens in a new tab)': '了解更多视频格式支持（在新标签页打开）',
    'We recommend Cloud Storage over direct uploads due to upload limitations.': '由于直接上传存在限制，建议使用云存储。',
    'For PDFs, use multi-image labeling. JSONL or Parquet (Enterprise only) files require cloud storage.': 'PDF 文件请使用多页图片标注。JSONL 或 Parquet 文件需要使用云存储。',
    'Check the documentation to import preannotated data.': '请查看文档了解如何导入预标注数据。',
    'List of items in raw JSON format stored in one JSON file. Use to export both the data and the annotations for a dataset. It\'s Label Studio Common Format': '将数据集的数据和标注导出为一个原始 JSON 文件，格式为平台通用格式。',
    'List of items where only "from_name", "to_name" values from the raw JSON format are exported. Use to export only the annotations for a dataset.': '仅导出原始 JSON 中的 from_name 和 to_name 字段，用于只导出数据集标注。',
    'Results are stored as comma-separated values with the column names specified by the values of the "from_name" and "to_name" fields.': '结果以逗号分隔值保存，列名由 from_name 和 to_name 字段决定。',
    'Results are stored as tab-separated tabular file with column names specified by "from_name" "to_name" values': '结果以制表符分隔的表格文件保存，列名由 from_name 和 to_name 字段决定。',
    'sequence labeling': '序列标注',
    'text tagging': '文本标记',
    'named entity recognition': '命名实体识别',
    'image segmentation': '图像分割',
    'object detection': '目标检测',
    'keypoints': '关键点',
    'brush annotations': '笔刷标注',
    'document': '文档',
    'doclang': 'DocLang',
    'Popular machine learning format used by the COCO dataset for object detection and image segmentation tasks with polygons and rectangles.': 'COCO 数据集常用的机器学习格式，支持多边形和矩形的目标检测与图像分割。',
    'Popular TXT format is created for each image file. Each txt file contains annotations for the corresponding image file.': '每个图像文件生成一个 TXT 文件，文件中包含对应图像的标注。',
    'Export your brush labels as NumPy 2d arrays. Each label outputs as one image.': '将笔刷标注导出为 NumPy 二维数组，每个标注输出为一张图片。',
    'Export your brush labels as PNG images': '将笔刷标注导出为 PNG 图片',
    'Export your brush labels as COCO format for segmentation tasks. Converts RLE encoded masks to COCO polygons.': '将笔刷标注导出为 COCO 分割格式，并将 RLE 编码的掩码转换为 COCO 多边形。',
    'Configure the labeling interface with tags. See all tags.': '使用标签配置标注界面。查看全部标签。',
    'Labeled regions will appear here': '已标注区域会显示在这里',
    'Start labeling and track your results': '开始标注并跟踪结果',
    'using this panel': '使用此面板',
    'Write instructions to help users complete labeling tasks.': '编写说明，帮助用户完成标注任务。',
    'The instruction field supports HTML markup and it allows use of images, iframes (pdf).': '说明支持 HTML 标记，也可以使用图片和 iframe（PDF）。',
    'Use predictions to prelabel tasks': '使用预测结果预标注任务',
    'Enable and select which set of predictions to use for prelabeling.': '启用并选择用于预标注的预测结果。',
    'Select which predictions or which model you want to use:': '选择要使用的预测结果或模型：',
    'Upload predictions to automatically prelabel your data and speed up annotation. Import predictions from multiple model versions to compare their performance, or connect live models from the Model page to generate predictions on demand.': '上传预测结果即可自动预标注数据并加快标注。可以导入多个模型版本的预测结果进行对比，也可以在模型页面连接在线模型，按需生成预测。',
    'Setup integrations that subscribe to certain events using Webhooks. When an event is triggered, Label Studio sends an HTTP POST request to the configured webhook URL.': '使用事件回调配置订阅特定事件的集成。事件触发后，平台会向配置的回调地址发送 HTTP POST 请求。',
    'Simplify project management by organizing projects into workspaces. Learn more': '将项目组织到工作区中，简化项目管理。了解更多',
    'Simplify project management by organizing projects into workspaces.': '将项目组织到工作区中，简化项目管理。',
    'Tasks are ordered by Task ID': '任务按任务 ID 排序',
    'Tasks are chosen with uniform random': '任务按均匀随机方式选择',
    'Tasks are chosen according to model uncertainty score (active learning mode). Learn more': '任务根据模型不确定性得分选择（主动学习模式）。了解更多',
    'Tasks are chosen according to model uncertainty score (active learning mode).': '任务根据模型不确定性得分选择（主动学习模式）。',
    "Perform these actions at your own risk. Actions you take on this page can't be reverted. Make sure your data is backed up.": '以下操作可能影响项目数据且无法撤销，请先备份数据。',
    'Reset Cache may help in cases like if you are unable to modify the labeling configuration due to validation errors concerning existing labels, but you are confident that the labels don\'t exist. You can use this action to reset the cache and try again.': '如果已有标签的校验错误导致无法修改标注配置，且确认这些标签不存在，可以重置缓存后重试。',
    'If the Data Manager is not loading, dropping all Data Manager tabs can help.': '如果数据管理器无法加载，关闭所有数据管理器标签页可能会解决问题。',
    'Deleting a project removes all tasks, annotations, and project data from the database.': '删除项目会从数据库中移除所有任务、标注和项目数据。',
    'We recommend ': '建议使用',
    ' over direct uploads due to upload limitations.': '，因为直接上传存在限制。',
    'For PDFs, use ': 'PDF 文件请使用',
    '. JSONL or Parquet (Enterprise only) files require cloud storage.': '。JSONL 或 Parquet 文件需要使用云存储。',
    'Check the documentation to ': '请查看文档了解如何',
    'import preannotated data.': '导入预标注数据。',
    'Check the documentation to import preannotated data.': '请查看文档了解如何导入预标注数据。',
    'We recommend': '建议使用',
    ' over direct uploads due to upload limitations.': '，因为直接上传存在限制。',
    ' over direct uploads due to ': '，因为直接上传存在',
    'over direct uploads due to': '，因为直接上传存在',
    'upload limitations.': '限制。',
    'upload limitations': '上传限制',
    'For PDFs, use': 'PDF 文件请使用',
    'multi-image labeling': '多页图片标注',
    'List of tasks': '任务列表',
    'Treat CSV/TSV as': '将 CSV/TSV 视为',
    'Time Series or Whole Text File': '时间序列或完整文本文件',
    '(opens in a new tab)': '（在新标签页打开）',
    'Check the documentation to': '请查看文档了解如何',
    'import preannotated data': '导入预标注数据',
    'Multi-image labeling documentation (opens in a new tab)': '多页图片标注文档（在新标签页打开）',
    'Add Filter': '添加筛选',
    'Inner ID': '内部 ID',
    'Completed': '已完成',
    'Annotations': '标注',
    'Cancelled': '已取消',
    'Annotated by': '标注人',
    'Annotation results': '标注结果',
    'Annotation IDs': '标注 ID',
    'Prediction score': '预测分数',
    'Prediction model versions': '预测模型版本',
    'Prediction results': '预测结果',
    'Upload filename': '上传文件名',
    'Storage filename': '存储文件名',
    'Created at': '创建时间',
    'Updated at': '更新时间',
    'Updated by': '更新人',
    'Lead Time': '耗时',
    'Drafts': '草稿',
    "Let's connect your first model": '连接第一个模型',
    'Connect Model': '连接模型',
    'Connect a machine learning model to generate live predictions for your project. Compare predictions, accelerate labeling with automatic prelabeling, and direct your team to the most impactful tasks through active learning.': '连接机器学习模型，为项目生成实时预测。可对比预测结果、用自动预标注加速标注，并通过主动学习把团队引导到最有价值的任务。',
    'Add Source Storage': '添加源存储',
    'Add Target Storage': '添加目标存储',
    'Add your first cloud storage': '添加第一个云存储',
    'Use cloud or database storage as the source for your labeling tasks or the target of your completed annotations.': '使用云存储或数据库作为标注任务的数据源，或作为已完成标注的导出目标。',
    'Configure data': '配置数据',
    'Configure settings': '配置选项',
    'Labels': '标签',
    'Add': '添加',
    'Add label names': '添加标签名称',
    'Use new line as a separator to add multiple labels': '使用换行分隔，可一次添加多个标签',
    'Select label and click the image to start': '选择标签后点击图像开始标注',
    'Width of region borders': '区域边框宽度',
    'Allow image zoom (ctrl+wheel)': '允许缩放图像（Ctrl + 滚轮）',
    'Show controls to zoom in and out': '显示缩放控件',
    'Show controls to rotate image': '显示旋转控件',
    'To select which field(s) to label you need to upload the data. Alternatively, you can provide it using Code mode.': '要选择标注字段，请先上传数据；也可以切换到代码模式手动配置。',
    '<set manually>': '手动设置',
    'Use image from': '图像来源',
    'Use image from <set manually>': '使用图像来源：手动设置',
    'Zoom to fit': '适应窗口',
    'Zoom to actual size': '实际大小',
    'Zoom In': '放大',
    'Zoom Out': '缩小',
    'Pan Image': '平移图像',
    'Move': '移动',
    'Arrow Marker': '箭头标记',
    'Brush labels to COCO': '笔刷标注转 COCO',
    'Brush labels to NumPy': '笔刷标注转 NumPy',
    'Brush labels to PNG': '笔刷标注转 PNG',
    'ASR Manifest': 'ASR Manifest',
    'YOLOv8 OBB': 'YOLOv8 OBB',
    'YOLOv8 OBB with Images': 'YOLOv8 OBB（含图片）',
    'DocLang (.dclx)': 'DocLang 格式（.dclx）',
    'speech recognition': '语音识别',
    'COCO format with images downloaded.': 'COCO 格式，并下载图片。',
    'YOLO format with images downloaded.': 'YOLO 格式，并下载图片。',
    'YOLOv8 OBB format with images downloaded.': 'YOLOv8 OBB 格式，并下载图片。',
    'Export your brush labels as PNG images. Each label outputs as one image.': '将笔刷标注导出为 PNG 图片，每个标注输出为一张图片。',
    'Popular XML format used for object detection and polygon image segmentation tasks.': '常用于目标检测与多边形图像分割的 XML 格式。',
    'Popular format used for the CoNLL-2003 named entity recognition challenge.': 'CoNLL-2003 命名实体识别任务常用的格式。',
    'Popular TXT format is created for each image file. Each txt file contains annotations for the corresponding image file, that is object class, object coordinates, height & width.': '每个图像文件生成一个 TXT 文件，包含对应图像的目标类别、坐标以及高宽信息。',
    'Popular TXT format is created for each image file. Each txt file contains annotations for the corresponding image file. The YOLO OBB format designates bounding boxes by their four corner points with coordinates normalized between 0 and 1, so it is possible to export rotated objects.': '每个图像文件生成一个 TXT 文件。YOLO OBB 使用四个角点表示边界框，坐标归一化到 0–1，可导出旋转目标。',
    'Export audio transcription labels for automatic speech recognition as the JSON manifest format expected by NVIDIA NeMo models.': '将语音转写标注导出为 NVIDIA NeMo 模型所需的 JSON Manifest 格式，用于自动语音识别。',
    'Package annotations from the Doclang Interface as DocLang OPC archives (document.xml + page image) for downstream Docling model training.': '将 DocLang 界面的标注打包为 DocLang OPC 归档（document.xml + 页面图像），供后续 Docling 模型训练使用。',
    'Results are stored in tab-separated tabular file with column names specified by "from_name" "to_name" values': '结果以制表符分隔的表格文件保存，列名由 from_name 和 to_name 字段决定',
    'Repository': '代码仓库',
    'Slack': 'Slack',
    'Ask on Slack': '联系支持',
    'Cannot convert undefined or null to object': '页面数据暂时无法加载',
    'No Project matches the given query.': '项目不存在或已被删除。',
    'TypeError: Cannot convert undefined or null to object': '页面数据暂时无法加载',
  };

  const attributes = {
    'Create new project': '创建新项目',
    'Project options': '项目选项',
    'Cancel project creation': '取消创建项目',
    'Cancel import': '取消导入',
    'Finish import': '完成导入',
    'Upload file': '上传文件',
    'Save general settings': '保存常规设置',
    'Save annotation settings': '保存标注设置',
    'Save configuration': '保存配置',
    'Export data': '导出数据',
    'Close modal': '关闭窗口',
    'Tab options': '标签页选项',
    'Open New Tab': '打开新标签页',
    'Tasks Actions': '任务操作',
    'Filters': '筛选',
    'Sort descending': '降序排列',
    'Refresh data': '刷新数据',
    'Browse templates': '浏览模板',
    'Create custom template': '创建自定义模板',
    'Default': '默认',
    'Dataset URL': '数据集 URL',
    'import button': '导入',
    'export button': '导出',
    'Comfortable density': '舒适密度',
    'Compact density': '紧凑密度',
    'Switch to grid view': '切换到网格视图',
    'Switch to list view': '切换到列表视图',
    'Filtered tasks': '筛选后的任务数',
    'Total tasks in the project': '项目总任务数',
    'Notifications (F8)': '通知（F8）',
    'Add machine learning model': '添加机器学习模型',
    'Add Source Storage': '添加源存储',
    'Add Target Storage': '添加目标存储',
    'Add labels': '添加标签',
    'Allow image zoom (ctrl+wheel)': '允许缩放图像（Ctrl + 滚轮）',
    'Show controls to zoom in and out': '显示缩放控件',
    'Show controls to rotate image': '显示旋转控件',
    'Hide all regions': '隐藏全部区域',
    'move-tool': '移动工具',
    'pan': '平移',
    'zoom-in': '放大',
    'zoom-out': '缩小',
    'Drag to resize': '拖动调整大小',
    'Zoom presets (click to see options)': '缩放预设（点击查看选项）',
  };

  const fragments = [
    [/Use image from/g, '图像来源'],
    [/Ask on Slack/g, '联系支持'],
    [/Cannot convert undefined or null to object/g, '页面数据暂时无法加载'],
    [/Cannot read properties of null \(reading '[^']+'\)/g, '页面数据暂时无法加载'],
    [/TypeError:\s*/g, ''],
    [/Runtime error/g, '运行错误'],
    [/No Project matches the given query\./g, '项目不存在或已被删除。'],
    [/Label Studio/g, '标注平台'],
    [/\s*\(Enterprise only\)/gi, ''],
  ];

  function translate(value) {
    const leading = value.match(/^\s*/)[0];
    const trailing = value.match(/\s*$/)[0];
    const core = value.trim();
    if (text[core]) return leading + text[core] + trailing;
    let match = core.match(/^(\d+) of (\d+) Tasks \(([^)]+)\)$/);
    if (match) return leading + match[1] + ' / ' + match[2] + ' 个任务（' + match[3] + '）' + trailing;
    match = core.match(/^Tasks: (\d+) \/ (\d+)$/);
    if (match) return leading + '任务：' + match[1] + ' / ' + match[2] + trailing;
    match = core.match(/^Submitted annotations: (\d+)$/);
    if (match) return leading + '已提交标注：' + match[1] + trailing;
    match = core.match(/^Predictions: (\d+)$/);
    if (match) return leading + '预测：' + match[1] + trailing;
    match = core.match(/^Labels \((\d+)\)$/);
    if (match) return leading + '标签（' + match[1] + '）' + trailing;
    match = core.match(/^(\d{1,2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (\d{4}), (\d{2}:\d{2})$/);
    if (match) {
      const months = {
        Jan: '1月', Feb: '2月', Mar: '3月', Apr: '4月', May: '5月', Jun: '6月',
        Jul: '7月', Aug: '8月', Sep: '9月', Oct: '10月', Nov: '11月', Dec: '12月',
      };
      return leading + match[3] + '年' + months[match[2]] + Number(match[1]) + '日 ' + match[4] + trailing;
    }
    return fragments.reduce((result, [pattern, replacement]) => result.replace(pattern, replacement), value);
  }

  function hideEnterprise(root) {
    if (!root.querySelectorAll) return;
    root.querySelectorAll('*').forEach((element) => {
      if (element.children.length) return;
      const value = (element.textContent || '').trim();
      if (!/^(enterprise|企业版|enterprise only|仅企业版)$/i.test(value)) return;
      const target = element.closest('button,a,[role="button"],[role="option"],[role="tab"],li,p')
        || element.parentElement;
      if (!target || target === document.body) return;
      if (target.getAttribute('aria-hidden') === 'true' && target.style.display === 'none') return;
      target.style.setProperty('display', 'none', 'important');
      target.setAttribute('aria-hidden', 'true');
    });
  }

  function hide(element) {
    if (!element || (element.dataset.modeloneHidden === 'true'
      && element.style.getPropertyValue('display') === 'none')) return;
    element.dataset.modeloneHidden = 'true';
    element.style.setProperty('display', 'none', 'important');
    element.setAttribute('aria-hidden', 'true');
  }

  function isVendorLink(anchor) {
    let url;
    try { url = new URL(anchor.getAttribute('href'), document.baseURI); }
    catch (_) { return false; }
    const host = url.hostname.toLowerCase();
    return /(^|\.)(labelstud\.io|humansignal\.com)$/.test(host)
      || (host === 'aws.amazon.com' && url.pathname.startsWith('/marketplace/'))
      || (host === 'github.com' && /^\/HumanSignal\/label-studio(?:-converter)?(?:\/|$)/i.test(url.pathname));
  }

  function hideVendorLinks(root) {
    if (!root.querySelectorAll) return;
    const links = root.matches && root.matches('a[href]')
      ? [root, ...root.querySelectorAll('a[href]')]
      : root.querySelectorAll('a[href]');
    links.forEach((anchor) => {
      if (!isVendorLink(anchor)) return;
      const parent = anchor.parentElement;
      let target = anchor;
      if (anchor.closest('.tips:has(> ul)')) target = anchor.closest('.tips:has(> ul)');
      else if (anchor.closest('.lsf-formats__feedback')) target = anchor.closest('.lsf-formats__feedback');
      else if (anchor.closest('.lsf-export-page__recent')) target = anchor.closest('.lsf-export-page__recent');
      else if (anchor.closest('.lsf-configure__tags-link')) target = anchor.closest('.lsf-configure__tags-link');
      else if (parent && parent.tagName === 'P'
        && parent.textContent.trim() === anchor.textContent.trim()) target = parent;
      else if (parent && parent.tagName === 'LI'
        && /Check the documentation to/i.test(parent.textContent)) target = parent;
      else if (parent && parent.tagName === 'SPAN'
        && /See the documentation to/i.test(parent.textContent)) target = parent;
      if (parent && parent.matches('[data-slot="alert-description"]')) {
        Array.from(parent.childNodes).filter((node) => node.nodeType === Node.TEXT_NODE).forEach((node) => {
          const next = node.textContent.replace(/\s*See the documentation for details:\s*/i, '');
          if (next !== node.textContent) node.textContent = next;
        });
      }
      hide(target);
    });

    // Error and help actions from the standalone product are not part of the
    // embedded modelOne workflow. Remove them even when rendered as buttons.
    root.querySelectorAll('button,[role="button"]').forEach((control) => {
      const value = (control.textContent || '').trim();
      if (/^(ask on slack|联系支持|查看文档|documentation|repository)$/i.test(value)) hide(control);
    });
  }

  function hideStandaloneNavigation(root) {
    if (!root.querySelectorAll) return;
    root.querySelectorAll('a[href]').forEach((anchor) => {
      const href = anchor.getAttribute('href') || '';
      if (/\/labelstudio\/(organization|version)(?:[/?#]|$)/i.test(href)) hide(anchor);
    });
  }

  function hideWorkspaceFields(root) {
    if (!root.querySelectorAll) return;
    if (root.matches && root.matches('.lsf-workspace-placeholder')) hide(root);
    root.querySelectorAll('.lsf-workspace-placeholder').forEach(hide);
    const labels = root.matches && root.matches('label')
      ? [root, ...root.querySelectorAll('label')]
      : root.querySelectorAll('label');
    labels.forEach((label) => {
      const name = Array.from(label.childNodes)
        .filter((node) => node.nodeType === Node.TEXT_NODE)
        .map((node) => node.textContent.trim()).join('');
      if (name !== 'Workspace' && name !== '工作区') return;
      const field = label.parentElement;
      if (field && field.querySelector('button[data-testid="select-trigger"][disabled]')) hide(field);
    });
  }

  function isProjectName(element) {
    return element.closest('[data-testid="project-title"], .text-neutral-content.truncate');
  }

  function translateCompoundLabels(root) {
    if (!root.querySelectorAll) return;
    root.querySelectorAll('p,label,button,[role="button"]').forEach((element) => {
      const textNodes = Array.from(element.childNodes).filter((node) => node.nodeType === Node.TEXT_NODE);
      if (!textNodes.length) return;
      const value = textNodes.map((node) => node.nodeValue).join('').trim();
      if (value !== 'Use image from') return;
      const first = textNodes[0];
      const leading = first.nodeValue.match(/^\s*/)[0];
      first.nodeValue = leading + '图像来源';
      textNodes.slice(1).forEach((node) => { node.nodeValue = ''; });
    });
  }

  function translateLeafText(element) {
    const nodes = Array.from(element.childNodes).filter((node) => node.nodeType === Node.TEXT_NODE);
    if (!nodes.length) return;

    const current = nodes.map((node) => node.nodeValue).join('');
    const next = translate(current);
    if (next === current) return;

    // Keep React's text-node references attached while translating split labels.
    nodes[0].nodeValue = next;
    nodes.slice(1).forEach((node) => { node.nodeValue = ''; });
  }

  function visit(root) {
    hideEnterprise(root);
    hideWorkspaceFields(root);
    hideVendorLinks(root);
    hideStandaloneNavigation(root);
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes = [];
    let node;
    while ((node = walker.nextNode())) {
      const parent = node.parentElement;
      if (parent && !/^(SCRIPT|STYLE|TEXTAREA|INPUT|OPTION)$/i.test(parent.tagName)
        && !isProjectName(parent)) nodes.push(node);
    }
    nodes.forEach((item) => {
      const next = translate(item.nodeValue);
      if (next !== item.nodeValue) item.nodeValue = next;
    });
    translateCompoundLabels(root);
    // React often splits a visible label into several text nodes (for
    // example, the task count). Translate the complete leaf label as well.
    root.querySelectorAll && root.querySelectorAll('*').forEach((element) => {
      if (element.children.length || /^(SCRIPT|STYLE|TEXTAREA|INPUT|OPTION)$/i.test(element.tagName)
        || isProjectName(element)) return;
      translateLeafText(element);
    });
    root.querySelectorAll && root.querySelectorAll('input,textarea,[aria-label],[title],img[alt]').forEach((element) => {
      ['placeholder', 'aria-label', 'title', 'alt'].forEach((name) => {
        if (element.hasAttribute(name)) {
          const value = element.getAttribute(name);
          const next = attributes[value] || text[value] || translate(value);
          if (next !== value) element.setAttribute(name, next);
        }
      });
    });
  }

  function start() {
    if (!document.body) return;
    visit(document.body);
    new MutationObserver((records) => {
      records.forEach((record) => {
        record.addedNodes.forEach((node) => {
          if (node.nodeType === Node.ELEMENT_NODE) visit(node);
          else if (node.nodeType === Node.TEXT_NODE && node.parentElement) {
            const next = translate(node.nodeValue);
            if (next !== node.nodeValue) node.nodeValue = next;
          }
        });
        if (record.type === 'characterData' && record.target.parentElement) {
          const next = translate(record.target.nodeValue);
          if (next !== record.target.nodeValue) record.target.nodeValue = next;
        }
        if (record.type === 'attributes' && record.target) visit(record.target.parentElement || record.target);
      });
    }).observe(document.body, { childList: true, characterData: true, attributes: true, subtree: true });
    // Some React views update existing text nodes without emitting a childList
    // mutation. A light periodic pass keeps route and modal content translated.
    window.setInterval(() => visit(document.body), 1200);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();
